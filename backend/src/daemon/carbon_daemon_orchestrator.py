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
import sys
from os import listdir
from os.path import isfile, join

import csv

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.common.carmen_exception import CarmenException, DataFetchError
from backend.src.common.errors import ErrorCode

from backend.src.core.yaml_config_loader import config
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.resource import Resource
from backend.src.daemon.carbon_daemon_result import (
    CarbonDaemonResult,
    ResourceTypeResult,
)

from backend.src.utils.helpers import get_execution_date

from backend.src.schemas.resource import ResourceType
from backend.src.daemon.processors.abstract_processor import (
    AbstractProcessor,
)
from backend.src.daemon.processors.processor_misc_services import (
    Processor_Misc_Services,
)
from backend.src.daemon.processors.processor_compute import Processor_Compute
from backend.src.daemon.processors.processor_storage import Processor_Storage

from backend.src.daemon.writers.abstract_writer import AbstractWriter

from backend.src.common.constants import (
    CSV_PATH,
    CSV_FILE_ENCODING,
)


logger = logging.getLogger(__name__)


def _print_cli_help() -> None:
    """Print Carbon Daemon CLI usage and supported options."""
    help_message = """Usage: python -m backend.src.daemon.carbon_daemon_orchestrator [options]

Options:
  -h, --help, -help
      Show this help message and exit.

  --carmen-config-filepath PATH
      Path to main daemon config YAML.
      Env fallback: CARMEN_CONFIG_FILEPATH
      Default: etc/config/config.yaml

  --carmen-provider-config-filepath PATH
      Path to provider config directory.
      Env fallback: CARMEN_PROVIDER_CONFIG_FILEPATH
      Default: etc/config/modelling_constants/cloud_providers

  --carmen-carbon-values-filepath PATH
      Path to carbon values YAML.
      Env fallback: CARMEN_CARBON_VALUES_FILEPATH
      Default: etc/config/modelling_constants/carbon_values.yaml

Examples:
  python -m backend.src.daemon.carbon_daemon_orchestrator --carmen-config-filepath etc/config/config.yaml
  python -m backend.src.daemon.carbon_daemon_orchestrator --carmen-provider-config-filepath etc/config/modelling_constants/cloud_providers --carmen-carbon-values-filepath etc/config/modelling_constants/carbon_values.yaml
"""
    print(help_message)


class OrchestratorContext:
    """
    Class to store variables related to this Carmen Daemon run.
    """

    # Variables set at the end of compute & storage processing.
    # These will then be used as cost model in the Misc Services process.
    # TODO Vnext: Should be set in Orchestrator context to be used only once.
    # compute_energy: float = 0.0
    # storage_energy: float = 0.0
    # compute_embodied: float = 0.0
    # storage_embodied: float = 0.0

    # compute_cost: float = 0.0
    # storage_cost: float = 0.0
    # storage_cost: float = 0.0


class CarbonDaemonOrchestrator:
    def __init__(
        self,
        daemon_config: DaemonConfig,
        list_resource_processors: list[str | AbstractProcessor] | None = None,
    ):
        """
        Initialize the carbon daemon.

        Args:
            daemon_config: Configuration for daemon operations
            list_resource_processors: List of resource processors to execute in the daemon
        """
        self.config: DaemonConfig = daemon_config

        # TODO: we should go for a collection ensuring unicity
        self.list_resource_processors: list[
            AbstractProcessor
        ] = self._resolve_resource_processors(list_resource_processors)

        self.carbon_daemon_result: CarbonDaemonResult = self.create_carbon_daemon_result(
            success=True,
            execution_time=0,
        )

        self.pre_process(self.list_resource_processors)

    def _resolve_resource_processors(
        self,
        list_resource_processors: list[str | AbstractProcessor] | None,
    ) -> list[AbstractProcessor]:
        """Resolve configured processor names into processor objects."""
        if not list_resource_processors:
            return []

        processor_factory: dict[str, type[AbstractProcessor]] = {
            "Processor_Compute": Processor_Compute,
            "Processor_Storage": Processor_Storage,
            "Processor_Misc_Services": Processor_Misc_Services,
        }

        resolved_processors: list[AbstractProcessor] = []
        for processor in list_resource_processors:
            if isinstance(processor, str):
                processor_cls = processor_factory.get(processor)
                if processor_cls is None:
                    raise CarmenException(
                        ErrorCode.CONFIG_INVALID_VALUE,
                        f"Unsupported processor configured: {processor}",
                    )
                resolved_processors.append(processor_cls(self.config))
                continue

            # Backward-compatible path for tests and callers that inject
            # mocked/custom processor objects directly.
            resolved_processors.append(processor)

        return resolved_processors

    def orchestrate_carbon_daemon(self):
        """
        Execute the complete daemon workflow.

        Returns:
            CarbonDaemonResult containing execution results
        """
        start_time = time.time()

        try:
            if self.list_resource_processors and len(self.list_resource_processors) > 0:
                logger.info("Starting Carbon Daemon execution")

                # Read infrastructure data
                self.read_data_source()

                # Run Impact Framework Engine for each Resource
                self.run_engine()

                # Write results
                self.write_report()

                total_execution_time = time.time() - start_time

                logger.info(
                    "Carbon Daemon execution completed successfully. Processed %d resource type(s) in %.2f seconds",
                    len(self.list_resource_processors),
                    total_execution_time,
                )

                logger.info(f"Result: {self.carbon_daemon_result.dict_resource_result}")
            else:
                error_msg = "Carmen Daemon not excuted, no processor found."
                logger.warning(error_msg)
                self.update_carbon_daemon_result(
                    success=False,
                    start_time=start_time,
                    list_exceptions=[CarmenException(ErrorCode.CONFIG_NO_PROCESSOR, error_msg)],
                    dict_resource_results=None,
                )

            return self.carbon_daemon_result

        except CarmenException as e:
            error_msg = f"known error during daemon execution: {e.formatted_string}"
            logger.error(error_msg)

            self.update_carbon_daemon_result(
                success=False,
                start_time=start_time,
                list_exceptions=[CarmenException(ErrorCode.UNKNOWN_ERROR, error_msg)],
                dict_resource_results=None,
            )
            return self.carbon_daemon_result

        except Exception as e:
            error_msg = f"Unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            self.update_carbon_daemon_result(
                success=False,
                start_time=start_time,
                list_exceptions=[Exception(ErrorCode.UNKNOWN_ERROR, error_msg)],
                dict_resource_results=None,
            )
            return self.carbon_daemon_result

    def pre_process(self, list_resource_processors):
        """
        Preparation steps to ensure daemon is running smoothly.

        Raises:
            Exception: 
        """
        start_time = time.time()

        try:
            if list_resource_processors:
                # Check if Misc Services processor is present in the list.
                # If yes and not in last position, re-order the list
                # TODO Vnext: protect against several misc services processor in the list, which should not be the case. 
                misc_proc = next(
                    (proc for proc in list_resource_processors if isinstance(proc, Processor_Misc_Services)),
                    None,
                )
                if misc_proc is not None:
                    if list_resource_processors[-1] is not misc_proc:
                        list_resource_processors.remove(misc_proc)
                        list_resource_processors.append(misc_proc)
                else:
                    logger.info(
                        "No processor found for Misc Services. "
                    )

                register_models()

                self.date: str = get_execution_date()
                for processor in list_resource_processors:
                    processor.execution_date = self.date
                self.list_input_file = []
                logger.debug(f"input_path: {self.config.source.input_path}")
                input_path = self.config.source.input_path
                self.list_input_file = self.load_input_files(input_path)

                logger.info(f"output_path: {self.config.output.output_path}")
                if self.config.output.output_file_name:
                    output_file_name = f"{self.config.output.output_file_name}.csv"
                else:
                    # No file name found in config, fallback to CO2_date.csv
                    output_file_name = f"CO2_{self.date}.csv"
                self.output_file: str = os.path.join(
                    str(self.config.output.output_path), output_file_name
                )

                logger.info("Carmen Daemon initialized")

        except Exception as e:
            logger.exception("Critical error in Carmen Daemon initialization: %s", str(e))
            raise

    # Load input files
    def load_input_files(self, input_path) -> list[str]:
        """
        Iterate on all files included in the input_path folder.
        Append the list of files for each found.

        Return: list of files full path.
        """
        list_files: list[str] = []
        for file in listdir(input_path):
            if isfile(join(input_path, file)) and file.endswith(".csv"):
                logger.info(f"input file found: {file}")
                list_files.append(input_path + "/" + file)

        logger.info(f"list_input_file: {list_files}")
        logger.info(f"Carmen Dameon loaded {len(list_files)} input file(s).")
        return list_files

    def read_data_source(self):
        """
        Loops over all configured processors and reads infrastructure data
        using the configured reader.

        Raises:
            Exception: If reading fails
        """
        logger.info(":::: Carbon Daemon Orchestrator :::: Start of"
                    " read_data_source process ::::")
        start_time = time.time()

        try:
            logger.info(
                "Starting data source reading loop for %d processors: %s.",
                len(self.list_resource_processors),
                self.list_resource_processors,
            )

            if self.list_resource_processors:
                all_resources_to_process: list[Resource] = []
                nb_input_files:int = 0
                for input_file in self.list_input_file:
                    # Check if file exists before trying to read it
                    try:
                        csv_data = ""
                        if os.path.exists(input_file):
                            logger.info("--------------")
                            logger.info(f"Data source reading from {input_file}")
                            logger.info("--------------")
                            with open(
                                input_file, "r", encoding=CSV_FILE_ENCODING
                            ) as file:
                                csv_data = file.read()

                        file_resources: list[Resource] = []

                        for abstract_processor in self.list_resource_processors:
                            logger.debug(f"abstract_processor: {abstract_processor}")
                            logger.info(
                                f"Data source reading by {abstract_processor.reader}"
                                f" reader for {abstract_processor.resource_type.value}"
                                f" resource type."
                            )
                            resources_from_reader = abstract_processor.read(
                                csv_data)

                            file_resources.extend(resources_from_reader)
                            logger.debug(f"file_resources: {file_resources}")

                        file_read_time = time.time() - start_time
                        if file_resources:
                            logger.info(
                                "Source data reading completed for file %s."
                                " Reader %s retrieved %d resources of type %s"
                                " in %.2f seconds",
                                input_file,
                                abstract_processor.reader,
                                len(file_resources),
                                abstract_processor.resource_type.value,
                                file_read_time,
                            )
                            all_resources_to_process.append(file_resources)
                            logger.info(f"all_resources_to_process length: {len(all_resources_to_process)}")
                            logger.debug(f"all_resources_to_process: {all_resources_to_process}")
                            nb_input_files += 1
                        else:
                            message = "No resources found for "
                            f"{abstract_processor.resource_type.value} in file"
                            f" {input_file}."
                    except FileNotFoundError:
                        message = f"File not found: {input_file}"
                        logger.error(message)
                        self.update_carbon_daemon_result(
                            success=False,
                            start_time=start_time,
                            list_exceptions=[
                                CarmenException(
                                    ErrorCode.FILE_NOT_FOUND,
                                    details=message)],
                            dict_resource_results=None,
                        )
                    except PermissionError as e:
                        message = f"Permission denied reading file {input_file}, {str(e)}"
                        logger.error(message)
                        self.update_carbon_daemon_result(
                            success=False,
                            start_time=start_time,
                            list_exceptions=[
                                CarmenException(
                                    ErrorCode.FILE_PERMISSION_DENIED,
                                    details=message,
                                )],
                            dict_resource_results=None,
                        )
                    except UnicodeDecodeError as e:
                        message = f"Failed to decode file data for {input_file}, {str(e)}"
                        logger.error(message)
                        self.update_carbon_daemon_result(
                            success=False,
                            start_time=start_time,
                            list_exceptions=[
                                CarmenException(
                                    ErrorCode.FILE_INVALID_FORMAT,
                                    details=message,
                                )],
                            dict_resource_results=None,
                        )
                    except Exception as e:
                        message = f"Unexpected error reading file {input_file}, {e.formatted_string}"
                        logger.error(message)
                        self.update_carbon_daemon_result(
                            success=False,
                            start_time=start_time,
                            list_exceptions=[CarmenException(ErrorCode.UNKNOWN_ERROR,details=message)],
                            dict_resource_results=None,
                        )

                logger.info(":::: Carbon Daemon Orchestrator :::: End of"
                            " read_data_source process ::::")
                read_time = time.time() - start_time
                if all_resources_to_process:
                    logger.info(
                        "Source data reading completed from %d valid input"
                        " file(s)."
                        " Reader(s) retrieved %d resources."
                        " in %.2f seconds",
                        nb_input_files,
                        len(all_resources_to_process),
                        read_time,
                    )
                    logger.debug(f"Resources fetched from input: {all_resources_to_process}")
                else:
                    message = "No resources found."
                    self.update_carbon_daemon_result(
                        success=False,
                        start_time=start_time,
                        list_exceptions=[
                            DataFetchError(
                                ErrorCode.DATA_FETCH_NO_RESULTS,
                                details=message,
                            )],
                        dict_resource_results=None,
                    )
            else:
                logger.error("No processor provided.")

        except Exception:
            message = "Failed to read data source"
            logger.error(message)
            self.update_carbon_daemon_result(
                success=False,
                start_time=start_time,
                list_exceptions=[CarmenException(ErrorCode.UNKNOWN_ERROR,
                                           details=message)],
                dict_resource_results=None,
            )

    def run_engine(self):
        """
        Loops over all configured processors and runs the Impact Framework
        using the configured runner.

        Raises:
            Exception: If running fails
        """
        logger.info(":::: Carbon Daemon Orchestrator :::: Start of"
                    " run_engine process ::::")
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
                        f"Running engine by {abstract_processor.runner}"
                        f" runner for {abstract_processor.resource_type.value}"
                        f" resource type."
                    )

                    logger.info(f"Length of list_resources_to_process: {len(abstract_processor.list_resources_to_process)}")

                    # Misc Services modelling is executed at the end of the process
                    if abstract_processor.resource_type == ResourceType.MISC_SERVICES:
                        self._hydrate_misc_services_resources(
                            abstract_processor.list_resources_to_process,
                            dict_resource_results,
                        )
                    logger.info(f"Length of list_resources_to_process: {len(abstract_processor.list_resources_to_process)}")

                    resource_type_result = abstract_processor.run()

                    # Populate result dictionary with Resource result
                    if resource_type_result:
                        dict_resource_results[
                            abstract_processor.resource_type
                        ] = resource_type_result

                # End of loop, store complete execution time
                logger.info(
                    f"Creating CarbonDaemonResult for dict_resource_results: {dict_resource_results}"
                )
                self.update_carbon_daemon_result(
                    success=True,
                    start_time=start_time,
                    list_exceptions=[],
                    dict_resource_results=dict_resource_results,
                )
                logger.info(":::: Carbon Daemon Orchestrator :::: End of"
                            " run_engine process ::::")
        except Exception as e:
            error_msg = f"Failed to run engine for the given processors: {str(e)}"
            logger.exception(error_msg)
            self.update_carbon_daemon_result(
                success=False,
                start_time=start_time,
                list_exceptions=[Exception(ErrorCode.UNKNOWN_ERROR, error_msg)],
                dict_resource_results=dict_resource_results,
            )
            raise

    def _hydrate_misc_services_resources(
        self,
        list_resources_to_process: list,
        dict_resource_results: dict[ResourceType, ResourceTypeResult],
    ) -> None:
        """
        Populate compute and storage fields on each MiscServicesResource before
        the misc services runner executes.

        Values are taken from the VM and Storage ResourceTypeResults already
        accumulated in ``dict_resource_results`` during the current engine loop.
        When a result is absent, configurable defaults from carbon_values.yaml
        are used instead.
        """
        vm_dict_result = dict_resource_results.get(ResourceType.VIRTUAL_MACHINE)
        storage_dict_result = dict_resource_results.get(ResourceType.STORAGE)
        misc_defaults = config.carbon_values_config.default_misc_services_constants

        for resource in list_resources_to_process:
            if vm_dict_result:
                resource.compute_cost = vm_dict_result.total_cost
                resource.compute_energy = vm_dict_result.total_energy_consumed
                resource.compute_embodied = vm_dict_result.total_carbon_embodied
            else:
                logger.warning(
                    "No compute results found for Misc Services model. "
                    "Using default values from carbon_values.yaml."
                )
                resource.compute_cost = misc_defaults.compute_cost
                resource.compute_energy = misc_defaults.compute_energy
                resource.compute_embodied = misc_defaults.compute_embodied

            if storage_dict_result:
                resource.storage_cost = storage_dict_result.total_cost
                resource.storage_energy = storage_dict_result.total_energy_consumed
                resource.storage_embodied = storage_dict_result.total_carbon_embodied
            else:
                logger.warning(
                    "No storage results found for Misc Services model. "
                    "Using default values from carbon_values.yaml."
                )
                resource.storage_cost = misc_defaults.storage_cost
                resource.storage_energy = misc_defaults.storage_energy
                resource.storage_embodied = misc_defaults.storage_embodied

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
        success,
        start_time,
        list_exceptions: list[Exception],
        dict_resource_results: dict[ResourceType, ResourceTypeResult],
    ):
        execution_time = time.time() - start_time
        logger.info(
            f"Updating CarbonDaemonResult with success={success}, execution_time={execution_time}, "
            f"list_exceptions={list_exceptions}, dict_resource_results={dict_resource_results}"
        )
        logger.info(f"Success value before update: {self.carbon_daemon_result.success}")
        self.carbon_daemon_result.success &= success
        self.carbon_daemon_result.execution_time = execution_time
        self.carbon_daemon_result.list_exceptions.extend(list_exceptions)

        if dict_resource_results:
            for resource_result in dict_resource_results.values():
                self.carbon_daemon_result.total_carbon_operational += (
                    resource_result.total_carbon_operational
                )
                self.carbon_daemon_result.total_carbon_embodied += (
                    resource_result.total_carbon_embodied
                )
                self.carbon_daemon_result.total_carbon_emitted += (
                    resource_result.total_carbon_emitted
                )
                self.carbon_daemon_result.total_energy_consumed += (
                    resource_result.total_energy_consumed
                )
            self.carbon_daemon_result.dict_resource_result = self.carbon_daemon_result.dict_resource_result | dict_resource_results

        logger.info(f"Success value after update: {self.carbon_daemon_result.success}")

    def write_report(self):
        """
        Creates a CSV report containing all resource types.
        Handles VMs, Storage, and future resource categories in one file.
        """
        logger.info(":::: Carbon Daemon Orchestrator :::: Start of"
                    " write_report process ::::")
        logger.info(
            "Starting write_results for %d resource results.",
            len(self.carbon_daemon_result.dict_resource_result),
        )
        start = time.time()

        if self.carbon_daemon_result.success:
            # Carbon daemon run was succesful, write report output file.
            logger.info("Carbon daemon run was succesful, write report output file.")
            os.makedirs(str(self.config.output.output_path), exist_ok=True)
            with open(self.output_file, "w", newline="") as report_csv_file:
                fieldnames = AbstractWriter.get_report_headers()
                dict_writer = csv.DictWriter(report_csv_file, fieldnames=fieldnames)
                dict_writer.writeheader()

                # Iterate on each Resource Carbon Daemon Processor
                if self.list_resource_processors:
                    for abstract_processor in self.list_resource_processors:
                        logger.info(
                            # f"Writing results by {abstract_processor.writer(dict_writer)}"
                            f" writer for {abstract_processor.resource_type.value}"
                            f" resource type."
                        )

                        # Call the AbstractWriter write method
                        abstract_processor.write(dict_writer)

                # # iterate on writers
                # for (
                #     resource_type_result
                # ) in self.carbon_daemon_result.dict_resource_result.values():
                #     # Instantiate writer dedicated to ResourceType
                #     if resource_type_result.resource_type == ResourceType.STORAGE:
                #         writer = Writer_Storage(self.config, self.date, dict_writer, resource_type_result)
                #         writer.write_content(resource_type_result.list_processed_resources)
                #     elif resource_type_result.resource_type == ResourceType.VIRTUAL_MACHINE:
                #         writer = Writer_Compute(self.config, self.date, dict_writer, resource_type_result)
                #         writer.write_content(resource_type_result.list_processed_resources)
                #     elif resource_type_result.resource_type == ResourceType.MISC_SERVICES:
                #         writer = Writer_Misc_Services(self.config, self.date, dict_writer, resource_type_result)
                #         writer.write_content(resource_type_result.list_processed_resources)
                #     else:
                #         logger.warning(
                #             "No writer implemented for resource type %s. Skipping writing results for this resource type.",
                #             resource_type_result.resource_type.value,
                #         )

        else:
            logger.info(
                "Carbon daemon run was not succesful, write error in output file."
            )
            # TODO: Implement error case

        elapsed_time = time.time() - start

        logger.info(":::: Carbon Daemon Orchestrator :::: End of"
                    " write_report process ::::")

        logger.info("CSV report created in %.2f seconds", elapsed_time)
        logger.info("Report saved to: %s", self.output_file)


def main() -> None:
    """
    Main entry point for the carbon daemon.

    Creates and runs a CarbonDaemonOrchestrator instance with the global configuration.
    Exits with appropriate code based on execution result.
    """
    try:
        if any(arg in {"-h", "--help", "-help"} for arg in sys.argv[1:]):
            _print_cli_help()
            return

        logger.info(CARMEN_LOGO)
        list_resource_processors = config.carmen_daemon.orchestrator.list_processors
        daemon = CarbonDaemonOrchestrator(
            daemon_config=config.carmen_daemon,
            list_resource_processors=list_resource_processors,
        )

        result = daemon.orchestrate_carbon_daemon()

        if not result.success:
            logger.error(f"Daemon execution failed: {result.list_exceptions}")
            exit(1)

        logger.info("Daemon execution completed successfully.")

    except Exception as e:
        logger.exception("Critical error in Daemon main: %s", str(e))
        exit(1)


if __name__ == "__main__":
    main()
