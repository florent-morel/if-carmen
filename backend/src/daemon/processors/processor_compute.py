from __future__ import annotations

import logging
from enum import Enum

from backend.src.daemon.processors.abstract_processor import (
    AbstractCarbonDaemonProcessor,
)

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.compute.reader_compute_azure import ReaderComputeAzure
from backend.src.daemon.readers.compute.reader_compute_local import ReaderComputeLocal
from backend.src.daemon.runners.runner_compute import CarbonDaemonRunnerCompute
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class ComputeSourceType(Enum):
    """Supported source types for compute processing."""

    AZURE = "AZURE"
    LOCAL = "LOCAL"


class CarbonDaemonProcessorCompute(AbstractCarbonDaemonProcessor):
    """
    Carbon Daemon processor implementation dedicated to Virtual Machines.
    """

    def __init__(self, source_type: ComputeSourceType, config: DaemonConfig):
        """
        Initialize carbon daemon processor.

        Args:
        """
        self.resource_type = ResourceType.VIRTUAL_MACHINE
        self.source_type = source_type
        self.config = config

        self.reader = self.init_reader()  # TODO: init from source type
        self.runner = CarbonDaemonRunnerCompute()
        # TODO: Implement writers
        # self.writer: AbstractWriter

        def init_reader():
            if self.source_type == ComputeSourceType.AZURE:
                self.reader = ReaderComputeAzure(self.daemon_config)
            if self.source_type == ComputeSourceType.LOCAL:
                self.reader = ReaderComputeLocal(self.daemon_config)
