"""
The Carbon Daemon Orchestrator is the main class taking care of the Carbon Daemon
process.
It iterates over the different resource related processors and orchestrates the 
following actions:
- Read input data.
- Run the call to the Impact Framework.
- Write output report.
- Upload report file.

"""

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
    CarbonDaemonResult,
    ResourceDaemonResult,
)

# from backend.src.daemon.readers.abstract_reader import (
#    ReaderCompute,
#    ReaderStorage,
# )
# from backend.src.daemon.writers.abstract_writer import (
#    ComputeWriter,
# )
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.processors.abstract_processor import (
    AbstractCarbonDaemonProcessor,
)

logger = logging.getLogger(__name__)


class CarbonDaemonOrchestrator:
    def __init__(
        self,
        daemon_config: DaemonConfig,
        list_carbon_daemon_resource_processors: list[AbstractCarbonDaemonProcessor]
        | None = None,
    ):
        """
        Initialize the carbon daemon.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """
        self.config: DaemonConfig = daemon_config

        self.list_carbon_daemon_resource_processors: list[
            AbstractCarbonDaemonProcessor
        ] = list_carbon_daemon_resource_processors
        self.carbon_daemon_result: CarbonDaemonResult = None

        register_models()

        logger.info("Carbon Daemon initialized")

    def run_carbon_daemon(self):
        """
        Execute the complete daemon workflow.

        Returns:
            CarbonDaemonResult containing execution results
        """
        start_time = time.time()

        try:
            logger.info("Starting Carbon Daemon execution")

            # Read infrastructure data
            self.read_data_source()

            # Run IF Engine for each Resource
            self.run_engine()

            # Write results
            self.write_results()

            # Upload report file
            # TODO: rename to have harmonized name
            self.upload_compute_report()

            total_execution_time = time.time() - start_time

            logger.info(
                "Carbon Daemon execution completed successfully. processed %d resources in %.2f seconds",
                len(self.carbon_daemon_result.list_processed_resources),
                total_execution_time,
            )

            return self.carbon_daemon_result

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

    def read_data_source(self):
        """
        Read infrastructure data using the configured reader.

        Returns:
            List of resources from the data source

        Raises:
            Exception: If reading fails
        """
        read_start_time = time.time()

        try:
            logger.info("Starting data source reading")

            if self.list_carbon_daemon_resource_processors:

                for (
                    carbon_daemon_resource_processor
                ) in self.list_carbon_daemon_resource_processors:
                    logger.info(f"Data source reading by {carbon_daemon_resource_processor.resource_type.value} processor.")
                    carbon_daemon_resource_processor.reader.read()

                read_time = time.time() - read_start_time
                logger.info(
                    "Source data reading completed. Retrieved %d resources of type %s in %.2f seconds",
                    # len(resources),
                    ResourceType,
                    read_time,
                )
            else:
                logger.error("No processor provided.")

        except Exception:
            logger.error("Failed to read data source")
            raise

    def run_engine(self):
        start_time = time.time()

        dict_resource_daemon_result = dict[ResourceType, ResourceDaemonResult]
        # Iterate on each Resource Carbon Daemon Processor
        for (
            carbon_daemon_resource_processor
        ) in self.list_carbon_daemon_resource_processors:
            resource_daemon_result = carbon_daemon_resource_processor.run()

            # Populate Daemon Carbon Result with Resource result
            dict_resource_daemon_result[
                carbon_daemon_resource_processor.resourceType, resource_daemon_result
            ]

        # End of loop, store complete execution time
        execution_time = time.time() - start_time
        self.carbon_daemon_result = self.create_carbon_daemon_result(
            success=True,
            execution_time=execution_time,
            dict_resource_results=dict_resource_daemon_result,
        )

    def create_carbon_daemon_result(
        self,
        success,
        execution_time,
        dict_resource_results: dict[ResourceType, ResourceDaemonResult],
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
        total_carbon_operational = 0
        total_carbon_embodied = 0
        total_carbon_emitted = 0
        total_energy_consumed = 0

        for resource_result in dict_resource_results.values():
            total_carbon_operational += resource_result.total_carbon_operational
            total_carbon_embodied += resource_result.total_carbon_embodied
            total_carbon_emitted += resource_result.total_carbon_emitted
            total_energy_consumed += resource_result.total_energy_consumed

        result = CarbonDaemonResult(
            success=success,
            dict_processed_resources=dict_resource_results,
            total_energy_consumed=total_energy_consumed,
            total_carbon_operational=total_carbon_operational,
            total_carbon_embodied=total_carbon_embodied,
            total_carbon_emitted=total_carbon_emitted,
            execution_time=execution_time,
        )

        return result

    def write_results(
        self,
    ):
        """
        Creates a CSV report containing all resource types.
        Handles VMs, Storage, and future resource categories in one file.
        """
        # logger.info(
        #     "Creating CSV report with %d resources",
        #     len(resources),
        # )
        # start = time.time()

        # with open(self.out_file, mode="w", newline="", encoding="utf-8") as report:
        #     writer_orchestrator = csv.writer(report)

        #     list_row_headers = list[str]
        #     list_content = list[str]

        #     # Data from CarbonDaemonResult: total_operational_carbon, etc
        #     # Total from calcultation.from CarbonDaemonResult
        #     # global_results_writer.write()

        #     # Columns for each source
        #     # source_related_writer.write()

        # # TODO: Implement loop on all active resource runners
        #     for writer in list_active_writers:
        #         # call each storage writer to get rows
        #         list_row_headers.append(writer.build_rows_headers())
        #         list_content.append(writer.build_content())

        #     # Write Row headers and content
        #     writer_orchestrator.writerows(list_row_headers)

        #     # Concatenate content for each source
        #     for row in self.build_content():
        #         writer_orchestrator.writerow(row)

        # elapsed_time = time.time() - start

    #       #   logging.info("Total carbon emitted: %.2f kg CO2", vm_carbon)
    #       #   logging.info("Total energy consumed: %.2f kWh", vm_energy)
    # logger.info("CSV report created in %.2f seconds", elapsed_time)
    # logger.info(
    #     "  Resources: %d resources",
    #     len(resources),
    # )
    # logger.info("Report saved to: %s", self.out_file)

    def write_result_report(self) -> None:
        """
        Write processed results using the configured writer.

        Args:
            resources: List of processed resources

        Raises:
            Exception: If writing fails
        """

    #         write_start_time = time.time()
    #
    #         try:
    #             logger.info("starting result upload for %d resources",
    #                         len(carbonDaemonResult.dict_resource_daemon_result.values()))
    #
    #             writer = self.writer_factory.create_writer(self.config, carbonDaemonResult)
    #
    #             self.writer_factory.create_CO2_report()
    #
    #             # TODO: Create an uploader to upload report
    #             writer.upload_compute_report()
    #
    #             write_time = time.time() - write_start_time
    #             logger.info("results uploaded successfully in %.2f seconds", write_time)
    #
    #         except Exception as e:
    #             logger.error("failed to write results: %s", str(e))
    #             raise

    def upload_compute_report(self) -> None:
        pass


def main() -> None:
    """
    Main entry point for the carbon daemon.

    Creates and runs a CarbonDaemon instance with the global configuration.
    Exits with appropriate code based on execution result.
    """
    try:
        logger.info(CARMEN_LOGO)
        # list_carbon_daemon_resource_processors = [CarbonDaemonVMProcessor(AZURE), StorageProcessor]
        daemon = CarbonDaemonOrchestrator(
            list_carbon_daemon_resource_processors=list_carbon_daemon_resource_processors
        )
        # AbstractCarbonDaemon(config.carmen_daemon)

        result = daemon.run_carbon_daemon()

        if not result.success:
            logger.error("Daemon execution failed: %s", result.error_message)
            exit(1)

        logger.info("Daemon execution completed successfully.")

    except Exception as e:
        logger.exception("Critical error in Daemon main: %s", str(e))
        exit(1)


if __name__ == "__main__":
    main()
