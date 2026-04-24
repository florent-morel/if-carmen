"""
Base module for reading and processing compute resource data.
"""

import logging
from abc import ABC, abstractmethod

from backend.src.schemas.resource import Resource

logger = logging.getLogger(__name__)


class AbstractReader(ABC):
    """
    Abstract base class for reading compute resource data from various sources.
    """

    def __init__(
        self,
    ):
        """
        Initialize reader.

        Args:

        """

    @property
    @abstractmethod
    def list_resources_to_process(self) -> list[Resource] | None:
        pass

    @abstractmethod
    def read(self, csv_data: str) -> list[Resource]:
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
        Processes CSV data from the blob and updates the resource dictionary.

        Args:
            missing_region_resource_count (Dict[str, int]): Dictionary with the information of missing regions and
            the corresponding resources count.
            blob_data (str): The CSV data read from the blob, as a string.
            resource_dict (Dict[str, Resource]): The dictionary containing Resource objects, indexed by their ID.
        Returns:
            bool: Returns True if the CSV data is processed successfully and contains data,
            False if the CSV data is empty (excluding the header row).
        """
