
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
from backend.src.daemon.abstract_carbon_daemon import (
    CarbonDaemonResult,
)
from backend.src.daemon.carbon_daemon_result import (
    ResourceDaemonResult,
)
from backend.src.daemon.readers.reader_factory import (
    DefaultReaderFactory,
    ReaderFactory,
)
from backend.src.daemon.writers.writer_factory import (
    DefaultWriterFactory,
    WriterFactory,
)
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter

logger = logging.getLogger(__name__)


class AbstractCarbonDaemonProcessor(ABC):
    def __init__(
        self,
        # daemon_config: DaemonConfig,
        # reader_factory: ReaderFactory | None = None,
        # writer_factory: WriterFactory | None = None,
        # list_carbon_daemon_resource_processors: list[AbstractCarbonDaemonProcessor] | None = None,
        # carbon_daemon_result: CarbonDaemonResult | None = None,
    ):
        """
        Initialize abstract carbon daemon processor.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """
        self.resource_type: ResourceType
        self.reader: AbstractReader
        self.runner: AbstractRunner
        self.writer: AbstractWriter

        self.reader_factory: ReaderFactory = reader_factory or DefaultReaderFactory()
        self.writer_factory: WriterFactory = writer_factory or DefaultWriterFactory()

        # Resources built by the reader to be handled by the runner
        self.list_resources_to_process = None
        self.carbon_daemon_result: CarbonDaemonResult = self.create_CarbonDaemonResult(
            success=None, execution_time=None, processed_resources=None)

    @abstractmethod
    def read(self
            ) -> list[Resource]:
        """
        Call the associated Reader to read data source.

        Returns:
        """

    @abstractmethod
    def run(self
            ) -> ResourceDaemonResult:
        """
        Execute the workflow dedicated to a given Resource.

        Returns:
            ResourceDaemonResult containing execution results
        """

    @abstractmethod
    def process_carbon_calculations(
        self,
    ) -> list[Resource]:
        """
        Process resources through the carbon calculation engine.

        Args:
            resources: List of resources to process

        Returns:
            Calculation result with list of resources with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """
