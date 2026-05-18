from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)
from backend.src.core.yaml_config_loader import DaemonConfig

from backend.src.daemon.readers.reader_misc_services import Reader_Misc_Services
from backend.src.daemon.runners.runner_misc_services import Runner_Misc_Services
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter

logger = logging.getLogger(__name__)


class Processor_Misc_Services(AbstractProcessor):
    """
    Carbon Daemon processor implementation dedicated to Misc Services.
    """

    def __init__(self, config: DaemonConfig):
        """
        Initialize processor dedicated to Misc Services.

        Args:
        """
        super().__init__(config)

        self.reader = Reader_Misc_Services(config)
        self.runner = Runner_Misc_Services()
        # TODO: Implement writers
        # self._writer: AbstractWriter

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.MISC_SERVICES

    @property
    def reader(self) -> AbstractReader:
        return self.reader

    @property
    def runner(self) -> AbstractRunner:
        return self.runner

    @property
    def writer(self) -> AbstractWriter:
        # TODO: Implement writer
        return None
