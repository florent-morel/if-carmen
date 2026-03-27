from __future__ import annotations

import logging

from backend.src.daemon.abstract_carbon_daemon_processor import (
    AbstractCarbonDaemonProcessor,
)

from backend.src.daemon.readers.storage_reader import StorageReader
from backend.src.daemon.runners.runner_storage import CarbonDaemonStorageRunner
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonStorageProcessor(AbstractCarbonDaemonProcessor):
    """
    Main daemon class responsible for orchestrating carbon emission calculations.

    This class coordinates reading infrastructure data, processing it through
    the carbon engine, and writing the results to the specified destination.
    """

    def __init__(
        self,
    ):
        """
        Initialize abstract carbon daemon processor.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """
        self.resource_type = ResourceType.VIRTUAL_MACHINE

        self.reader: StorageReader() # TODO: init from source type
        self.runner: CarbonDaemonStorageRunner()
        # TODO: Implement writers
        # self.writer: AbstractWriter
