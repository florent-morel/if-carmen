from __future__ import annotations

import logging

from backend.src.daemon.abstract_carbon_daemon_processor import (
    AbstractCarbonDaemonProcessor,
)

from backend.src.daemon.readers.vm_reader import VMReader
from backend.src.daemon.runners.runner_vm import CarbonDaemonVMRunner
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonVMProcessor(AbstractCarbonDaemonProcessor):
    """
    Carbon Daemon processor implementation dedicated to Virtual Machines.
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
        self.source_type = ""

        self.reader: self.init_reader()  # TODO: init from source type
        self.runner: CarbonDaemonVMRunner()
        # TODO: Implement writers
        # self.writer: AbstractWriter
