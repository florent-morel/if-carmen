"""
Storage module for reading and processing compute resource data.
"""

import csv
import os
import logging

from pydantic import ValidationError
from datetime import datetime
from backend.src.utils.helpers import str_to_float

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.schemas.resource import Resource
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.readers.helpers.storage_helpers import (
    date_delta,
    create_storage_resource,
    get_storage_type,
    get_replication_type,
    calculate_storage_size,
    process_storage_row as _process_storage_row,
)
from backend.src.schemas.storage_resource import StorageResource

logger = logging.getLogger(__name__)


class Reader_Storage(AbstractReader):
    """
    Class for reading storage input data.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config
        self.storage_file = os.getenv(CSV_PATH, CSV_FILE_TEST)

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
        self.process_csv_data(csv_data, storage_dict)
        storage_resources = list(storage_dict.values())

        logger.info(
            "Loaded %d storage resources from local test file",
            len(storage_resources),
        )
        self.list_resources_to_process = storage_resources

        return self.list_resources_to_process

    def process_storage_row(
        self,
        row: dict,
        billing_period_days: int,
        storage_dict: dict[str, StorageResource],
    ) -> bool:
        """
        Process a single CSV row and add storage resource.
        Returns True if a valid storage resource was processed.

        Args:
            row: CSV row data
            billing_period_days: Billing period in days
            storage_dict: Dictionary to store storage resources

        Returns:
            bool: True if valid storage was processed, False otherwise
        """
        provider = row.get("Provider", "")
        provider_config = config.provider_configs.get(provider or "")
        disk_sku_mapping = (
            provider_config.get_disk_sku_size_mapping() if provider_config else None
        ) or {}
        return _process_storage_row(
            row, billing_period_days, storage_dict, disk_sku_mapping
        )

    def process_csv_data(
        self,
        csv_data: str,
        storage_dict: dict[str, StorageResource],
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

        period_days = date_delta(csv_data)

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
                if self.process_storage_row(row, period_days, storage_dict):
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
