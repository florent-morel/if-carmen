from __future__ import annotations

import logging

from backend.src.daemon.processors.abstract_processor import (
    AbstractCarbonDaemonProcessor,
)

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.reader_compute import Reader_Compute
from backend.src.daemon.runners.runner_compute import RunnerCompute
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class CarbonDaemonProcessorCompute(AbstractCarbonDaemonProcessor):
    """
    Carbon Daemon processor implementation dedicated to Virtual Machines.
    """

    def __init__(self, config: DaemonConfig):
        """
        Initialize carbon daemon processor.

        Args:
        """
        self.resource_type = ResourceType.VIRTUAL_MACHINE
        self.config = config

        self.reader = Reader_Compute(self.config)
        self.runner = RunnerCompute()
        # TODO: Implement writers
        # self.writer: AbstractWriter
