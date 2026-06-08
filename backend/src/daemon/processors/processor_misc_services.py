from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)
from backend.src.core.yaml_config_loader import DaemonConfig

from backend.src.daemon.readers.reader_misc_services import Reader_Misc_Services
from backend.src.daemon.runners.runner_misc_services import Runner_Misc_Services
from backend.src.daemon.writers.writer_misc_services import Writer_Misc_Services
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.resource import ResourceType

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

        self._reader = Reader_Misc_Services(config)
        self._runner = Runner_Misc_Services()
        self._writer = Writer_Misc_Services(config, self.date, self.writer_csv_dict_writer, self.resource_result)
        # self._writer: AbstractWriter

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.MISC_SERVICES

    @property
    def reader(self) -> AbstractReader:
        return self._reader

    @property
    def runner(self) -> AbstractRunner:
        return self._runner

    @property
    def writer(self) -> AbstractWriter:
        return self._writer
