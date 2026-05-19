"""
Helper functions for misc_services model
"""

import csv
import logging
from datetime import datetime, timedelta

from backend.src.common.known_exception import KnownException
from backend.src.core.settings import ReportConfig
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


def create_misc_services_report(
    misc_services_resources: list[MiscServicesResource], date: str, out_file: str
):
    """
    Creates a misc_services report for the given misc services resource list.
    """
    logger.info("Creating misc_services model report...")
    with open(out_file, mode="w", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)
        writer.writerows(ReportConfig.misc_services_REPORT_HEADERS)
        for misc_services_resource in misc_services_resources:
            row = [
                date,
                misc_services_resource.id,
                misc_services_resource.resource_type,
                misc_services_resource.region,
                misc_services_resource.subscription,
                misc_services_resource.carbon_intensity,
                misc_services_resource.misc_services_cost,
                misc_services_resource.total_energy_consumed,
                misc_services_resource.total_carbon_operational,
                misc_services_resource.total_carbon_embodied,
            ]
            writer.writerow(row)
    logger.info("misc_services model report saved to: %s", out_file)


def create_misc_services_resource(row):
    """
    Creates a misc_services resource from the given row
    """
    region = row.get("ResourceLocation", "unknown")
    misc_services_resource = MiscServicesResource(
        id=row.get("ResourceId"),
        name=row.get("ProductName", ""),
        provider=row.get("Provider", ""),
        region=region,
        subscription=row.get("SubscriptionId", "unknown"),
        carbon_intensity=PaasCiMapper.calculate_ci(region.lower()),
        services_misc_services=str_to_float(row.get("BillingCost", "0")),
    )
    timestamp = row.get(
        "Date", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    )
    misc_services_resource.time_points = [timestamp]
    return misc_services_resource
