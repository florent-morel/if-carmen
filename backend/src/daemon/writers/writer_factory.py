
"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

import logging
import time
import csv
from typing import Protocol, runtime_checkable

from backend.src.common.constants import (
    ResourceType,
    UploadType,
)
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.daemon.writers.compute.azure_compute_writer import AzureComputeWriter
from backend.src.daemon.writers.compute.compute_writer import ComputeWriter
from backend.src.daemon.writers.compute.local_compute_writer import LocalComputeWriter
from backend.src.schemas.resource import Resource
from backend.src.daemon.abstract_carbon_daemon import CarbonDaemonResult

logger = logging.getLogger(__name__)


@runtime_checkable
class WriterFactory(Protocol):
    """Protocol for writer factory implementations."""

    def create_writer(
        self, daemon_config: DaemonConfig,
        carbonDaemonResult: CarbonDaemonResult
    ) -> list[ComputeWriter]:
        """Create a writer instance based on configuration."""

    def create_CO2_report(
        self,
        list_active_writers: list[AbstractWriter]
    ):
        """
        Creates a CSV report containing all resource types.
        Handles VMs, Storage, and future resource categories in one file.
        """
        # resources = self.resources or []

        logger.info(
            "Creating CSV report with %d resources",
            len(resources),
        )
        start = time.time()

        # TODO: Implement loop on all active resources
        with open(self.out_file, mode="w", newline="", encoding="utf-8") as report:
            writer_orchestrator = csv.writer(report)

            list_row_headers = list[str]
            list_content = list[str]

            for writer in list_active_writers:
                # call each storage writer to get rows
                list_row_headers.append(writer.build_rows_headers())
                list_content.append(writer.build_content())


            # Write Row headers and content
            writer_orchestrator.writerows(list_row_headers)
            for row in self.build_content():
                writer_orchestrator.writerow(row)

        elapsed_time = time.time() - start
#         logging.info("Total carbon emitted: %.2f kg CO2", vm_carbon)
#         logging.info("Total energy consumed: %.2f kWh", vm_energy)
        logger.info("CSV report created in %.2f seconds", elapsed_time)
        logger.info(
            "  Resources: %d resources",
            len(resources),
        )
        logger.info("Report saved to: %s", self.out_file)


class DefaultWriterFactory:
    """Default factory for creating writer instances."""

    def create_writer(
        self, daemon_config: DaemonConfig,
        carbonDaemonResult: CarbonDaemonResult
    ) -> list[ComputeWriter]:
        """
        Create a writer based on daemon configuration.

        Args:
            daemon_config: Configuration containing upload information
            vms: List of virtual machines to write

        Returns:
            Writer instance

        Raises:
            ValueError: If unsupported upload type is specified
        """
        listComputeWriter = list[ComputeWriter]()
        for resourceType, resources in carbonDaemonResult.dict_processed_resources.items():
            if (resourceType == ResourceType.VIRTUAL_MACHINE):
                upload_type = daemon_config.upload.type.lower()

                if upload_type == UploadType.AZURE.value:
                    listComputeWriter.append(AzureComputeWriter(resources, daemon_config))
                if upload_type == UploadType.LOCAL.value:
                    listComputeWriter.append(LocalComputeWriter(resources, daemon_config))
            # elif (resourceType == ResourceType.STORAGE):
                    #listComputeWriter.append(StorageWriter(resources, daemon_config))

        return listComputeWriter

        raise ValueError(f"unsupported upload type: {upload_type}")
