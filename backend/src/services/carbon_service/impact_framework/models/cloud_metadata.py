"""
Cloud Metadata model for VM instance lookup and per-VM TDP attribution.
"""

import csv
import logging
from functools import lru_cache
from pathlib import Path

from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import CarmenException
from backend.src.core.settings import settings
from backend.src.core.yaml_config_loader import config
from backend.src.daemon.readers.helpers.virtual_machine_helpers import parse_vcpu_count_from_azure_vm_size
from backend.src.schemas.virtual_machine import VirtualMachine


from backend.src.common.constants import (
    MODELS_INSTANCE_CLASS,
    MODELS_CPU_CORES_AVAIL,
    MODELS_CPU_CORES_UTILIZED,
    MODELS_CPU_TDP,
    MODELS_MEMORY_AVAIL,
    IF_INPUT_CPU_TDP,
    IF_INPUT_MEMORY_REQUESTED,
    IF_INPUT_VCPU_ALLOCATED,
    IF_INPUT_VCPU_TOTAL,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def _load_instances(provider: str) -> dict:
    """
    Load and cache the provider's instances CSV keyed by instance-class.

    Skips '#' comment lines and empty instance-class rows. When
    cpu-cores-available is absent or zero, defaults it to cpu-cores-utilized
    so the full TDP is attributed to the VM. Returns an empty dict if no
    provider is specified or the CSV is missing or unreadable.
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
    try:
        with open(csv_path, encoding="utf-8") as f:
            data_lines = (line for line in f if not line.startswith("#"))
            reader = csv.DictReader(data_lines)
            for row in reader:
                key = row.get(MODELS_INSTANCE_CLASS, "").strip()
                if not key:
                    continue
                try:
                    raw_avail = row.get(MODELS_CPU_CORES_AVAIL, "").strip()
                    raw_util = row.get(MODELS_CPU_CORES_UTILIZED, "").strip()
                    raw_tdp = row.get(MODELS_CPU_TDP, "").strip()
                    raw_mem = row.get(MODELS_MEMORY_AVAIL, "").strip()
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
                    MODELS_CPU_CORES_AVAIL: cores_available,
                    MODELS_CPU_CORES_UTILIZED: cores_utilized,
                    MODELS_CPU_TDP: cpu_tdp,
                    MODELS_MEMORY_AVAIL: memory,
                }
    except OSError as e:
        logger.warning(
            "Could not read instances CSV '%s' for provider '%s': %s; all VMs will use the TDP fallback",
            csv_path,
            provider,
            e,
        )
        return {}
    return result


class CloudMetadata:
    """
    Resolves VM hardware inputs (cpu/thermal-design-power, vcpus-total,
    vcpus-allocated, memory/requested) from the provider instances CSV.

    The CSV stores full host package TDP, which is scaled to the VM's share:

        cpu/thermal-design-power = cpu-tdp x (vcpus-utilized / vcpus-available)

    When an instance type is absent from the CSV, TDP is approximated as
    cpu_max x vcpu_count using the provider's cpu_max value and the resolved
    vCPU count.
    """

    @staticmethod
    def fill_inputs(resource: VirtualMachine, time_index: int) -> dict:
        provider = resource.provider or ""
        instances = _load_instances(provider)
        row = instances.get(resource.vm_size or "")

        if row is not None:
            cores_available = row[MODELS_CPU_CORES_AVAIL]
            cores_utilized = row[MODELS_CPU_CORES_UTILIZED]
            cpu_tdp = row[MODELS_CPU_TDP]
            memory = row[MODELS_MEMORY_AVAIL]
            # Scale full host package TDP down to the VM's core share.
            vm_tdp = cpu_tdp * cores_utilized / cores_available
            return {
                IF_INPUT_CPU_TDP: vm_tdp,
                IF_INPUT_VCPU_TOTAL: cores_available,
                IF_INPUT_VCPU_ALLOCATED: cores_utilized,
                IF_INPUT_MEMORY_REQUESTED: memory,
            }

        # Estimate TDP from provider cpu_max when the instance type is absent from the CSV.
        provider_config = config.provider_configs.get(provider)
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
            IF_INPUT_CPU_TDP: vm_tdp,
            IF_INPUT_VCPU_TOTAL: vcpu_count,
            IF_INPUT_VCPU_ALLOCATED: vcpu_count,
            # Memory is unavailable without a CSV entry; pass 0 as required by the IF pipeline.
            IF_INPUT_MEMORY_REQUESTED: 0,
        }

    @staticmethod
    def _resolve_vcpu_count(vm: VirtualMachine, cpu_max: float) -> int:
        """
        Resolve vCPU count when the instance type is absent from the CSV:
        1. Input CSV VmNbCpus column (vm.vcpu_count).
        2. Azure VM size name parsing (e.g. Standard_D32as_v5 -> 32) for Azure VMs.
        3. Raise CarmenException(UNKNOWN_VM_INSTANCE_TYPE).
        """
        if vm.vcpu_count is not None:
            logger.warning(
                "VM '%s' (type '%s') not in instances CSV; using input CSV VCpuCount=%d "
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
                f"provider instances CSV, has no VCpuCount in the input CSV, and could "
                f"not be resolved from the instance type name. Cannot compute CPU energy."
            ),
        )
