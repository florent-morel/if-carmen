
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
from backend.src.daemon.abstract_carbon_daemon import (
    AbstractCarbonDaemon,
    CarbonDaemonResult,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)


class CarbonDaemonStorage(AbstractCarbonDaemon):
    """
    Main daemon class responsible for orchestrating carbon emission calculations.

    This class coordinates reading infrastructure data, processing it through
    the carbon engine, and writing the results to the specified destination.
    """

    def run(self) -> CarbonDaemonResult:
        """
        Execute the complete daemon workflow.

        Returns:
            CarbonDaemonResult containing execution results
        """
        start_time = time.time()

        try:
            logger.info("Starting carbon daemon execution")

            # Implement call to storage calculations
            storage_resources = self.read_infrastructure_data_generic("StorageResource")

            carbonDaemonResult = self.process_carbon_calculations(storage_resources)

            self.write_results(carbonDaemonResult.list_processed_resources)

            execution_time = time.time() - start_time
            carbonDaemonResult.execution_time = execution_time

            logger.info(
                "carbon daemon execution completed successfully. processed %d storage resources in %.2f seconds",
                len(carbonDaemonResult.list_processed_resources),
                execution_time,
            )

            return carbonDaemonResult

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

    def process_carbon_calculations(
        self, storage_resources: list[StorageResource]
    ) -> CarbonDaemonResult:
        process_start_time = time.time()
        if storage_resources:
            try:
                logger.info(
                    "starting carbon calculations for %d storage resources",
                    len(storage_resources),
                )

                storage_service = ioc_util.resolve(
                    CarbonService, "IFStorage", DAILY_SECONDS
                )

                if storage_service is None:
                    raise RuntimeError(
                        "failed to resolve CarbonService from IoC container"
                    )

                processed_storage_resources: list[
                    StorageResource
                ] = storage_service.run_engine(storage_resources)

                process_time = time.time() - process_start_time

                result = self.create_CarbonDaemonResult(True, process_time, processed_storage_resources)

                logger.info(
                    "Storage processing calculations completed in %.2f seconds",
                    process_time,
                )

                logger.info(
                    "Storage processing : %d storage resources processed, "
                    "%.2f kWh total energy, %.0f gCO2 total emissions",
                    len(processed_storage_resources),
                    result.total_energy_consumed,
                    result.total_carbon_emitted,
                )

                return result

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
