"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

import csv
import logging
import time

from backend.src.common.constants import (
    DAILY_SECONDS,
)
from backend.src.common.known_exception import KnownException
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)


class Runner_Storage(AbstractRunner):
    """
    Implementation of the Runner for the Storage Resource Type.
    """

    def __init__(self):
        self.resource_type_result: ResourceTypeResult | None

    # Resources built by the reader to be handled by the runner
    @property
    def resource_type_result(self) -> ResourceTypeResult | None:
        return self.resource_type_result

    def run(self, list_resources_to_process: list[Resource]) -> ResourceTypeResult:
        """
        Run the Impact Framework and build result for the Storage Resource Type.

        Returns:
            ResourceTypeResult containing execution results
        """

        start_time = time.time()

        try:
            logger.info("Starting Storage runner execution.")

            processed_storage_resources = self.process_carbon_calculations(
                list_resources_to_process
            )

            logger.info("Processed resources: %s", processed_storage_resources)
            execution_time = time.time() - start_time

            resourceDaemonResult = self.create_resource_type_result(
                True, execution_time, ResourceType.STORAGE, processed_storage_resources
            )

            logger.info(
                "Storage processing: %d storage resources processed, "
                "%.2f kWh total energy, %.0f gCO2 total emissions",
                len(resourceDaemonResult.list_processed_resources),
                resourceDaemonResult.total_energy_consumed,
                resourceDaemonResult.total_carbon_emitted,
            )

            return resourceDaemonResult

        except KnownException as e:
            execution_time = time.time() - start_time
            error_msg = f"known error during daemon execution: {e.formatted_string}"
            logger.error(error_msg)

            return ResourceTypeResult(
                success=False, execution_time=execution_time, error_message=error_msg
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            return ResourceTypeResult(
                success=False, execution_time=execution_time, error_message=error_msg
            )

    def process_carbon_calculations(
        self, storage_resources: list[StorageResource]
    ) -> list[StorageResource]:
        process_start_time = time.time()
        if storage_resources:
            try:
                logger.info(
                    "Starting carbon calculations for %d storage resources",
                    len(storage_resources),
                )

                ## TODO: check why we have this DAILY_SECONDS (really needed?)
                storage_service = ioc_util.resolve(
                    CarbonService, "IFStorage", DAILY_SECONDS
                )

                if storage_service is None:
                    raise RuntimeError(
                        "failed to resolve CarbonService from IoC container"
                    )

                logger.info(
                    "process carbon calculations on resources: %s", storage_resources
                )
                processed_storage_resources: list[
                    StorageResource
                ] = storage_service.run_engine(storage_resources)
                logger.info(
                    "Result process carbon calculations on resources: %s",
                    processed_storage_resources,
                )

                process_time = time.time() - process_start_time

                logger.info(
                    "Storage processing calculations completed in %.2f seconds",
                    process_time,
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
