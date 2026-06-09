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

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.MISC_SERVICES

    @property
    def reader(self) -> AbstractReader:
        if not self._reader:
            self._reader = Reader_Misc_Services(self.config)
        return self._reader

    @property
    def runner(self) -> AbstractRunner:
        if not self._runner:
            self._runner = Runner_Misc_Services()
        return self._runner

    @property
    def writer(self) -> AbstractWriter:
        if not self._writer:
            self._writer = Writer_Misc_Services(self.config, self.date, self.writer_csv_dict_writer, self.resource_result)
        return self._writer
