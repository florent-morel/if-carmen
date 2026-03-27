from __future__ import annotations

import logging

from backend.src.daemon.abstract_carbon_daemon_processor import (
    AbstractCarbonDaemonProcessor,
)

from backend.src.daemon.readers.storage_reader import StorageReader
from backend.src.daemon.runners.runner_storage import CarbonDaemonRunnerStorage
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonProcessorStorage(AbstractCarbonDaemonProcessor):
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
        """
        self.resource_type = ResourceType.STORAGE

        self.reader: StorageReader() # TODO: init from source type
        self.runner: CarbonDaemonRunnerStorage()
        # TODO: Implement writers
        # self.writer: AbstractWriter
