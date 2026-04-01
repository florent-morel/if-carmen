from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.common.known_exception import KnownException
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.carbon_daemon_result import (
    ResourceDaemonResult,
)
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractReader
from backend.src.daemon.writers.abstract_writer import AbstractWriter

logger = logging.getLogger(__name__)


class AbstractRunner(ABC):
    """
    Main abstract class to provide the methods for the implementation of the call to the Impact Framework.
    """

    @abstractmethod
    def run(self, list_resources_to_process: list[Resource]) -> ResourceDaemonResult:
        """
        Run the Impact Framework and build result for a given ResourceType.

        Returns:
            ResourceDaemonResult containing execution results
        """
    # Resources built by the reader to be handled by the runner
    @property
    @abstractmethod
    def resource_daemon_result(self) -> ResourceDaemonResult | None:
        pass

    @abstractmethod
    def process_carbon_calculations(
        self, list_resources_to_process: list[Resource]
    ) -> list[Resource]:
        """
        Process resources impact through the carbon calculation engine.

        Args:
            vms: List of virtual machines to process

        Returns:
            List of virtual machines with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """
