"""
Helper functions for cost model
"""

import csv
import logging
from datetime import datetime, timedelta

from backend.src.common.known_exception import KnownException
from backend.src.core.config import settings
from backend.src.schemas.costResource import CostResource
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.helpers import str_to_float
from backend.src.utils.paas_ci_mapper import PaasCiMapper

logger = logging.getLogger(__name__)


def get_carbon_and_energy_values(vms: list[VirtualMachine], storage_resources: list[StorageResource]):
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
        vm_total_carbon += (vm.total_carbon_operational + vm.total_carbon_embodied)
        vm_total_energy += vm.total_energy_consumed
    for storage in storage_resources:
        storage_total_carbon += (
                storage.total_carbon_operational + storage.total_carbon_embodied
        )
        storage_total_energy += storage.total_energy_consumed
    return storage_total_carbon, storage_total_energy, vm_total_carbon, vm_total_energy


def process_cost_csv(csv_data: str) -> tuple[list[CostResource], float, float]:
    """
    Process CSV data into a CostResource list.

    Args:
        csv_data: Raw CSV data

    Returns:
        list[CostResource]: Processed cost resource list
        float: Total compute cost
        float: Total storage cost
    """
    rows = csv_data.splitlines()
    if len(rows) <= 1:
        raise KnownException("Cost CSV data is empty")

    csv_reader = csv.DictReader(rows)

    logger.info("Processing Cost CSV...")
    cost_resources: list[CostResource] = []
    total_compute_cost = 0.0
    total_storage_cost = 0.0
    for row in csv_reader:
        consumed_service = row.get("ConsumedService", "").lower()
        if "microsoft.compute" == consumed_service:
            total_compute_cost += str_to_float(row.get("CostInBillingCurrencyEUR", "0"))
        elif "microsoft.storage" == consumed_service:
            total_storage_cost += str_to_float(row.get("CostInBillingCurrencyEUR", "0"))
        else:
            cost_resource = create_cost_resource(row)
            if cost_resource.id == "":
                continue
            cost_resources.append(cost_resource)
    logger.info("Cost CSV processed")
    return cost_resources, total_compute_cost, total_storage_cost


def create_cost_resource(row):
    """
    Creates a cost resource from the given row
    """
    region = row.get("ResourceLocation", "unknown")
    cost_resource = CostResource(
        id=row.get("ResourceId"),
        name=row.get("ProductName", ""),
        region=region,
        subscription=row.get("SubscriptionId", "unknown"),
        carbon_intensity=PaasCiMapper.calculate_ci(region.lower()),
        services_cost=str_to_float(row.get("CostInBillingCurrencyEUR", "0"))
    )
    timestamp = row.get("Date", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"))
    cost_resource.time_points = [timestamp]
    return cost_resource


def create_cost_report(cost_resources: list[CostResource], date: str, out_file: str):
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
                cost_resource.name,
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
