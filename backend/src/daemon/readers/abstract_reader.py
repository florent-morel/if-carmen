"""
Base module for reading and processing compute resource data.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from collections import Counter

from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.schemas.resource import Resource

logger = logging.getLogger(__name__)


class AbstractReader(ABC):
    """
    Abstract base class for reading compute resource data from various sources.
    """

    def __init__(self, daemon_config: DaemonConfig):
        self.config: DaemonConfig = daemon_config
        self.input_path: Path = Path(str(self.config.source.input_path)).resolve()
        logger.info(
            "Local Reader initialized with source path %s",
            self.input_path,
        )
        self.list_resources_to_process: list[Resource] | None = None
        self.known_regions: set[str] = {
            region
            for pc in config.provider_configs.values()
            if pc.get_regions()
            for region in pc.get_regions()
        }
        self.missing_regions: Counter = Counter()
        self.missing_providers: Counter = Counter()

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
    ) -> bool:
        """
        Processes CSV data from the blob and updates the resource dictionary.

        Args:
            blob_data (str): The CSV data read from the blob, as a string.
            resource_dict (Dict[str, Resource]): The dictionary containing Resource objects, indexed by their ID.
        Returns:
            bool: Returns True if the CSV data is processed successfully and contains data,
            False if the CSV data is empty (excluding the header row).
        """

    @abstractmethod
    def log_processing_results(self) -> None:
        """
        Log the results of the processing operation.
        """

    def process_missing_regions(self, region_csv):
        """
        If region coming from csv input file, store it to log it afterwards.
        """
        if region_csv not in self.known_regions:
            self.missing_regions[region_csv] += 1

    def process_missing_provider(self, provider_csv):
        """
        If provider coming from csv input file, store it to log it afterwards.
        """
        if provider_csv not in config.provider_configs:
            self.missing_providers[provider_csv] += 1

    def log_missing_info(self) -> None:
        for region, count in self.missing_regions.items():
            logger.warning(
                "Unknown Region '%s': %d — using default carbon intensity",
                region,
                count,
            )
        for provider, count in self.missing_providers.items():
            logger.warning(
                "unknown provider '%s': %d — using default PUE",
                provider,
                count,
            )
