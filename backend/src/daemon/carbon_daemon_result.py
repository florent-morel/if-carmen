from __future__ import annotations

import logging

# from backend.src.daemon.writers.writer_factory import (
#    DefaultWriterFactory,
#    WriterFactory,
# )


# from backend.src.daemon.readers.reader_factory import (
#    DefaultReaderFactory,
#    ReaderFactory,
# )
from backend.src.schemas.resource import Resource, ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonResult:
    """Container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        dict_resource_result: dict[ResourceType, ResourceTypeResult],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,
        error_message: str = "",
    ):
        self.success: bool = success
        self.dict_resource_result: dict = dict_resource_result
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.error_message: str = error_message


class ResourceTypeResult:
    """Resource specific container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        resource_type: ResourceType,
        list_processed_resources: list[Resource],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,
        error_message: str = "",
    ):
        self.success: bool = success
        self.resource_type: ResourceType = resource_type
        self.list_processed_resources: list = list_processed_resources
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.error_message: str = error_message
