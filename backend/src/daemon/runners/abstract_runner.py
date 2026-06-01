from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.common.carmen_exception import CarmenException
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.carbon_daemon_result import (
    ResourceTypeResult,
)
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.writers.abstract_writer import AbstractWriter

logger = logging.getLogger(__name__)


class AbstractRunner(ABC):
    """
    Main abstract class to provide the methods for the implementation of the call to the Impact Framework.
    """

    @abstractmethod
    def should_run(self, list_resources_to_process: list[Resource]) -> bool:
        """
        Check if the runner has the right context to process.

        Returns:
            True if runner should run, false otherwise.
        """
        pass

    @abstractmethod
    def run(self, list_resources_to_process: list[Resource]) -> ResourceTypeResult:
        """
        Run the Impact Framework and build result for a given ResourceType.

        Returns:
            ResourceTypeResult containing execution results
        """

    @abstractmethod
    def process_carbon_calculations(
        self, list_resources_to_process: list[Resource]
    ) -> list[Resource]:
        """
        Process resources impact through the carbon calculation engine.

        Args:
            computing_resources: List of computing resources to process

        Returns:
            List of computing resources with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """

    def create_resource_type_result(
        self,
        success,
        execution_time,
        resource_type: ResourceType,
        list_processed_resources: list[Resource],
        list_exceptions: list[Exception],
    ) -> ResourceTypeResult:
        """
        Create a ResourceTypeResult from the list of processed resources.

        Args:
            success: whether the call to the IF has been successful.
            execution_time: time to execute the call.
            processed_resources: List of processed resources.

        Returns:
            ResourceTypeResult
        """
        resource_type_result = ResourceTypeResult(
            success=success,
            resource_type=resource_type,
            list_processed_resources=list_processed_resources,
            list_exceptions=list_exceptions,
            total_energy_consumed=0,
            total_carbon_operational=0,
            total_carbon_embodied=0,
            total_carbon_emitted=0,
            execution_time=execution_time,
            total_billing_cost=0,
        )

        for resource_result in list_processed_resources:
            resource_type_result.total_energy_consumed += (
                resource_result.total_energy_consumed
            )
            resource_type_result.total_carbon_operational += (
                resource_result.total_carbon_operational
            )
            resource_type_result.total_carbon_embodied += (
                resource_result.total_carbon_embodied
            )
            resource_type_result.total_carbon_emitted += (
                resource_result.total_carbon_emitted
            )

            # If this resource is indeed emitting CO2
            # then consider it for the computation of misc_services impact
            if resource_result.total_carbon_emitted > 0:
                resource_type_result.total_billing_cost += (
                    resource_result.billing_cost
                )

        return resource_type_result
