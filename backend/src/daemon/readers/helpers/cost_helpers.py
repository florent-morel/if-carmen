"""
Helper functions for cost model
"""

import csv
import logging
from datetime import datetime, timedelta

from backend.src.common.known_exception import KnownException
from backend.src.core.settings import settings
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.helpers import str_to_float
from backend.src.utils.paas_ci_mapper import PaasCiMapper

from backend.src.common.errors import ErrorCode

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






def create_cost_report(cost_resources: list[MiscServicesResource], date: str, out_file: str):
    """
    Creates a cost report for the given cost resource list.
    """
    logger.info("Creating cost model report...")
    with open(out_file, mode="w", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)
        writer.writerows(settings.FINOPS.COST_REPORT_HEADERS)
        for cost_resource in cost_resources:
            row = [
                date,
                cost_resource.id,
                cost_resource.resource_type,
                cost_resource.region,
                cost_resource.subscription,
                cost_resource.carbon_intensity,
                cost_resource.services_cost,
                cost_resource.total_energy_consumed,
                cost_resource.total_carbon_operational,
                cost_resource.total_carbon_embodied,
            ]
            writer.writerow(row)
    logger.info("Cost model report saved to: %s", out_file)
