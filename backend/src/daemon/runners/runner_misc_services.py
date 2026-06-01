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
    HOURLY_INTERVAL_SECONDS,
)
from backend.src.common.carmen_exception import CarmenException, DataFetchError
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
from backend.src.utils import ioc_util
from backend.src.common.errors import ErrorCode
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.daemon.carbon_daemon_result import (
    CarbonDaemonResult,
    ResourceTypeResult,
)

logger = logging.getLogger(__name__)


class Runner_Misc_Services(AbstractRunner):
    """
    Implementation of the Runner for the Storage Resource Type.
    """

    def should_run(self, list_resources_to_process: list[Resource]) -> bool:

        should_run = True
        if not list_resources_to_process:
            should_run = False
            raise DataFetchError(
                ErrorCode.DATA_FETCH_NO_RESULTS,
                details="No Misc services resource found in data source",
            )

        return should_run

    def run(self, list_resources_to_process: list[Resource]) -> ResourceTypeResult:
        """
        Run the Impact Framework and build result for the Storage Resource Type.

        Returns:
            ResourceTypeResult containing execution results
        """

        start_time = time.time()
        resource_type_result = None

        try:
            logger.info("Starting Misc services runner execution.")

            if self.should_run(list_resources_to_process):
                processed_resources = self.process_carbon_calculations(
                    list_resources_to_process
                )

                logger.info("Processed resources: %s", processed_resources)
                execution_time = time.time() - start_time

                resource_type_result = self.create_resource_type_result(
                    True,
                    execution_time,
                    ResourceType.MISC_SERVICES,
                    processed_resources,
                    [],
                )

                logger.info(
                    "Misc services processing: %d misc services resources processed, "
                    "%.2f kWh total energy, %.0f gCO2 total emissions",
                    len(resource_type_result.list_processed_resources),
                    resource_type_result.total_energy_consumed,
                    resource_type_result.total_carbon_emitted,
                )

            return resource_type_result

        except CarmenException as e:
            execution_time = time.time() - start_time
            error_msg = f"known error during daemon execution: {e.formatted_string}"
            logger.error(error_msg)

            return ResourceTypeResult(
                success=False,
                resource_type=ResourceType.MISC_SERVICES,
                list_exceptions=[CarmenException(ErrorCode.UNKNOWN_ERROR), error_msg],
                execution_time=execution_time,
                error_message=error_msg,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error during runner {ResourceType.MISC_SERVICES} execution: {str(e)}"
            logger.exception(error_msg)

            return ResourceTypeResult(
                success=False,
                resource_type=ResourceType.MISC_SERVICES,
                list_exceptions=[CarmenException(ErrorCode.UNKNOWN_ERROR), error_msg],
                execution_time=execution_time,
                error_message=error_msg,
            )

    def process_carbon_calculations(
        self, list_resources_to_process: list[Resource]
    ) -> list[Resource]:
        """
        Process Misc Resources through the carbon calculation engine.

        Scope:
            - Misc services (e.g., Azure Active Directory, Azure Key Vault, etc.)

        Args:
            misc_services: List of miscellaneous services to process

        Returns:
            List of miscellaneous services with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """
        process_start_time = time.time()

        try:
            logger.info(
                "starting carbon calculations for %d miscellaneous services",
                len(list_resources_to_process),
            )

            # TODO: duration should not be hardcoded
            # => design decision needed on how to handle
            # env variable? input file parameter?
            carbon_service = ioc_util.resolve(
                CarbonService, "IFMiscServices", DAILY_SECONDS
            )

            if carbon_service is None:
                raise RuntimeError("failed to resolve CarbonService from IoC container")

            processed_misc_services: list[Resource] = carbon_service.run_engine(
                list_resources_to_process
            )

            process_time = time.time() - process_start_time

            logger.info("carbon calculations completed in %.2f seconds", process_time)

            return processed_misc_services

        except Exception as e:
            logger.error("failed to process carbon calculations: %s", str(e))
            raise
