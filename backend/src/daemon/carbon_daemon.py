#!/usr/bin/env python3
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

from backend.src.common.constants import CARMEN_LOGO
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


class UploadType(Enum):
    """Supported upload destination types."""

    AZURE = "azure"
    LOCAL = "local"


@runtime_checkable
class ReaderFactory(Protocol):
    """Protocol for reader factory implementations."""

    def create_reader(self, daemon_config: DaemonConfig) -> Reader:
        """Create a reader instance based on configuration."""


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
        if daemon_config.source.type == "StorageResource":
            return StorageReaderStrategy(daemon_config)

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


class CarbonDaemonResult:
    """Container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        vm_count: int = 0,
        execution_time: float = 0.0,
        error_message: str = "",
    ):
        self.success: bool = success
        self.vm_count: int = vm_count
        self.execution_time: float = execution_time
        self.error_message: str = error_message


class CarbonDaemon:
    """
    Main daemon class responsible for orchestrating carbon emission calculations.

    This class coordinates reading infrastructure data, processing it through
    the carbon engine, and writing the results to the specified destination.
    """

    HOURLY_INTERVAL_SECONDS: int = 3600
    DAILY_SECONDS: int = 86400

    def __init__(
        self,
        daemon_config: DaemonConfig,
        reader_factory: ReaderFactory | None = None,
        writer_factory: WriterFactory | None = None,
    ):
        """
        Initialize the carbon daemon.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """
        self.config: DaemonConfig = daemon_config
        self.reader_factory: ReaderFactory = reader_factory or DefaultReaderFactory()
        self.writer_factory: WriterFactory = writer_factory or DefaultWriterFactory()

        register_models()

        logger.info("Carbon daemon initialized")

    def run(self) -> CarbonDaemonResult:
        """
        Execute the complete daemon workflow.

        Returns:
            CarbonDaemonResult containing execution results
        """
        start_time = time.time()

        try:
            logger.info("Starting carbon daemon execution")

            vms = self._read_infrastructure_data_generic("VirtualMachine")
            if not vms:
                raise KnownException(
                    ErrorCode.DATA_FETCH_NO_RESULTS,
                    details="No virtual machines found in data source",
                )

            processed_vms = self._process_carbon_calculations_compute(vms)

            self._write_results(processed_vms)

            # Implement call to storage calculations
            storage_resources = self._read_infrastructure_data_generic("StorageResource")

            processed_storage = self._process_carbon_calculations_storage(storage_resources)

            execution_time = time.time() - start_time
            result = CarbonDaemonResult(
                success=True, vm_count=len(processed_vms), execution_time=execution_time
            )

            logger.info(
                "carbon daemon execution completed successfully. processed %d VMs in %.2f seconds",
                len(processed_vms),
                execution_time,
            )

            return result

        except KnownException as e:
            execution_time = time.time() - start_time
            error_msg = f"known error during daemon execution: {e.formatted_string}"
            logger.error(error_msg)

            return CarbonDaemonResult(
                success=False, execution_time=execution_time, error_message=error_msg
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            return CarbonDaemonResult(
                success=False, execution_time=execution_time, error_message=error_msg
            )

    def _read_infrastructure_data_generic(self, resourceName: Resource.name) -> list[Resource]:
        """
        Read infrastructure data using the configured reader.

        Returns:
            List of resources from the data source

        Raises:
            Exception: If reading fails
        """
        read_start_time = time.time()

        try:
            logger.info("starting infrastructure data reading")
            reader = self.reader_factory.create_reader(self.config, resourceName)
            resources = reader.read_files()

            read_time = time.time() - read_start_time
            logger.info(
                "infrastructure data reading completed. Retrieved %d resources of type %s in %.2f seconds",
                len(resources),
                resourceName,
                read_time,
            )

            return resources

        except Exception as e:
            logger.error("failed to read infrastructure data: %s for reader %s", str(e), resourceName)
            raise

    def _process_carbon_calculations_compute(
        self, vms: list[VirtualMachine]
    ) -> list[VirtualMachine]:
        """
        Process virtual machines through the carbon calculation engine.

        Scope:
            - cpu
            - memory
            - VM disks

        Args:
            vms: List of virtual machines to process

        Returns:
            List of virtual machines with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """
        process_start_time = time.time()

        try:
            logger.info("starting carbon calculations for %d VMs", len(vms))

            carbon_service = ioc_util.resolve(
                CarbonService, "IFVm", self.HOURLY_INTERVAL_SECONDS
            )

            if carbon_service is None:
                raise RuntimeError("failed to resolve CarbonService from IoC container")

            processed_vms: list[VirtualMachine] = carbon_service.run_engine(vms)

            process_time = time.time() - process_start_time
            logger.info("carbon calculations completed in %.2f seconds", process_time)

            return processed_vms

        except Exception as e:
            logger.error("failed to process carbon calculations: %s", str(e))
            raise

    def _process_carbon_calculations_storage(
        self, storage_resources: list[StorageResource]
    ) -> list[StorageResource]:
        """
        Process storage resources through the carbon calculation engine.

        Args:
            vms: List of storage resources to process

        Returns:
            List of storage resources with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """
        process_start_time = time.time()
        if storage_resources:
            try:
                logger.info(
                    "starting carbon calculations for %d storage resources",
                    len(storage_resources),
                )

                storage_service = ioc_util.resolve(
                    CarbonService, "IFStorage", self.DAILY_SECONDS
                )

                if storage_service is None:
                    raise RuntimeError(
                        "failed to resolve CarbonService from IoC container"
                    )

                processed_storage_resources: list[
                    StorageResource
                ] = storage_service.run_engine(storage_resources)

                process_time = time.time() - process_start_time

                total_storage_carbon = sum(
                    storage.total_carbon_emitted
                    for storage in processed_storage_resources
                )
                total_storage_energy = sum(
                    storage.total_energy_consumed
                    for storage in processed_storage_resources
                )

                logger.info(
                    "Storage processing calculations completed in %.2f seconds",
                    process_time,
                )

                logger.info(
                    "Storage processing : %d storage resources processed, "
                    "%.2f kWh total energy, %.0f gCO2 total emissions",
                    len(processed_storage_resources),
                    total_storage_energy,
                    total_storage_carbon,
                )

                return processed_storage_resources

            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.exception(
                    "File system error processing storage resources: %s", str(e)
                )
            except (csv.Error, UnicodeDecodeError, ValueError) as e:
                logger.exception(
                    "Data parsing error processing storage resources: %s", str(e)
                )
            except KnownException as e:
                logger.exception("Known error processing storage resources: %s", str(e))
            except ImportError as e:
                logger.exception(
                    "Import error processing storage resources: %s", str(e)
                )
        else:
            logger.info("No storage resources found to process")

    def _write_results(self, vms: list[VirtualMachine]) -> None:
        """
        Write processed results using the configured writer.

        Args:
            vms: List of processed virtual machines

        Raises:
            Exception: If writing fails
        """
        write_start_time = time.time()

        try:
            logger.info("starting result upload for %d VMs", len(vms))

            writer = self.writer_factory.create_writer(self.config, vms)
            writer.upload_compute_report()

            write_time = time.time() - write_start_time
            logger.info("results uploaded successfully in %.2f seconds", write_time)

        except Exception as e:
            logger.error("failed to write results: %s", str(e))
            raise


def main() -> None:
    """
    Main entry point for the carbon daemon.

    Creates and runs a CarbonDaemon instance with the global configuration.
    Exits with appropriate code based on execution result.
    """
    try:
        logger.info(CARMEN_LOGO)
        daemon = CarbonDaemon(config.carmen_daemon)
        result = daemon.run()

        if not result.success:
            logger.error("daemon execution failed: %s", result.error_message)
            exit(1)

        logger.info("daemon execution completed successfully")

    except Exception as e:
        logger.exception("critical error in daemon main: %s", str(e))
        exit(1)


if __name__ == "__main__":
    main()
