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
        self.resource_type = ResourceType.VIRTUAL_MACHINE
        super.config = config

        self.reader = Reader_Compute(self.config)
        self.runner = Runner_Compute()
        # TODO: Implement writers
        # self.writer: AbstractWriter
        #

    def resource_type(self) -> ResourceType:
        self.resource_type

    def reader(self) -> AbstractReader:
        self.reader

    def runner(self) -> AbstractRunner:
        self.runner

    def writer(self) -> AbstractWriter:
        # self.writer
        return None
