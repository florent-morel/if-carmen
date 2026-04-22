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
import csv
import file

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.common.known_exception import KnownException, DataFetchError
from backend.src.common.errors import ErrorCode
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.carbon_daemon_result import (
    CarbonDaemonResult,
    ResourceTypeResult,
)

# from backend.src.daemon.readers.abstract_reader import (
#    Reader_Compute,
#    Reader_Storage,
# )
# from backend.src.daemon.writers.abstract_writer import (
#    ComputeWriter,
# )
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)

from backend.src.daemon.uploaders.abstract_uploader import AbstractUploader
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.daemon.writers.writer_storage import Writer_Storage
from backend.src.daemon.writers.writer_compute import Writer_Compute
from backend.src.daemon.uploaders.uploader_local import Uploader_Local


logger = logging.getLogger(__name__)


class CarbonDaemonOrchestrator:
    def __init__(
        self,
        daemon_config: DaemonConfig,
        list_resource_processors: list[AbstractProcessor] | None = None,
    ):
        """
        Initialize the carbon daemon.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """
        self.config: DaemonConfig = daemon_config

        self.list_resource_processors: list[
            AbstractProcessor
        ] = list_resource_processors
        self.carbon_daemon_result: CarbonDaemonResult = None

        register_models()

        self.output_file: file

        logger.info("Carbon Daemon initialized")

    def orchestrate_carbon_daemon(self):
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
                "Carbon Daemon execution completed successfully. Processed %d resource typs in %.2f seconds",
                len(self.list_resource_processors),
                total_execution_time,
            )

            return self.carbon_daemon_result

        except KnownException as e:
            execution_time = time.time() - start_time
            error_msg = f"known error during daemon execution: {e.formatted_string}"
            logger.error(error_msg)

            return CarbonDaemonResult(
                success=False,
                dict_resource_result={},
                total_energy_consumed=0.0,
                total_carbon_operational=0.0,
                total_carbon_embodied=0.0,
                total_carbon_emitted=0.0,
                execution_time=execution_time,
                error_message=error_msg,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            return CarbonDaemonResult(
                success=False,
                dict_resource_result={},
                total_energy_consumed=0.0,
                total_carbon_operational=0.0,
                total_carbon_embodied=0.0,
                total_carbon_emitted=0.0,
                execution_time=execution_time,
                error_message=error_msg,
            )

    def read_data_source(self):
        """
        Loops over all configured processors and reads infrastructure data
        using the configured reader.

        Raises:
            Exception: If reading fails
        """
        read_start_time = time.time()

        try:
            logger.info(
                "Starting data source reading loop for %d processors: %s.",
                len(self.list_resource_processors),
                self.list_resource_processors,
            )

            if self.list_resource_processors:
                for abstract_processor in self.list_resource_processors:
                    logger.info(
                        f"Data source reading by {abstract_processor.reader}"
                        f" reader for {abstract_processor.resource_type.value}"
                        f" resource type."
                    )
                    resources = abstract_processor.read()

                read_time = time.time() - read_start_time
                if resources:
                    logger.info(
                        "Source data reading completed. Reader %s retrieved %d resources of type %s in %.2f seconds",
                        abstract_processor.reader,
                        len(resources),
                        abstract_processor.resource_type.value,
                        read_time,
                    )
                else:
                    raise DataFetchError(
                        ErrorCode.DATA_FETCH_NO_RESULTS,
                        details=f"No resources found for {abstract_processor.resource_type.value} in data source",
                    )
            else:
                logger.error("No processor provided.")

        except Exception:
            logger.error("Failed to read data source")
            raise

    def run_engine(self):
        """
        Loops over all configured processors and runs the Impact Framework
        using the configured runner.

        Raises:
            Exception: If running fails
        """
        start_time = time.time()
        dict_resource_results: dict[ResourceType, ResourceTypeResult] = {}
        try:
            logger.info(
                "Starting run_engine loop on %d processors.",
                len(self.list_resource_processors),
            )

            # Iterate on each Resource Carbon Daemon Processor
            if self.list_resource_processors:
                for abstract_processor in self.list_resource_processors:
                    logger.info(
                        f"Running engin by {abstract_processor.runner}"
                        f" runner for {abstract_processor.resource_type.value}"
                        f" resource type."
                    )
                    resource_type_result = abstract_processor.run()

                    # Populate result dictionary with Resource result
                    if resource_type_result:
                        dict_resource_results[
                            abstract_processor.resource_type
                        ] = resource_type_result

                # End of loop, store complete execution time
                execution_time = time.time() - start_time
                logger.info(
                    f"Creating CarbonDaemonResult for dict_resource_results: {dict_resource_results}"
                )
                self.carbon_daemon_result = self.create_carbon_daemon_result(
                    success=True,
                    execution_time=execution_time,
                    dict_resource_results=dict_resource_results,
                )
        except Exception:
            logger.error("Failed to run engine for the given processors.")
            execution_time = time.time() - start_time
            self.carbon_daemon_result = self.create_carbon_daemon_result(
                success=False,
                execution_time=execution_time,
                dict_resource_results=dict_resource_results,
            )
            raise

    def create_carbon_daemon_result(
        self,
        success,
        execution_time,
        dict_resource_results: dict[ResourceType, ResourceTypeResult],
    ) -> CarbonDaemonResult:
        """
        Create a CarbonDaemonResult from the list of resource type results.

        Args:
            success: whether the call to the IF has been successful.
            execution_time: time to execute the call.
            dict_resource_results: List of resource type results.

        Returns:
            CarbonDaemonResult
        """

        carbon_daemon_result = CarbonDaemonResult(
            success=success,
            dict_resource_result=dict_resource_results,
            total_energy_consumed=0,
            total_carbon_operational=0,
            total_carbon_embodied=0,
            total_carbon_emitted=0,
            execution_time=execution_time,
        )

        for resource_result in dict_resource_results.values():
            carbon_daemon_result.total_carbon_operational += (
                resource_result.total_carbon_operational
            )
            carbon_daemon_result.total_carbon_embodied += (
                resource_result.total_carbon_embodied
            )
            carbon_daemon_result.total_carbon_emitted += (
                resource_result.total_carbon_emitted
            )
            carbon_daemon_result.total_energy_consumed += (
                resource_result.total_energy_consumed
            )

        return carbon_daemon_result

    def write_results(self):
        """
        Creates a CSV report containing all resource types.
        Handles VMs, Storage, and future resource categories in one file.
        """
        logger.info(
            "Starting write_results for %d resource results.",
            len(self.carbon_daemon_result.dict_resource_result),
        )
        start = time.time()

        if self.carbon_daemon_result.success:
            # Carbon daemon run was succesful, write report output file.
            logger.info("Carbon daemon run was succesful, write report output file.")
            # init csv writer
            with open(self.out_file, "w", newline="") as report_csv_file:
                fieldnames = AbstractWriter.get_report_headers()
                self.writer = csv.DictWriter(report_csv_file, fieldnames=fieldnames)

            # iterate on writers
            for resource_type_result in self.carbon_daemon_result.dict_resource_result.values():
                # TODO: need to go via the factory
                # Instantiate writer dedicated to ResourceType
                if resource_type_result.resource_type == ResourceType.STORAGE:
                    writer = Writer_Storage(report_csv_file)
                    writer.write_content()
                elif resource_type_result.resource_type == ResourceType.VIRTUAL_MACHINE:
                    writer = Writer_Compute(report_csv_file)
                    writer.write_content()

            self.output_file = report_csv_file

        else:
            # Carbon daemon run was not succesful, write error in output file.
            logger.info(
                "Carbon daemon run was not succesful, write error in output file."
            )
            # TODO: Implement error case

        elapsed_time = time.time() - start

        #       #   logging.info("Total carbon emitted: %.2f kg CO2", vm_carbon)
        #       #   logging.info("Total energy consumed: %.2f kWh", vm_energy)
        logger.info("CSV report created in %.2f seconds", elapsed_time)

        logger.info("Report saved to: %s", self.output_file)

    def upload_compute_report(self) -> None:
        """
        Call the configured uploader to push the CO2 report to the proper
        location.

        Args:

        Raises:
            Exception: If upload fails.
        """

        logger.info("Starting upload_report.")

        upload_start_time = time.time()
        #
        try:
            # TODO: Fetch upload type from config.yaml
            upload_type = "local"
            if upload_type == "local":
                # Local implementation: move file to configured path
                uploader = Uploader_Local()
                uploader.upload_report()

            upload_time = time.time() - upload_start_time
            logger.info("results uploaded successfully in %.2f seconds", upload_time)

        except Exception as e:
            logger.error("failed to upload results: %s", str(e))
            raise


def main() -> None:
    """
    Main entry point for the carbon daemon.

    Creates and runs a CarbonDaemon instance with the global configuration.
    Exits with appropriate code based on execution result.
    """
    try:
        logger.info(CARMEN_LOGO)
        # list_resource_processors = [CarbonDaemonVMProcessor(AZURE), StorageProcessor]
        daemon = CarbonDaemonOrchestrator(
            list_resource_processors=list_resource_processors
        )
        # AbstractCarbonDaemon(config.carmen_daemon)

        result = daemon.orchestrate_carbon_daemon()

        if not result.success:
            logger.error("Daemon execution failed: %s", result.error_message)
            exit(1)

        logger.info("Daemon execution completed successfully.")

    except Exception as e:
        logger.exception("Critical error in Daemon main: %s", str(e))
        exit(1)


if __name__ == "__main__":
    main()
