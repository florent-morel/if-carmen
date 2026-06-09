from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)

from backend.src.daemon.readers.reader_storage import Reader_Storage
from backend.src.daemon.runners.runner_storage import Runner_Storage
from backend.src.daemon.writers.writer_storage import Writer_Storage
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class Processor_Storage(AbstractProcessor):
    """
    Carbon Daemon processor implementation dedicated to Storage.
    """

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.STORAGE

    @property
    def reader(self) -> AbstractReader:
        if not self._reader:
            self._reader = Reader_Storage(self.config)
        return self._reader

    @property
    def runner(self) -> AbstractRunner:
        if not self._runner:
            self._runner = Runner_Storage()
        return self._runner

    @property
    def writer(self) -> AbstractWriter:
        if not self._writer:
            self._writer = Writer_Storage(self.config, self.date, self.writer_csv_dict_writer, self.resource_result)
        return self._writer
