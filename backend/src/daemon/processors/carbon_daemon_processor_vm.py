
"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

import logging
import time

from backend.src.common.constants import (
    HOURLY_INTERVAL_SECONDS,
)
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException
from backend.src.daemon.abstract_carbon_daemon import (
    AbstractCarbonDaemon,
)

from backend.src.daemon.carbon_daemon_result import ResourceDaemonResult
from backend.src.schemas.resource import Resource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.abstract_carbon_daemon_processor import AbstractCarbonDaemonProcessor

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter
logger = logging.getLogger(__name__)


class CarbonDaemonVMProcessor(AbstractCarbonDaemonProcessor):
    """
    Main daemon class responsible for orchestrating carbon emission calculations.

    This class coordinates reading infrastructure data, processing it through
    the carbon engine, and writing the results to the specified destination.
    """


    def __init__(
        self,
        resource_type: ResourceType
    ):
        """
        Initialize abstract carbon daemon processor.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """
        self.resource_type = ResourceType.VIRTUAL_MACHINE

        self.reader: AbstractReader
        self.runner: AbstractRunner
        self.writer: AbstractWriter

        # Resources built by the reader to be handled by the runner
        self.list_resources_to_process = None
        self.carbon_daemon_result: CarbonDaemonResult = self.create_CarbonDaemonResult(
            success=None, execution_time=None, processed_resources=None)


