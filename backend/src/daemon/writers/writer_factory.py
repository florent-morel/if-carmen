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
    #    ResourceType,
    UploadType,
)
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.daemon.writers.compute.azure_compute_writer import AzureComputeWriter
from backend.src.daemon.writers.compute.compute_writer import ComputeWriter
from backend.src.daemon.writers.compute.local_compute_writer import LocalComputeWriter
from backend.src.schemas.resource import Resource
from backend.src.daemon.carbon_daemon_orchestrator import CarbonDaemonResult

logger = logging.getLogger(__name__)


@runtime_checkable
class WriterFactory(Protocol):
    """Protocol for writer factory implementations."""

    def create_writer(
        self, daemon_config: DaemonConfig, carbonDaemonResult: CarbonDaemonResult
    ) -> list[ComputeWriter]:
        """Create a writer instance based on configuration."""


class DefaultWriterFactory:
    """Default factory for creating writer instances."""

    def create_writer(
        self, daemon_config: DaemonConfig, carbonDaemonResult: CarbonDaemonResult
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
        for (
            resourceType,
            resources,
        ) in carbonDaemonResult.dict_processed_resources.items():
            if resourceType == ResourceType.VIRTUAL_MACHINE:
                upload_type = daemon_config.upload.type.lower()

                if upload_type == UploadType.AZURE.value:
                    listComputeWriter.append(
                        AzureComputeWriter(resources, daemon_config)
                    )
                if upload_type == UploadType.LOCAL.value:
                    listComputeWriter.append(
                        LocalComputeWriter(resources, daemon_config)
                    )
            # elif (resourceType == ResourceType.STORAGE):
            # listComputeWriter.append(StorageWriter(resources, daemon_config))

        return listComputeWriter

        raise ValueError(f"unsupported upload type: {upload_type}")
