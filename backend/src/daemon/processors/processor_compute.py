from __future__ import annotations

import logging
import csv

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)

from backend.src.daemon.readers.reader_compute import Reader_Compute
from backend.src.daemon.runners.runner_compute import Runner_Compute
from backend.src.daemon.writers.writer_compute import Writer_Compute
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class Processor_Compute(AbstractProcessor):
    """
    Carbon Daemon processor implementation dedicated to Compute.
    """

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.VIRTUAL_MACHINE

    @property
    def reader(self) -> AbstractReader:
        if not self._reader:
            self._reader = Reader_Compute(self.config)
        return self._reader

    @property
    def runner(self) -> AbstractRunner:
        if not self._runner:
            self._runner = Runner_Compute()
        return self._runner

    def writer(self, dict_writer: csv.DictWriter) -> AbstractWriter:
        if not self._writer:
            self._writer = Writer_Compute(
                self.config,
                self.execution_date,
                dict_writer,
                self.resource_type_result,
            )
        return self._writer
