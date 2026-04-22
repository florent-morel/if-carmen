
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
from backend.src.daemon.carbon_daemon_result import ResourceDaemonResult
from backend.src.core.settings import settings, FinOpsConfig

logger = logging.getLogger(__name__)


class AbstractWriter(ABC):

    def __init__(self, config: "DaemonConfig",
                 resource_result: ResourceDaemonResult):
        self.resource_result: ResourceDaemonResult
        self.date: str = AbstractWriter.get_execution_date()
        self.config: "DaemonConfig" = config
        self.out_file: str = os.path.join(
            str(self.config.upload_path), f"CO2_{self.date}.csv"
        )
        with open(self.out_file, 'w', newline='') as csvfile:
            # fieldnames = ['first_name', 'last_name']
            # self.writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            self.writer = csv.DictWriter(csvfile)

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

    def build_rows_headers() -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer list the header
        rows it needs.
        """
        return settings.FINOPS.REPORT_HEADERS

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
            FinOpsConfig.HEADER_COMMON_DATE: self.date,
            FinOpsConfig.HEADER_COMMON_RESOURCE_TYPE: resource.resource_type,
            FinOpsConfig.HEADER_COMMON_ID: resource.id,
            FinOpsConfig.HEADER_COMMON_NAME: resource.name,
            FinOpsConfig.HEADER_COMMON_REGION: resource.region,
            FinOpsConfig.HEADER_COMMON_SUBSCRIPTION: resource.subscription,
            FinOpsConfig.HEADER_COMMON_ENERGY: resource.total_energy_consumed,
            FinOpsConfig.HEADER_COMMON_OPERATIONAL_CARBON: resource.total_carbon_operational,
            FinOpsConfig.HEADER_COMMON_EMBODIED_CARBON: resource.total_carbon_embodied,
            FinOpsConfig.HEADER_COMMON_TOTAL_CARBON: resource.total_carbon_emitted,
            FinOpsConfig.HEADER_COMMON_CARBON_INTENSITY: resource.carbon_intensity,
        }

        return row
