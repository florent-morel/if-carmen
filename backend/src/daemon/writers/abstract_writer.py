import logging
import os
import csv
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Iterable

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.resource import Resource
from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
from backend.src.core.settings import settings, ReportConfig

logger = logging.getLogger(__name__)


class AbstractWriter(ABC):
    def __init__(self, config: "DaemonConfig", resource_result: ResourceTypeResult):
        self.resource_result: ResourceTypeResult = resource_result
        self.date: str = AbstractWriter.get_execution_date()
        self.config: "DaemonConfig" = config
        self.out_file: str = os.path.join(
            str(self.config.upload_path), f"CO2_{self.date}.csv"
        )
        with open(self.out_file, "w", newline="") as csvfile:
            fieldnames = self.get_report_headers()
            self.writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

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

    def initialize_headers(self):
        self.writer.writeheader()

    def get_report_headers() -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer list the header
        rows it needs.
        """
        return ReportConfig.REPORT_HEADERS

    @abstractmethod
    def build_content() -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer build the
        content it needs.
        """

    def build_common_content(self, resource: Resource) -> dict[str, str]:
        """
        Method to fill common columns for a given resource.
        Args:
            resource: the resource to fill the columns.
        """
        # Add information to fill common columns
        row = {
            # Common columns
            ReportConfig.HEADER_COMMON_DATE: self.date,
            ReportConfig.HEADER_COMMON_RESOURCE_TYPE: resource.resource_type,
            ReportConfig.HEADER_COMMON_ID: resource.id,
            ReportConfig.HEADER_COMMON_NAME: resource.name,
            ReportConfig.HEADER_COMMON_REGION: resource.region,
            ReportConfig.HEADER_COMMON_SUBSCRIPTION: resource.subscription,
            ReportConfig.HEADER_COMMON_ENERGY: resource.total_energy_consumed,
            ReportConfig.HEADER_COMMON_OPERATIONAL_CARBON: resource.total_carbon_operational,
            ReportConfig.HEADER_COMMON_EMBODIED_CARBON: resource.total_carbon_embodied,
            ReportConfig.HEADER_COMMON_TOTAL_CARBON: resource.total_carbon_emitted,
            ReportConfig.HEADER_COMMON_CARBON_INTENSITY: resource.carbon_intensity,
        }

        return row
