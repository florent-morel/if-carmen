"""
Storage module for reading and processing compute resource data.
"""

import csv
import os
import logging

from pydantic import ValidationError

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.schemas.resource import Resource
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.helpers.storage_helpers import (
    calculation_period_days,
    process_storage_row,
)
from backend.src.schemas.storage_resource import StorageResource

logger = logging.getLogger(__name__)


class Reader_Storage(AbstractReader):
    """
    Class for reading storage input data.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config
        self.list_resources_to_process: list[Resource]
        self.storage_file = os.getenv(CSV_PATH, CSV_FILE_TEST)

    @property
    def list_resources_to_process(self) -> list[Resource] | None:
        return self.list_resources_to_process

    def read(self, csv_data) -> list[Resource]:
        """
        Read and process files to extract storage resource information.

        Returns:
            list[StorageResource]: List of storage resources extracted from the
            data source.
        """
        logger.info(f"Inside reader Storage: {self}")
        storage_resources = list[Resource]
        storage_dict = {}
        self.process_csv_data(csv_data, storage_dict, None)
        storage_resources = list(storage_dict.values())

        logger.info(
            "Loaded %d storage resources from local test file",
            len(storage_resources),
        )
        self.list_resources_to_process = storage_resources

        return self.list_resources_to_process

    def process_csv_data(
        self,
        csv_data: str,
        storage_dict: dict[str, StorageResource],
        missing_region_resource_count: dict[str, int],
    ) -> bool:
        """
        Parse CSV data into StorageResource objects.

        Args:
            csv_data: Raw CSV data as string
            storage_dict: Dictionary to store processed storage resources

        Returns:
            bool: True if data was found and processed, False otherwise
        """
        rows = csv_data.splitlines()
        if len(rows) <= 1:
            return False

        csv_reader = csv.DictReader(rows)
        data_found = False

        # Debug counters
        total_rows = 0
        total_storage_rows = 0
        not_storage_rows = 0
        disk_rows = 0
        excluded_rows = 0

        period_days = calculation_period_days(csv_data)

        logger.info("Processing CSV...")

        for row in csv_reader:
            total_rows += 1

            # Filter for MeterCategory = "Storage"
            meter_category = row.get("MeterCategory", "").lower()
            if "storage" not in meter_category:
                not_storage_rows += 1
                continue

            total_storage_rows += 1

            # Process storage row using helper
            try:
                if process_storage_row(row, period_days, storage_dict):
                    disk_rows += 1
                    data_found = True
                else:
                    excluded_rows += 1
            except ValidationError as e:
                logger.exception(
                    "ValidationError for storage row %s: %s",
                    row.get("LineNumber", ""),
                    str(e),
                )
                excluded_rows += 1
                continue

        logger.info("Storage CSV processed")

        # Summary logging
        logger.debug("Storage processing summary:")
        logger.debug("  Total rows: %s", total_rows)
        logger.debug("  Total Storage rows: %s", total_storage_rows)
        logger.debug("  Not Storage rows: %s", not_storage_rows)
        logger.debug("  Excluded rows: %s", excluded_rows)
        logger.debug("  Disk rows (processed): %s", disk_rows)
        logger.debug("  Billing period days: %s", period_days)

        return data_found
