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
from backend.src.core.settings import ReportConfig

logger = logging.getLogger(__name__)


class AbstractWriter(ABC):
    def __init__(self, config: DaemonConfig,
                 writer: csv.DictWriter,
                 resource_result: ResourceTypeResult):
        self.resource_result: ResourceTypeResult = resource_result
        self.config: DaemonConfig = config
        self.writer: csv.DictWriter = writer

    def initialize_headers(self):
        self.writer.writeheader()

    @staticmethod
    def get_report_headers() -> Iterable[Iterable[Any]]:
        """
        Abstract method to let each resource dedicated writer list the header
        rows it needs.
        """
        list_headers = []
        for header in ReportConfig.HEADER.values():
            for header_sub in header.values():
                list_headers.append(header_sub)

        return list_headers

    @abstractmethod
    def write_content() -> Iterable[Iterable[Any]]:
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
            ReportConfig.HEADER_COMMON.DATE: self.date,
            ReportConfig.HEADER_COMMON.RESOURCE_TYPE: resource.resource_type,
            ReportConfig.HEADER_COMMON.ID: resource.id,
            ReportConfig.HEADER_COMMON.NAME: resource.name,
            ReportConfig.HEADER_COMMON.REGION: resource.region,
            ReportConfig.HEADER_COMMON.SUBSCRIPTION: resource.subscription,
            ReportConfig.HEADER_COMMON.ENERGY: resource.total_energy_consumed,
            ReportConfig.HEADER_COMMON.OPERATIONAL_CARBON: resource.total_carbon_operational,
            ReportConfig.HEADER_COMMON.EMBODIED_CARBON: resource.total_carbon_embodied,
            ReportConfig.HEADER_COMMON.TOTAL_CARBON: resource.total_carbon_emitted,
            ReportConfig.HEADER_COMMON.CARBON_INTENSITY: resource.carbon_intensity,
        }

        return row
