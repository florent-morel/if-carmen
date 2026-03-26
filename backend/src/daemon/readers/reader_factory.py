


#!/usr/bin/env python3
"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.abstract_reader import Reader
from backend.src.daemon.readers.compute.azure_compute_reader import (
    AzureComputeReaderStrategy,
)
from backend.src.daemon.readers.compute.local_compute_reader import (
    LocalComputeReaderStrategy,
)
from backend.src.daemon.readers.storage_reader import (
    StorageReaderStrategy,
)

logger = logging.getLogger(__name__)




@runtime_checkable
class ReaderFactory(Protocol):
    """Protocol for reader factory implementations."""

    def create_reader(self, daemon_config: DaemonConfig) -> Reader:
        """Create a reader instance based on configuration."""

class DefaultReaderFactory:
    """Default factory for creating reader instances."""

    def create_reader(self, daemon_config: DaemonConfig) -> Reader:
        """
        Create a reader based on daemon configuration.

        Args:
            daemon_config: Configuration containing source information

        Returns:
            Reader instance

        Raises:
            ValueError: If unsupported source type is specified
        """
        if daemon_config.source.type == "azure":
            return AzureComputeReaderStrategy(daemon_config)
        if daemon_config.source.type == "local":
            return LocalComputeReaderStrategy(daemon_config)
        if daemon_config.source.type == "StorageResource":
            return StorageReaderStrategy(daemon_config)

        raise ValueError("unsupported source type in configuration")


