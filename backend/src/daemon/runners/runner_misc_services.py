
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
from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
from backend.src.utils import ioc_util
from backend.src.common.errors import ErrorCode

logger = logging.getLogger(__name__)


class Runner_Misc_Services(AbstractRunner):
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
            logger.info("Starting Misc services runner execution.")

            processed_resources = self.process_carbon_calculations(
                list_resources_to_process
            )

            logger.info("Processed resources: %s", processed_resources)
            execution_time = time.time() - start_time

            resourceDaemonResult = self.create_resource_type_result(
                True, execution_time, ResourceType.MISC_SERVICES, processed_resources, []
            )

            logger.info(
                "Misc services processing: %d misc services resources processed, "
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
                success=False, resource_type=ResourceType.MISC_SERVICES,
                list_exceptions=[KnownException(ErrorCode.UNKNOWN_ERROR), error_msg],
                execution_time=execution_time, error_message=error_msg
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            return ResourceTypeResult(
                success=False, resource_type=ResourceType.MISC_SERVICES,
                list_exceptions=[KnownException(ErrorCode.UNKNOWN_ERROR), error_msg],
                execution_time=execution_time, error_message=error_msg
            )
