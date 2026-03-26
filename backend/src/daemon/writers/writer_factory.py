



"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

from backend.src.schemas.resource import Resource
import csv
import logging
import time
from enum import Enum
from typing import Protocol, runtime_checkable

from backend.src.common.constants import (
    CARMEN_LOGO,
    HOURLY_INTERVAL_SECONDS,
    DAILY_SECONDS,
    UploadType,
)
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.cost_helpers import (
    create_cost_report,
    get_carbon_and_energy_values,
    process_cost_csv,
)
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
from backend.src.daemon.writers.compute.azure_compute_writer import AzureComputeWriter
from backend.src.daemon.writers.compute.compute_writer import ComputeWriter
from backend.src.daemon.writers.compute.local_compute_writer import LocalComputeWriter
from backend.src.schemas.costResource import CostResource
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)


from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)

@runtime_checkable
class WriterFactory(Protocol):
    """Protocol for writer factory implementations."""

    def create_writer(
        self, daemon_config: DaemonConfig, vms: list[VirtualMachine]
    ) -> ComputeWriter:
        """Create a writer instance based on configuration."""


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

        raise ValueError("unsupported source type in configuration")


class DefaultWriterFactory:
    """Default factory for creating writer instances."""

    def create_writer(
        self, daemon_config: DaemonConfig, vms: list[VirtualMachine]
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
        upload_type = daemon_config.upload.type.lower()

        if upload_type == UploadType.AZURE.value:
            return AzureComputeWriter(vms, daemon_config)
        if upload_type == UploadType.LOCAL.value:
            return LocalComputeWriter(vms, daemon_config)

        raise ValueError(f"unsupported upload type: {upload_type}")




