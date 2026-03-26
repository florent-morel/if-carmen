
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.src.daemon.writers.writer_factory import (
    DefaultWriterFactory,
    WriterFactory,
)

from backend.src.common.constants import (
    CARMEN_LOGO,
    SupportedResourcesType,
)
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.readers.reader_factory import (
    DefaultReaderFactory,
    ReaderFactory,
)
from backend.src.schemas.resource import Resource

logger = logging.getLogger(__name__)


class CarbonDaemonResult:
    """Container for daemon execution results."""

    def __init__(
        self,
        success: bool,
        list_processed_resources: list[Resource],
        total_energy_consumed: float,
        total_carbon_operational: float,
        total_carbon_embodied: float,
        total_carbon_emitted: float,
        execution_time: float = 0.0,
        error_message: str = "",
    ):
        self.success: bool = success
        self.list_processed_resources: list = list_processed_resources
        self.total_energy_consumed: float = total_energy_consumed
        self.total_carbon_operational: float = total_carbon_operational
        self.total_carbon_embodied: float = total_carbon_embodied
        self.total_carbon_emitted: float = total_carbon_emitted
        self.execution_time: float = execution_time
        self.error_message: str = error_message


class AbstractCarbonDaemon(ABC):

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

    @abstractmethod
    def run(self) -> CarbonDaemonResult:
        """
        Execute the complete daemon workflow.

        Returns:
            CarbonDaemonResult containing execution results
        """

    @abstractmethod
    def process_carbon_calculations(
        self, resources: list[Resource]
    ) -> CarbonDaemonResult:
        """
        Process resources through the carbon calculation engine.

        Args:
            resources: List of resources to process

        Returns:
            Calculation result with list of resources with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """

    def create_CarbonDaemonResult(self, success,
                                  execution_time,
                                  processed_resources: list[Resource]
                                  ) -> CarbonDaemonResult:
        """
        Create a CarbonDaemonResult from the list of processed resources.

        Args:
            success: whether the call to the IF has been successful.
            execution_time: time to execute the call.
            processed_resources: List of processed resources.

        Returns:
            CarbonDaemonResult
        """
        total_carbon_operational = sum(
            resource.total_carbon_operational
            for resource in processed_resources
        )

        total_carbon_embodied = sum(
            resource.total_carbon_embodied
            for resource in processed_resources
        )

        total_carbon_emitted = sum(
            resource.total_carbon_emitted
            for resource in processed_resources
        )
        total_energy_consumed = sum(
            resource.total_energy_consumed
            for resource in processed_resources
        )
        result = CarbonDaemonResult(
            success=True, 
            list_processed_resources=processed_resources,
            total_energy_consumed=total_energy_consumed,
            total_carbon_operational=total_carbon_operational,
            total_carbon_embodied=total_carbon_embodied,
            total_carbon_emitted=total_carbon_emitted,
            execution_time=execution_time
        )

        return result

    def write_results(self, resources: list[Resource]) -> None:
        """
        Write processed results using the configured writer.

        Args:
            resources: List of processed resources

        Raises:
            Exception: If writing fails
        """
        write_start_time = time.time()

        try:
            logger.info("starting result upload for %d VMs", len(resources))

            writer = self.writer_factory.create_writer(self.config, resources)
            writer.upload_compute_report()

            write_time = time.time() - write_start_time
            logger.info("results uploaded successfully in %.2f seconds", write_time)

        except Exception as e:
            logger.error("failed to write results: %s", str(e))
            raise

    def read_infrastructure_data(self, supportedResourcesType: SupportedResourcesType) -> list[Resource]:
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
            reader = self.reader_factory.create_reader(self.config, supportedResourcesType)
            resources = reader.read_files()

            read_time = time.time() - read_start_time
            logger.info(
                "infrastructure data reading completed. Retrieved %d resources of type %s in %.2f seconds",
                len(resources),
                SupportedResourcesType.value,
                read_time,
            )

            return resources

        except Exception as e:
            logger.error("failed to read infrastructure data: %s for reader %s"
                         , str(e), supportedResourcesType.value)
            raise


def main() -> None:
    """
    Main entry point for the carbon daemon.

    Creates and runs a CarbonDaemon instance with the global configuration.
    Exits with appropriate code based on execution result.
    """
    try:
        logger.info(CARMEN_LOGO)
        daemon = AbstractCarbonDaemon(config.carmen_daemon)
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
