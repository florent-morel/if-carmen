
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.src.daemon.writers.writer_factory import (
    DefaultWriterFactory,
    WriterFactory,
)

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.readers.reader_factory import (
    DefaultReaderFactory,
    ReaderFactory,
)
from backend.src.schemas.resource import Resource, ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonResult:
    """Container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        dict_resource_daemon_result: dict[ResourceType, [ResourceDaemonResult]],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,
        error_message: str = "",
    ):
        self.success: bool = success
        self.dict_resource_daemon_result: dict = dict_resource_daemon_result
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.error_message: str = error_message

    def create_CarbonDaemonResult(self, success,
                                  execution_time,
                                  resourceType: ResourceType,
                                  processed_resources: list[Resource]
                                  ) -> CarbonDaemonResult:
        """
        Create a CarbonDaemonResult from the list of processed resources.

        Args:
            success: whether the call to the IF has been successful.
            execution_time: time to execute the call.
            processed_resources: List of processed resources.

        Returns:
            CarbonDaemonResult
        """

        dict_processed_resources = dict[resourceType, processed_resources]

        total_carbon_operational = sum(
            resource.total_carbon_operational
            for resource in processed_resources
        )

        total_carbon_embodied = sum(
            resource.total_carbon_embodied
            for resource in processed_resources
        )

        total_carbon_emitted = sum(
            resource.total_carbon_emitted
            for resource in processed_resources
        )
        total_energy_consumed = sum(
            resource.total_energy_consumed
            for resource in processed_resources
        )
        result = CarbonDaemonResult(
            success=True,
            dict_processed_resources=dict_processed_resources,
            total_energy_consumed=total_energy_consumed,
            total_carbon_operational=total_carbon_operational,
            total_carbon_embodied=total_carbon_embodied,
            total_carbon_emitted=total_carbon_emitted,
            execution_time=execution_time
        )

        return result


class ResourceDaemonResult:
    """Resource specific container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        resourceType: ResourceType,
        list_processed_resources: list[Resource],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,
        error_message: str = "",
    ):
        self.success: bool = success
        self.list_processed_resources: list = list_processed_resources
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.error_message: str = error_message

    def create_ResourceDaemonResult(self, success, execution_time, resourceType: ResourceType, processed_resources: list[Resource]) -> CarbonDaemonResult:
        """
        Create a ResourceDaemonResult from the list of processed resources.

        Args:
            success: whether the call to the IF has been successful.
            execution_time: time to execute the call.
            processed_resources: List of processed resources.

        Returns:
            ResourceDaemonResult
        """

        list_processed_resources = list[processed_resources]

        total_carbon_operational = sum(
            resource.total_carbon_operational
            for resource in processed_resources
        )

        total_carbon_embodied = sum(
            resource.total_carbon_embodied
            for resource in processed_resources
        )

        total_carbon_emitted = sum(
            resource.total_carbon_emitted
            for resource in processed_resources
        )
        total_energy_consumed = sum(
            resource.total_energy_consumed
            for resource in processed_resources
        )
        result = ResourceDaemonResult(
            success=True,
            resourceType=resourceType,
            list_processed_resources=list_processed_resources,
            total_energy_consumed=total_energy_consumed,
            total_carbon_operational=total_carbon_operational,
            total_carbon_embodied=total_carbon_embodied,
            total_carbon_emitted=total_carbon_emitted,
            execution_time=execution_time
        )

        return result
