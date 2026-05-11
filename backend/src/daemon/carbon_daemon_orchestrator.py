"""
The Carbon Daemon Orchestrator is the main class taking care of the Carbon Daemon
process.
It iterates over the different resource related processors and orchestrates the 
following actions:
- Read input data.
- Run the call to the Impact Framework.
- Write output report.

"""

from __future__ import annotations

import logging
import time
import os
import csv
from datetime import datetime, timedelta

from backend.src.common.constants import (
    CARMEN_LOGO,
    DATE_FORMAT,
    EXECUTION_DATE,
)
from backend.src.common.known_exception import KnownException, DataFetchError
from backend.src.common.errors import ErrorCode

from backend.src.core.yaml_config_loader import config
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.carbon_daemon_result import (
    CarbonDaemonResult,
    ResourceTypeResult,
)

from backend.src.schemas.resource import ResourceType
from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.daemon.writers.writer_storage import Writer_Storage
from backend.src.daemon.writers.writer_compute import Writer_Compute

from backend.src.common.constants import (
    CSV_PATH,
    CSV_FILE_TEST,
    CSV_FILE_ENCODING,
)


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
        self.carbon_daemon_result: CarbonDaemonResult = CarbonDaemonResult(
                    success=True,
                    dict_resource_result={},
                    list_exceptions=[],
                    total_energy_consumed=0.0,
                    total_carbon_operational=0.0,
                    total_carbon_embodied=0.0,
                    total_carbon_emitted=0.0,
                    execution_time=0,
                )
        self.carbon_daemon_result = self.create_carbon_daemon_result(
            success=True,
            execution_time=0,
        )

        register_models()

        self.date: str = self.get_execution_date()
        # TODO: Implement support for list
        self.list_input_file = []
        # TODO: read from config file
        self.list_input_file.append(os.getenv(CSV_PATH, CSV_FILE_TEST))

        self.output_file: str = os.path.join(
            str(self.config.output.output_path), f"CO2_{self.date}.csv"
        )

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
            self.write_report()

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

            self.update_carbon_daemon_result(
                self.carbon_daemon_result,
                success=False,
                execution_time=execution_time,
                list_exceptions=[KnownException(ErrorCode.UNKNOWN_ERROR, error_msg)],
                dict_resource_results=None,
            )
            return self.carbon_daemon_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            self.update_carbon_daemon_result(
                self.carbon_daemon_result,
                success=False,
                execution_time=execution_time,
                list_exceptions=[Exception(ErrorCode.UNKNOWN_ERROR, error_msg)],
                dict_resource_results=None,
            )
            return self.carbon_daemon_result

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
                for input_file in self.list_input_file:
                    # Check if file exists before trying to read it
                    try:
                        if os.path.exists(input_file):
                            with open(
                                input_file, "r", encoding=CSV_FILE_ENCODING
                            ) as file:
                                logger.info(f"Data source reading from {input_file}")
                                csv_data = file.read()

                        for abstract_processor in self.list_resource_processors:
                            logger.info(
                                f"Data source reading by {abstract_processor.reader}"
                                f" reader for {abstract_processor.resource_type.value}"
                                f" resource type."
                            )
                            resources = abstract_processor.read(csv_data)

                        read_time = time.time() - read_start_time
                        if resources:
                            logger.info(
                                "Source data reading completed for file %s."
                                "Reader %s retrieved %d resources of type %s"
                                "in %.2f seconds",
                                input_file,
                                abstract_processor.reader,
                                len(resources),
                                abstract_processor.resource_type.value,
                                read_time,
                            )
                        else:
                            self.carbon_daemon_result.list_exceptions.append(
                                DataFetchError(
                                    ErrorCode.DATA_FETCH_NO_RESULTS,
                                    details="No resources found for"
                                    f"{abstract_processor.resource_type.value}"
                                    "in data source"
                                )
                            )
                    except FileNotFoundError:
                        logger.error("file not found %s", input_file)
                        self.carbon_daemon_result.list_exceptions.append(
                            KnownException(
                                ErrorCode.FILE_NOT_FOUND,
                                details=f"file not found: {input_file}"
                            )
                        )
                    except PermissionError as e:
                        logger.error(
                            "permission denied reading file %s %s", input_file, str(e)
                        )
                        self.carbon_daemon_result.list_exceptions.append(
                            KnownException(
                                ErrorCode.FILE_PERMISSION_DENIED,
                                details=f"permission denied: {input_file}"
                            )
                        )
                    except UnicodeDecodeError as e:
                        logger.error(
                            "failed to decode file data for %s %s", input_file, str(e)
                        )
                        self.carbon_daemon_result.list_exceptions.append(
                            KnownException(
                                ErrorCode.FILE_INVALID_FORMAT,
                                details=f"failed to decode file: {input_file} {str(e)}"
                            )
                        )
                    except Exception as e:
                        logger.error(
                            "unexpected error reading file %s %s", input_file, str(e)
                        )
                        self.carbon_daemon_result.list_exceptions.append(
                            Exception(ErrorCode.UNKNOWN_ERROR)
                        )
            else:
                logger.error("No processor provided.")

        except Exception:
            logger.error("Failed to read data source")
            self.carbon_daemon_result.list_exceptions.append(
                Exception(ErrorCode.UNKNOWN_ERROR)
            )

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
                self.update_carbon_daemon_result(
                    self.carbon_daemon_result,
                    success=True,
                    execution_time=execution_time,
                    list_exceptions=[],
                    dict_resource_results=dict_resource_results,
                )
        except Exception:
            logger.error("Failed to run engine for the given processors.")
            execution_time = time.time() - start_time
            self.update_carbon_daemon_result(
                self.carbon_daemon_result,
                success=False,
                execution_time=execution_time,
                list_exceptions=[Exception(ErrorCode.UNKNOWN_ERROR)],
                dict_resource_results=dict_resource_results,
            )
            raise

    def create_carbon_daemon_result(
        self,
        success,
        execution_time,
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
            dict_resource_result={},
            list_exceptions=[],
            total_energy_consumed=0,
            total_carbon_operational=0,
            total_carbon_embodied=0,
            total_carbon_emitted=0,
            execution_time=execution_time,
        )

        return carbon_daemon_result

    def update_carbon_daemon_result(
        self,
        carbon_daemon_result,
        success,
        execution_time,
        list_exceptions: list[Exception],
        dict_resource_results: dict[ResourceType, ResourceTypeResult],
    ):
        carbon_daemon_result.success = success
        carbon_daemon_result.execution_time = execution_time
        carbon_daemon_result.list_exceptions.extend(list_exceptions)

        if dict_resource_results:
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


    def write_report(self):
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
            with open(self.output_file, "w", newline="") as report_csv_file:
                fieldnames = AbstractWriter.get_report_headers()
                writer = csv.DictWriter(report_csv_file, fieldnames=fieldnames)

            # iterate on writers
            for (
                resource_type_result
            ) in self.carbon_daemon_result.dict_resource_result.values():
                # TODO: need to go via the factory
                # Instantiate writer dedicated to ResourceType
                if resource_type_result.resource_type == ResourceType.STORAGE:
                    writer = Writer_Storage(writer)
                    writer.write_content()
                elif resource_type_result.resource_type == ResourceType.VIRTUAL_MACHINE:
                    writer = Writer_Compute(writer)
                    writer.write_content()

            self.output_file = report_csv_file

        else:
            # Carbon daemon run was not succesful, write error in output file.
            logger.info(
                "Carbon daemon run was not succesful, write error in output file."
            )
            # TODO: Implement error case

        elapsed_time = time.time() - start

        logger.info("CSV report created in %.2f seconds", elapsed_time)
        logger.info("Report saved to: %s", self.output_file)

    def get_execution_date(self):
        execution_date_str = os.getenv(EXECUTION_DATE)
        if not execution_date_str:
            execution_date_str = (datetime.now() - timedelta(days=2)).strftime(
                DATE_FORMAT
            )
        try:
            execution_date = datetime.strptime(execution_date_str, DATE_FORMAT)
        except ValueError as err:
            logger.error(
                "Invalid date format for EXECUTION_DATE: '%s'", execution_date_str
            )
            raise KnownException(
                ErrorCode.VALIDATION_INVALID_DATE_FORMAT,
                details="Failed to parse execution date",
            ) from err
        logger.info(
            "Carbon daemon starting execution for date: %s",
            execution_date.strftime(DATE_FORMAT),
        )
        return execution_date_str


def main() -> None:
    """
    Main entry point for the carbon daemon.

    Creates and runs a CarbonDaemon instance with the global configuration.
    Exits with appropriate code based on execution result.
    """
    try:
        logger.info(CARMEN_LOGO)
        list_resource_processors = config.carmen_daemon.orchestrator.list_processors
        daemon = CarbonDaemonOrchestrator(
            daemon_config=config, list_resource_processors=list_resource_processors
        )

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
