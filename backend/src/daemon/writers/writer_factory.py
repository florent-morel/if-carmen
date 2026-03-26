
"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from backend.src.common.constants import (
    ResourceType,
    UploadType,
)
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.writers.compute.azure_compute_writer import AzureComputeWriter
from backend.src.daemon.writers.compute.compute_writer import ComputeWriter
from backend.src.daemon.writers.compute.local_compute_writer import LocalComputeWriter
from backend.src.schemas.resource import Resource

logger = logging.getLogger(__name__)


@runtime_checkable
class WriterFactory(Protocol):
    """Protocol for writer factory implementations."""

    def create_writer(
        self, daemon_config: DaemonConfig, resources: list[Resource]
    ) -> ComputeWriter:
        """Create a writer instance based on configuration."""


class DefaultWriterFactory:
    """Default factory for creating writer instances."""

    def create_writer(
        self, daemon_config: DaemonConfig, resources: list[Resource],
        resourceType: ResourceType
    ) -> ComputeWriter:
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
        if (resourceType == ResourceType.VIRTUAL_MACHINE):
            upload_type = daemon_config.upload.type.lower()

            if upload_type == UploadType.AZURE.value:
                return AzureComputeWriter(resources, daemon_config)
            if upload_type == UploadType.LOCAL.value:
                return LocalComputeWriter(resources, daemon_config)
        # elif (resourceType == ResourceType.STORAGE):
        #     return StorageWriter(resources, daemon_config)

        raise ValueError(f"unsupported upload type: {upload_type}")
