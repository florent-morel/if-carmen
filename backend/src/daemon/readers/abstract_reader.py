"""
Base module for reading and processing compute resource data.
"""

import csv
import logging
from abc import ABC, abstractmethod

from pydantic import ValidationError

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.daemon_helpers import (
    calculate_resource_count_for_missing_regions,
    create_resource,
)
from backend.src.schemas.resource import Resource
from backend.src.utils.helpers import str_to_float

logger = logging.getLogger(__name__)


class Reader(ABC):
    """
    Abstract base class for reading compute resource data from various sources.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config

    @abstractmethod
    def read_files(self) -> list[Resource]:
        """
        Read and process files to extract resource information.

        Returns:
            list[Resource]: List of resources extracted from the data source.
        """

    @abstractmethod
    def process_csv_data(
        self,
        blob_data: str,
        resource_dict: dict[str, Resource],
        missing_region_resource_count: dict[str, int],
    ) -> bool:
        """
        Processes CSV data from the blob and updates the resource machine dictionary.

        Args:
            missing_region_resource_count (Dict[str, int]): Dictionary with the information of missing regions and
            the corresponding VM count.
            blob_data (str): The CSV data read from the blob, as a string.
            resource_dict (Dict[str, Resource]): The dictionary containing Resource objects, indexed by their ID.
        Returns:
            bool: Returns True if the CSV data is processed successfully and contains data,
            False if the CSV data is empty (excluding the header row).
        """

