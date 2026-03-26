
from abc import ABC, abstractmethod
from typing import Any, Iterable
import logging
import time
import csv
import os
from datetime import datetime, timedelta
from backend.src.common.known_exception import KnownException
from backend.src.common.errors import ErrorCode
from backend.src.core.settings import settings
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.resource import Resource

logger = logging.getLogger(__name__)


class AbstractWriter(ABC):

    def __init__(self, config: "DaemonConfig", resource: list[Resource]):
        self.resources: list[Resource] = resource
        self.date: str = AbstractWriter.get_execution_date()
        self.config: "DaemonConfig" = config
        self.out_file: str = os.path.join(
            str(self.config.upload_path), f"CO2_{self.date}.csv"
        )

    @abstractmethod
    def upload_compute_report(self):
        pass

    @staticmethod
    def get_execution_date():
        execution_date_str = os.getenv("EXECUTION_DATE")
        if not execution_date_str:
            execution_date_str = (datetime.now() - timedelta(days=2)).strftime(
                "%Y-%m-%d"
            )
        try:
            execution_date = datetime.strptime(execution_date_str, "%Y-%m-%d")
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
            execution_date.strftime("%Y-%m-%d"),
        )
        return execution_date_str

    def create_compute_CO2_report(
        self,
    ):
        """
        Creates a CSV report containing all resource types.
        Handles VMs, Storage, and future resource categories in one file.
        """
        resources = self.resources or []

        logger.info(
            "Creating CSV report with %d resources",
            len(resources),
        )
        start = time.time()


        # TODO: Implement loop on all active resources

        with open(self.out_file, mode="w", newline="", encoding="utf-8") as report:
            writer = csv.writer(report)

        # TODO: call each writer to get rows
            writer.writerows(self.build_rows_headers())
            for row in self.build_content():
                writer.writerow(row)

        elapsed_time = time.time() - start
#         logging.info("Total carbon emitted: %.2f kg CO2", vm_carbon)
#         logging.info("Total energy consumed: %.2f kWh", vm_energy)
        logger.info("CSV report created in %.2f seconds", elapsed_time)
        logger.info(
            "  Resources: %d resources",
            len(resources),
        )
        logger.info("Report saved to: %s", self.out_file)

    @abstractmethod
    def build_rows_headers() -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer list the header
        rows it needs.
        """

    @abstractmethod
    def build_content() -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer build the 
        content it needs.
        """
