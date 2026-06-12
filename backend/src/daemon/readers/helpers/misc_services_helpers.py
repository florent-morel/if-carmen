"""
Helper functions for misc_services model
"""

import logging
from datetime import datetime, timedelta

from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.helpers import str_to_float
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.common.constants import (
    SOURCE_PROVIDER,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_DATE,
    DATE_FORMAT,
    UNKNOWN,
)

logger = logging.getLogger(__name__)


def get_carbon_and_energy_values(
    vms: list[VirtualMachine], storage_resources: list[StorageResource]
):
    """
    Calculates and returns carbon and energy values for VMs and storage resources.
    Args:
        vms: List of vms
        storage_resources: List of storage resources

    Returns:
        Tuple containing storage total carbon, storage total energy, VM total carbon, VM total energy
    """
    vm_total_carbon = 0
    storage_total_carbon = 0
    vm_total_energy = 0
    storage_total_energy = 0
    for vm in vms:
        vm_total_carbon += vm.total_carbon_operational + vm.total_carbon_embodied
        vm_total_energy += vm.total_energy_consumed
    for storage in storage_resources:
        storage_total_carbon += (
            storage.total_carbon_operational + storage.total_carbon_embodied
        )
        storage_total_energy += storage.total_energy_consumed
    return storage_total_carbon, storage_total_energy, vm_total_carbon, vm_total_energy


def create_misc_services_resource(row):
    """
    Creates a misc_services resource from the given row
    """
    logger.debug(f"Inside create misc_services_resource row: {row}")
    region = row.get(SOURCE_REGION, UNKNOWN)
    logger.debug(f"{SOURCE_REGION}: {region}")
    id = row.get(SOURCE_RESOURCE_ID)
    misc_services_resource = None
    if id:
        misc_services_resource = MiscServicesResource(
            name=row.get(SOURCE_PRODUCT_NAME, ""),
            id=id,
            provider=row.get(SOURCE_PROVIDER, ""),
            region=region,
            carbon_intensity=PaasCiMapper.calculate_ci(region.lower()),
            cost=str_to_float(row.get(SOURCE_COST, "0")),
        )
        timestamp = row.get(
            SOURCE_DATE, (datetime.now() - timedelta(days=2)).strftime(DATE_FORMAT)
        )
        misc_services_resource.time_points = [timestamp]
    return misc_services_resource
