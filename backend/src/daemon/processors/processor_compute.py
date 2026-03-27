from __future__ import annotations

import logging

from backend.src.daemon.abstract_carbon_daemon_processor import (
    AbstractCarbonDaemonProcessor,
)

from backend.src.daemon.readers.reader_compute import VMReader
from backend.src.daemon.runners.runner_compute import CarbonDaemonRunnerCompute
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonProcessorCompute(AbstractCarbonDaemonProcessor):
    """
    Carbon Daemon processor implementation dedicated to Virtual Machines.
    """

    def __init__(
        self,
    ):
        """
        Initialize abstract carbon daemon processor.

        Args:
        """
        self.resource_type = ResourceType.VIRTUAL_MACHINE
        self.source_type = ""

        self.reader: self.init_reader()  # TODO: init from source type
        self.runner: CarbonDaemonRunnerCompute()
        # TODO: Implement writers
        # self.writer: AbstractWriter
