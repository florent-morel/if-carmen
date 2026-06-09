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
import csv
from abc import ABC, abstractmethod

from backend.src.daemon.carbon_daemon_result import (
    ResourceTypeResult,
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

    @abstractmethod
    def writer(self, dict_writer: csv.DictWriter) -> AbstractWriter:
        pass

    def __init__(self, config: DaemonConfig, execution_date: str = ""):
        """
        Initialize the abstract carbon daemon processor.

        Args:
            config: Configuration for daemon operations
            execution_date: Execution date for the processor (optional)
        """
        self.config = config
        self.execution_date: str = execution_date
        self.list_resources_to_process: list[Resource] = []
        self.resource_type_result: ResourceTypeResult | None = None
        self._reader: AbstractReader | None = None
        self._runner: AbstractRunner | None = None
        self._writer: AbstractWriter | None = None

    def read(self, csv_data: str) -> list[Resource]:
        """
        Call the associated Reader to read data source.

        Args:
            csv_data: CSV data to be read

        Returns:
            List of resources read from the CSV data
        """
        logger.debug(f"Inside AbstractProcessor reader: {self.reader}")
        self.list_resources_to_process.extend(self.reader.read(csv_data))
        return self.list_resources_to_process

    def run(self) -> ResourceTypeResult:
        """
        Execute the workflow dedicated to a given Resource.

        Returns:
            ResourceTypeResult containing execution results
        """
        self.resource_type_result = None
        if self.list_resources_to_process and len(self.list_resources_to_process) > 0:
            logger.info("list_resources_to_process: %d", len(self.list_resources_to_process))
            self.resource_type_result = self.runner.run(self.list_resources_to_process)
        else:
            logger.error("No resource to process for this runner.")
        return self.resource_type_result

    def write(self, dict_writer: csv.DictWriter) -> None:
        """
        Call the associated Writer to write results to output.

        Args:
            dict_writer: CSV DictWriter to write the output
        """
        if not self.resource_type_result:
            logger.warning("No resource result to write for %s", self.resource_type)
            return
        self.writer(dict_writer).write_content(
            self.resource_type_result.list_processed_resources
        )