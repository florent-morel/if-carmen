"""
Storage module for reading and processing compute resource data.
"""

import csv
import logging

from pydantic import ValidationError
from datetime import datetime

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.readers.helpers.storage_helpers import _process_storage_row
from backend.src.core.yaml_config_loader import config
from backend.src.daemon.readers.helpers.storage_helpers import (
    date_delta,
    create_storage_resource,
    get_storage_type,
    get_replication_type,
    calculate_storage_size,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.common.constants import (
    SOURCE_RESOURCE_ID,
    SOURCE_PROVIDER,
    SOURCE_REGION,
    SOURCE_METER_CATEGORY,
    SOURCE_DATE,
    DATE_FORMAT,
    UNKNOWN,
)

logger = logging.getLogger(__name__)


class Reader_Storage(AbstractReader):
    """
    Class for reading storage input data.
    """

    def read(self, csv_data) -> list[Resource]:
        """
        Read and process files to extract storage resource information.

        Returns:
            list[StorageResource]: List of storage resources extracted from the
            data source.
        """

        logger.info("Starting to read storage data from local filesystem")

        try:
            storage_dict: dict[str, StorageResource] = {}

            self.process_csv_data(csv_data, storage_dict)

            self.list_resources_to_process = list(storage_dict.values())

            self.log_processing_results()

            return self.list_resources_to_process

        except Exception as e:
            logger.error("failed to read files from local filesystem %s", str(e))
            raise

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
        logger.info(f"Processing row: {row}")
        provider = row.get(SOURCE_PROVIDER, "")
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
        logger.info(f"Processing {len(rows) - 1} rows for storage resources.")
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
        logger.info(f"List of mandatory columns for resource type "
                    f"{ResourceType.STORAGE}: {StorageResource.mandatory_columns()}")
        logger.info(f"csv_data: {csv_data}")

        for row in csv_reader:
            total_rows += 1

            self.process_unknown_regions(row[SOURCE_REGION])
            self.process_unknown_providers(row[SOURCE_PROVIDER])

            # Filter for MeterCategory = "Storage"
            meter_category = row.get(SOURCE_METER_CATEGORY, "").lower()
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
                    row.get(SOURCE_RESOURCE_ID, ""),
                    str(e),
                )
                excluded_rows += 1
                continue

        self.dict_log_info["total_rows"] = total_rows
        self.dict_log_info["total_storage_rows"] = total_storage_rows
        self.dict_log_info["not_storage_rows"] = not_storage_rows
        self.dict_log_info["excluded_rows"] = excluded_rows
        self.dict_log_info["disk_rows"] = disk_rows
        self.dict_log_info["period_days"] = period_days

        logger.info("Storage CSV processed")

        logger.info(f"End of process_csv_data, storage_dict: {storage_dict}")
        return data_found

    def log_processing_results(self) -> None:
        """
        Log the results of the processing operation.
        """
        logger.info("Processing completed found %d compute resources",
                    len(self.list_resources_to_process))

        # Summary logging
        logger.debug("Storage processing summary:")
        logger.debug("  Total rows: %s", self.dict_log_info["total_rows"])
        logger.debug("  Total Storage rows: %s", self.dict_log_info[
                     "total_storage_rows"])
        logger.debug("  Not Storage rows: %s", self.dict_log_info[
                     "not_storage_rows"])
        logger.debug("  Excluded rows: %s", self.dict_log_info[
                     "excluded_rows"])
        logger.debug("  Disk rows (processed): %s", self.dict_log_info[
                     "disk_rows"])
        logger.debug("  Billing period days: %s", self.dict_log_info[
                     "period_days"])

        self.log_unknown_info()

        logger.info("Local Reader processing finished successfully"
                    " for resource type storage.")
