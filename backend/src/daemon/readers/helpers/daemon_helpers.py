"""
This module contains helper functions for the daemon, including VM creation and logging of missing regions.
TODO: this is actually a VM_helpers module
"""

import logging
from backend.src.core.yaml_config_loader import config
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.paas_ci_mapper import PaasCiMapper

logger = logging.getLogger(__name__)

def get_row_data(row_data: str) -> str:
    """
    Helper function to get row data, returns empty string if the data is missing or represented as '-'.
    """
    return row_data if row_data != "-" and row_data else ""


def create_vm(row: dict[str, str], vm_id: str) -> VirtualMachine:
    """
    Creates a new VirtualMachine instance based on the provided row data.
    """
    region = get_row_data(row["Region"])
    provider = get_row_data(row["Provider"])
    provider_config = config.provider_configs.get(provider)
    pue = provider_config.get_pue() if provider_config else config.defaults.pue
    return VirtualMachine(
        id=vm_id,
        region=region,
        vm_size=get_row_data(row["Size"]),
        service=get_row_data(row["Service"]),
        component=get_row_data(row["Component"]),
        subscription=get_row_data(row["Subscription"]),
        name=get_row_data(row["Name"]),
        instance=get_row_data(row["Instance"]),
        environment=get_row_data(row["Environment"]),
        partition=get_row_data(row["Partition"]),
        carbon_intensity=PaasCiMapper.calculate_ci(region),
        provider=provider,
        pue=pue,
    )
