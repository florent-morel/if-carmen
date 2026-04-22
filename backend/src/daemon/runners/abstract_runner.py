from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.common.known_exception import KnownException
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.carbon_daemon_result import (
    ResourceTypeResult,
)
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractReader
from backend.src.daemon.writers.abstract_writer import AbstractWriter

logger = logging.getLogger(__name__)


class AbstractRunner(ABC):
    """
    Main abstract class to provide the methods for the implementation of the call to the Impact Framework.
    """

    @abstractmethod
    def run(self, list_resources_to_process: list[Resource]) -> ResourceTypeResult:
        """
        Run the Impact Framework and build result for a given ResourceType.

        Returns:
            ResourceTypeResult containing execution results
        """

    # Resources built by the reader to be handled by the runner
    @property
    @abstractmethod
    def resource_type_result(self) -> ResourceTypeResult | None:
        pass

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
            total_energy_consumed=0,
            total_carbon_operational=0,
            total_carbon_embodied=0,
            total_carbon_emitted=0,
            execution_time=execution_time,
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

        return resource_type_result
