import logging
import os
import csv
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Iterable

from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import CarmenException
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.resource import Resource
from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
from backend.src.core.settings import ReportConfig

logger = logging.getLogger(__name__)


class AbstractWriter(ABC):
    def __init__(
        self,
        config: DaemonConfig,
        date: str,
        writer: csv.DictWriter,
        resource_result: ResourceTypeResult,
    ):
        self.resource_result: ResourceTypeResult = resource_result
        self.date: str = date,
        self.config: DaemonConfig = config
        self.writer: csv.DictWriter = writer

    def initialize_headers(self):
        self.writer.writeheader()

    @staticmethod
    def get_report_headers() -> list[str]:
        """
        Returns the flat list of column names used to initialise csv.DictWriter.
        """
        return ReportConfig.REPORT_HEADERS

    @abstractmethod
    def write_content(self, resources: list[Resource]) -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer build the
        content it needs.
        """

    def write_common_content(self, resource: Resource) -> dict[str, str]:
        """
        Method to fill common columns for a given resource.
        Args:
            resource: the resource to fill the columns.
        """
        # Add information to fill common columns
        row = {
            # Common columns
            ReportConfig.COMMON_DATE: self.date,
            ReportConfig.COMMON_RESOURCE_TYPE: resource.resource_type,
            ReportConfig.COMMON_ID: resource.id,
            ReportConfig.COMMON_NAME: resource.name,
            ReportConfig.COMMON_PROVIDER: resource.provider,
            ReportConfig.COMMON_REGION: resource.region,
            ReportConfig.COMMON_SUBSCRIPTION: resource.subscription,
            ReportConfig.COMMON_ENERGY: resource.total_energy_consumed,
            ReportConfig.COMMON_OPERATIONAL_CARBON: resource.total_carbon_operational,
            ReportConfig.COMMON_EMBODIED_CARBON: resource.total_carbon_embodied,
            ReportConfig.COMMON_TOTAL_CARBON: resource.total_carbon_emitted,
            ReportConfig.COMMON_CARBON_INTENSITY: resource.carbon_intensity,
        }
        return row
