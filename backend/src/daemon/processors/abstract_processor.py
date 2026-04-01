"""
A Carbon Processor contains a reference to all the classes
needed to:
- Read input data.
- Run the call to the Impact Framework.
- Write output report.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from backend.src.daemon.carbon_daemon_result import (
    ResourceDaemonResult,
)
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.resource import Resource, ResourceType

logger = logging.getLogger(__name__)


class AbstractProcessor(ABC):

    @property
    @abstractmethod
    def resource_type(self) -> ResourceType:
        pass

    @property
    @abstractmethod
    def reader(self) -> AbstractReader:
        pass

    @property
    @abstractmethod
    def runner(self) -> AbstractRunner:
        pass

    @property
    @abstractmethod
    def writer(self) -> AbstractWriter:
        pass


    def __init__(self, config: DaemonConfig):
        """
        Initialize the abstract carbon daemon processor.

        Args:
            daemon_config: Configuration for daemon operations
            writer_factory: Factory for creating writer instances (optional)
        """

        # Resources built by the reader to be handled by the runner
        self.list_resources_to_process = list[Resource] | None
        self.resource_daemon_result: ResourceDaemonResult | None

    def read(self) -> list[Resource]:
        """
        Call the associated Reader to read data source.

        Returns:
        """
        self.list_resources_to_process = self.reader.read()

    def run(self) -> ResourceDaemonResult:
        """
        Execute the workflow dedicated to a given Resource.

        Returns:
            ResourceDaemonResult containing execution results
        """
        self.resource_daemon_result = self.runner.run(self.list_resources_to_process)
