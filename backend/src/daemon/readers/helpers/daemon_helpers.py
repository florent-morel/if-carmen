"""
This module contains helper functions for the daemon, including VM creation and logging of missing regions.
"""

import logging
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.common.constants import (
    REGION_TO_COUNTRY_CARBON_INTENSITY,
    CARBON_INTENSITY_EUROPE,
    PUE_AZURE,
)

logger = logging.getLogger(__name__)


def calculate_vm_count_for_missing_regions(
    missing_region_vm_count: dict[str, int], region: str
):
    """
    Fills the missing_region_vm_count dictionary.
    Args:
        missing_region_vm_count Dict[str, int]: Dictionary with the information of missing regions and
        the corresponding VM count.
        region str: Current VM's region.
    def get_vms() -> list
    """
    if region not in REGION_TO_COUNTRY_CARBON_INTENSITY:
        if region not in missing_region_vm_count:
            missing_region_vm_count[region] = 1
        else:
            missing_region_vm_count[region] += 1


def log_missing_regions(missing_region_vm_count: dict[str, int]):
    """
    Logs missing regions with the information of total number of VMs these regions contain.
    Args:
        missing_region_vm_count (Dict[str, int]): Dictionary with the information of missing regions and
        the corresponding VM count
    """
    for region in missing_region_vm_count:
        logger.warning(
            "unknown region '%s' detected with %d VMs - using European average carbon intensity (%d gCO2/kWh).",
            region,
            missing_region_vm_count[region],
            CARBON_INTENSITY_EUROPE,
        )


def create_vm(row: dict[str, str], vm_id: str, vm_size: str) -> VirtualMachine:
    """
    Creates a new VirtualMachine instance based on the provided row data.
    """
    return VirtualMachine(
        id=vm_id,
        region=row["Region"],
        vm_size=vm_size,
        service=row["Service"] if row["Service"] != "-" else "",
        component=row["Component"] if row["Component"] != "-" else "",
        subscription=(row["Subscription"] if row["Subscription"] != "-" else ""),
        name=row["Name"],
        instance=row["Instance"] if row["Instance"] != "-" else "",
        environment=row["Environment"] if row["Environment"] != "-" else "",
        partition=row["Partition"] if row["Partition"] != "-" else "",
        carbon_intensity=PaasCiMapper.calculate_ci(
            row["Region"]
            if row["Region"] != "-" and row["Region"]
            else "germanywestcentral"
        ),
        pue=PUE_AZURE,  # improvement: add pue value dynamically
    )
