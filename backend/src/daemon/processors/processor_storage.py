from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)
from backend.src.core.yaml_config_loader import DaemonConfig

from backend.src.daemon.readers.reader_storage import Reader_Storage
from backend.src.daemon.runners.runner_storage import Runner_Storage
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class Processor_Storage(AbstractProcessor):
    """
    Main daemon class responsible for orchestrating carbon emission calculations.

    This class coordinates reading infrastructure data, processing it through
    the carbon engine, and writing the results to the specified destination.
    """

    def __init__(
        self, config: DaemonConfig
    ):
        """
        Initialize processor dedicated to storage.

        Args:
        """
        self.resource_type = ResourceType.STORAGE

        super().reader = Reader_Storage(config)
        super().runner = Runner_Storage()
        # TODO: Implement writers
        # self.writer: AbstractWriter
