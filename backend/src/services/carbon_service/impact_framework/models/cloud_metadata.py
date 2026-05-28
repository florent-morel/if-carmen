"""
Cloud Metadata model — Python-level VM instance lookup with correct per-VM TDP attribution.

For each VM, ``fill_inputs`` looks up the instance type in the provider instances
CSV and returns four values consumed by the IF pipeline:

  - ``cpu/thermal-design-power`` — host package TDP scaled to the VM's share:

        cpu/thermal-design-power = cpu-tdp × (vcpus-utilized / vcpus-available)

    The CSV stores the FULL package TDP for the entire physical host.  Without
    this scaling, the IF pipeline over-counts CPU power by a factor equal to
    the total number of host cores.

  - ``vcpus-total`` / ``vcpus-allocated`` — used by downstream embodied-carbon
    steps to compute the VM's share of manufacturing emissions.

  - ``memory/requested`` — VM memory in GB.

When the instance type is absent from the CSV, TDP and core counts are
unavailable.  Because TDP is exclusively sourced from the CSV, a CSV hit
already provides everything needed — billing vCPU count is redundant in that
case.  When the CSV lookup misses, the chain is:

       a. Billing NbVCpus (``vm.vcpu_count``, populated by ``create_vm`` from
          the billing export's NbVCpus column). 
          VM value reported by the cloud provider.

       b. Name-parsing heuristic : try to extract the digit from the instance type
          name (e.g. ``Standard_D32as_v5`` → 32). 
          Less reliable than billing data: constrained-core variants 
          (e.g. ``Standard_E32-8s_v3``) can encode a different number 
          than the actual vCPU count.

       c. CarmenException(UNKNOWN_VM_INSTANCE_TYPE) — the VM cannot be
          attributed and is excluded from the carbon report.

     In all fallback cases TDP is approximated as ``cpu_max × vcpu_count``
     where ``cpu_max`` is the per-core maximum power drawn from provider config.

# TODO: update docs/methodology.md to document the fallback chain and
#       the TDP scaling formula.
"""

import csv
import logging
from functools import lru_cache
from pathlib import Path

from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import CarmenException
from backend.src.core.settings import settings
from backend.src.daemon.readers.helpers.daemon_helpers import parse_vcpu_count_from_azure_vm_size
from backend.src.schemas.virtual_machine import VirtualMachine

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def _load_instances(provider: str) -> dict:
    """
    Load and cache the instances CSV for a provider as a dict keyed by instance-class.

    The CSV may start with comment lines beginning with '#'; these are skipped.
    Rows with an empty instance-class are ignored.
    If 'cpu-cores-available' is absent or zero, it is defaulted to 'cpu-cores-utilized'
    so the attribution ratio is 1 (full TDP assigned to the VM).

    Returns an empty dict when the CSV does not exist or cannot be read.
    """
    if not provider:
        return {}
    csv_path = (
        Path(settings.CARMEN_PROVIDER_CONFIG_FILEPATH)
        / provider
        / f"{provider}_instances.csv"
    ).resolve()
    if not csv_path.exists():
        logger.warning(
            "No instances CSV for provider '%s'; all VMs will use the TDP fallback",
            provider,
        )
        return {}
    result: dict = {}
    with open(csv_path, encoding="utf-8") as f:
        data_lines = (line for line in f if not line.startswith("#"))
        reader = csv.DictReader(data_lines)
        for row in reader:
            key = row.get("instance-class", "").strip()
            if not key:
                continue
            try:
                raw_avail = row.get("cpu-cores-available", "").strip()
                raw_util = row.get("cpu-cores-utilized", "").strip()
                raw_tdp = row.get("cpu-tdp", "").strip()
                raw_mem = row.get("memory-available", "").strip()
                cores_utilized = float(raw_util) if raw_util else None
                cores_available = float(raw_avail) if raw_avail else None
                cpu_tdp = float(raw_tdp) if raw_tdp else None
                memory = float(raw_mem) if raw_mem else 0.0
            except ValueError:
                logger.debug("Skipping malformed CSV row for instance '%s'", key)
                continue
            # If cpu-cores-available is absent or zero, treat ratio as 1
            if not cores_available:
                cores_available = cores_utilized
            result[key] = {
                "cpu-cores-available": cores_available,
                "cpu-cores-utilized": cores_utilized,
                "cpu-tdp": cpu_tdp,
                "memory-available": memory,
            }
    return result


class CloudMetadata:
    """
    Cloud metadata provider.

    ``fill_inputs`` returns cpu/thermal-design-power, vcpus-total, vcpus-allocated, 
    memory/requested, with TDP correctly scaled to the VM's allocated share of the host processor:

        cpu/thermal-design-power = cpu-tdp × (vcpus-utilized / vcpus-available)

    For VM types not present in the instances CSV the fallback chain is applied
    (billing NbVCpus → name parsing → CarmenException).
    """

    @staticmethod
    def fill_inputs(resource: VirtualMachine, time_index: int) -> dict:  # noqa: ARG002
        from backend.src.core.yaml_config_loader import config as app_config

        provider = resource.provider or ""
        instances = _load_instances(provider)
        row = instances.get(resource.vm_size or "")

        if row is not None:
            cores_available = row["cpu-cores-available"]
            cores_utilized = row["cpu-cores-utilized"]
            cpu_tdp = row["cpu-tdp"]
            memory = row["memory-available"]
            # Scale the full host package TDP down to the VM's allocation fraction.
            vm_tdp = cpu_tdp * cores_utilized / cores_available
            return {
                "cpu/thermal-design-power": vm_tdp,
                "vcpus-total": cores_available,
                "vcpus-allocated": cores_utilized,
                "memory/requested": memory,
            }

        # Instance type not in CSV — apply fallback chain.
        provider_config = app_config.provider_configs.get(provider)
        cpu_max = provider_config.get_cpu_max() if provider_config else None
        if cpu_max is None:
            raise CarmenException(
                ErrorCode.UNKNOWN_VM_INSTANCE_TYPE,
                details=(
                    f"VM '{resource.name}' (type '{resource.vm_size}'): instance type is not "
                    f"in the provider instances CSV and provider config has no 'cpu_max' value. "
                    f"Cannot compute CPU energy."
                ),
            )
        vcpu_count = CloudMetadata._resolve_vcpu_count(resource, cpu_max)
        vm_tdp = cpu_max * vcpu_count
        return {
            "cpu/thermal-design-power": vm_tdp,
            "vcpus-total": vcpu_count,
            "vcpus-allocated": vcpu_count,
            # INV3c: memory fallback not yet implemented; 0 avoids an IF pipeline crash
            "memory/requested": 0,
        }

    @staticmethod
    def _resolve_vcpu_count(vm: VirtualMachine, cpu_max: float) -> int:
        """
        Fallback chain for VMs whose instance type is absent from the CSV:
          1. Billing NbVCpus column (``vm.vcpu_count``, set by ``create_vm``)
          2. Azure name-parsing heuristic (e.g. ``Standard_D32as_v5`` → 32),
             only attempted when ``vm.provider == "azure"``
          3. Raise CarmenException
        """
        if vm.vcpu_count is not None:
            logger.warning(
                "VM '%s' (type '%s') not in instances CSV; using billing VCpuCount=%d "
                "as TDP fallback (%.2f W)",
                vm.name,
                vm.vm_size,
                vm.vcpu_count,
                cpu_max * vm.vcpu_count,
            )
            return vm.vcpu_count
        parsed = (
            parse_vcpu_count_from_azure_vm_size(vm.vm_size or "")
            if vm.provider == "azure"
            else None
        )
        if parsed is not None:
            logger.warning(
                "VM '%s' (type '%s') not in instances CSV; vCPU count %d inferred "
                "from instance type name (heuristic, %.2f W)",
                vm.name,
                vm.vm_size,
                parsed,
                cpu_max * parsed,
            )
            return parsed
        raise CarmenException(
            ErrorCode.UNKNOWN_VM_INSTANCE_TYPE,
            details=(
                f"VM '{vm.name}' has instance type '{vm.vm_size}' which is not in the "
                f"provider instances CSV, has no VCpuCount in the billing data, and could "
                f"not be resolved from the instance type name. Cannot compute CPU energy."
            ),
        )
