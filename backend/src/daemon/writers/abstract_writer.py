
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Iterable

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.resource import Resource
from backend.src.daemon.carbon_daemon_result import ResourceDaemonResult

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

    def build_common_content(self, resource: Resource) -> Iterable[Any]:
        """
        Method to fill common columns for a given resource.
        Args:
            resource: the resource to fill the columns.
        """

        # Add information to fill common columns
        row = [
            # Common columns
            self.date,
            resource.resource_type,  # TODO: there's no resource_type attribute in Resource.
            resource.id,
            resource.name,
            resource.region,
            resource.subscription,
            resource.total_energy_consumed,
            resource.total_carbon_operational,
            resource.total_carbon_embodied,
            resource.total_carbon_emitted,
            resource.carbon_intensity,
        ]

        return row
