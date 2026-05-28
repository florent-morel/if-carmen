from __future__ import annotations

import logging

from backend.src.schemas.resource import Resource, ResourceType
from backend.src.common.known_exception import CarmenException

logger = logging.getLogger(__name__)


class CarbonDaemonResult:
    """
    Container for daemon execution results.
    """

    def __init__(
        self,
        success: bool,
        dict_resource_result: dict[ResourceType, ResourceTypeResult],
        list_exceptions: list[CarmenException],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,

        # Total values computed by different processors
        # To properly estimate misc services
        # We need all already computed resources
        # And get their billing cost
        compute_energy: float = 0.0,
        storage_energy: float = 0.0,
        compute_embodied: float = 0.0,
        storage_embodied: float = 0.0,
        compute_cost: float = 0.0,
        storage_cost: float = 0.0,
    ):
        self.success: bool = success
        self.dict_resource_result: dict = dict_resource_result
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.list_exceptions: list = list_exceptions

    def get_resource_type_list_exception(self, resource_type: ResourceType) -> dict[ResourceType, list[CarmenException]] | None:
        """
        Fetches exceptions in different resource results.
        """
        dict_resource_result_exceptions: dict[ResourceType, list[CarmenException]] = None

        if resource_type is None:
            # No resource_type provided in input
            # Iterate on all results
            for resource_result in self.dict_resource_result.values():
                if resource_result and resource_result.list_exceptions:
                    dict_resource_result_exceptions[resource_result.resource_type] = resource_result.list_exceptions

        else:
            # Fetch only for given resource_type
            logger.info(f"Fetching exceptions for ResourceTypeResult {resource_type}")
            resource_result = self.dict_resource_result.get(resource_type)
            logger.info(f"resource results: {resource_result}")
            if resource_result and resource_result.list_exceptions:
                dict_resource_result_exceptions[resource_result.resource_type] = resource_result.list_exceptions

        return dict_resource_result_exceptions


class ResourceTypeResult:
    """Resource specific container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        resource_type: ResourceType,
        list_processed_resources: list[Resource],
        list_exceptions: list[CarmenException],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,
        total_billing_cost: float = 0.0,
    ):
        self.success: bool = success
        self.resource_type: ResourceType = resource_type
        self.list_processed_resources: list = list_processed_resources
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.list_exceptions: list = list_exceptions
        self.total_billing_cost: float = total_billing_cost
