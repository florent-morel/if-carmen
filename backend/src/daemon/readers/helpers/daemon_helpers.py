"""
This module contains helper functions for the daemon, including VM creation and logging of missing regions.
TODO: this is actually a VM_helpers module
"""

import re

from backend.src.core.yaml_config_loader import config
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.utils.helpers import get_row_data
from backend.src.common.constants import (
    SOURCE_PROVIDER,
    SOURCE_NAME,
    SOURCE_SERVICE,
    SOURCE_INSTANCE,
    SOURCE_ENVIRONMENT,
    SOURCE_PARTITION,
    SOURCE_COMPONENT,
    SOURCE_SUBSCRIPTION,
    SOURCE_REGION,
    SOURCE_AVG_CPU_PERCENTAGE,
    SOURCE_METER_CATEGORY,
    SOURCE_BILLING_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_METER_NAME,
    SOURCE_QUANTITY,
    SOURCE_UNIT_OF_MEASURE,
    SOURCE_DATE,
    SOURCE_TIME,
    SOURCE_SIZE,
    SOURCE_NB_VCPUS,
    DATE_FORMAT,
    SOURCE_DISK_SIZE_GB,
    UNKNOWN,
)


# TODO: Magic Azure
# Matches Azure VM size names of the form Standard_<family><digits>[suffix]
# (e.g. Standard_D32as_v5, Standard_E4s_v3, Standard_B2ms) and extracts the
# digit(s) immediately following the family letters as the vCPU count.
# This heuristic does not apply to other cloud providers: AWS names
# (e.g. m5.xlarge) do not encode a vCPU count, and GCP names follow a
# different scheme requiring a separate pattern.
_VM_SIZE_VCPU_RE = re.compile(r"(?i)standard_[a-z]+(\d+)")


def parse_vcpu_count_from_azure_vm_size(vm_size: str) -> int | None:
    """
    Attempt to extract the vCPU count from an Azure VM size name using the
    Azure naming convention (e.g. Standard_D32as_v5 → 32, Standard_E4s_v3 → 4).

    Returns None if the pattern does not match or vm_size is empty.
    Constrained-core variants (e.g. Standard_E32-8s_v3) are not handled and
    will return None. This is a last-resort fallback — always log a WARNING.
    """
    if not vm_size:
        return None
    m = _VM_SIZE_VCPU_RE.match(vm_size)
    if m:
        return int(m.group(1))
    return None


def _parse_vcpu_count_from_row(row: dict[str, str]) -> int | None:
    """Parse NbVCpus from a billing CSV row; returns None if absent or non-numeric."""
    raw = get_row_data(row.get(SOURCE_NB_VCPUS, ""))
    if not raw:
        return None
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return None


def create_vm(row: dict[str, str], vm_id: str) -> VirtualMachine:
    """
    Creates a new VirtualMachine instance based on the provided row data.
    """
    region = get_row_data(row[SOURCE_REGION])
    provider = get_row_data(row[SOURCE_PROVIDER])
    provider_config = config.provider_configs.get(provider)
    return VirtualMachine(
        id=vm_id,
        region=region,
        vm_size=get_row_data(row[SOURCE_SIZE]),
        service=get_row_data(row[SOURCE_SERVICE]),
        # component=get_row_data(row[SOURCE_COMPONENT]),
        # subscription=get_row_data(row[SOURCE_SUBSCRIPTION]),
        name=get_row_data(row[SOURCE_NAME]),
        # instance=get_row_data(row[SOURCE_INSTANCE]),
        # environment=get_row_data(row[SOURCE_ENVIRONMENT]),
        # partition=get_row_data(row[SOURCE_PARTITION]),
        carbon_intensity=PaasCiMapper.calculate_ci(region),
        provider=provider,
        pue=provider_config.get_pue() if provider_config else config.defaults.pue,
        billing_cost=get_row_data(row[SOURCE_BILLING_COST]),
        vcpu_count=_parse_vcpu_count_from_row(row),
    )
