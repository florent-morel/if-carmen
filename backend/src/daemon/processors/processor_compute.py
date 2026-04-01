from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.reader_compute import Reader_Compute
from backend.src.daemon.runners.runner_compute import Runner_Compute
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter

logger = logging.getLogger(__name__)


class Processor_Compute(AbstractProcessor):
    """
    Carbon Daemon processor implementation dedicated to Virtual Machines.
    """

    def __init__(self, config: DaemonConfig):
        """
        Initialize carbon daemon processor.

        Args:
        """
        super().__init__(config)

        self._reader = Reader_Compute(self.config)
        self._runner = Runner_Compute()
        # TODO: Implement writers
        # self._writer: AbstractWriter

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.VIRTUAL_MACHINE

    @property
    def reader(self) -> AbstractReader:
        return self._reader

    @property
    def runner(self) -> AbstractRunner:
        return self._runner

    @property
    def writer(self) -> AbstractWriter:
        # TODO: Implement writer
        return None
