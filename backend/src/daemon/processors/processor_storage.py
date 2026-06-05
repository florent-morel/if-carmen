from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)
from backend.src.core.yaml_config_loader import DaemonConfig

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

    def __init__(self, config: DaemonConfig):
        """
        Initialize processor dedicated to storage.

        Args:
        """
        super().__init__(config)

        self._reader = Reader_Storage(config)
        self._runner = Runner_Storage()
        self._writer = Writer_Storage(config, self.date, self.writer_csv_dict_writer, self.resource_result)
        # self._writer: AbstractWriter

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.STORAGE

    @property
    def reader(self) -> AbstractReader:
        return self._reader

    @property
    def runner(self) -> AbstractRunner:
        return self._runner

    @property
    def writer(self) -> AbstractWriter:
        return self._writer
