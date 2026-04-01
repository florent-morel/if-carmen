from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)
from backend.src.core.yaml_config_loader import DaemonConfig

from backend.src.daemon.readers.reader_storage import Reader_Storage
from backend.src.daemon.runners.runner_storage import Runner_Storage
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.daemon.carbon_daemon_result import (
    ResourceDaemonResult,
)

logger = logging.getLogger(__name__)


class Processor_Storage(AbstractProcessor):
    """
    Main daemon class responsible for orchestrating carbon emission calculations.

    This class coordinates reading infrastructure data, processing it through
    the carbon engine, and writing the results to the specified destination.
    """

    def __init__(
        self, config: DaemonConfig
    ):
        """
        Initialize processor dedicated to storage.

        Args:
        """
        self.resource_type = ResourceType.STORAGE

        self.reader = Reader_Storage(config)
        self.runner = Runner_Storage()
        # TODO: Implement writers
        # self.writer: AbstractWriter

    def resource_type(self) -> ResourceType:
        self.resource_type

    def reader(self) -> AbstractReader:
        self.reader

    def runner(self) -> AbstractRunner:
        self.runner

    def writer(self) -> AbstractWriter:
        # self.writer
        return None

    def list_resources_to_process(self) -> list[Resource] | None:
        return self._reader.list_resources_to_process

    # Resources built by the reader to be handled by the runner
    def resource_daemon_result(self) -> ResourceDaemonResult | None:
        return self._runner.resource_daemon_result
