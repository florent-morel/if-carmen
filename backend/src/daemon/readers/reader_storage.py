"""
Storage module for reading and processing compute resource data.
"""

import csv
import os
import logging
import re

from pydantic import ValidationError
from datetime import datetime
from backend.src.utils.helpers import str_to_float

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.schemas.resource import Resource
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.helpers.storage_helpers import (
    calculation_period_days,
    process_storage_row,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)

logger = logging.getLogger(__name__)


class Reader_Storage(AbstractReader):
    """
    Class for reading storage input data.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config
        # TODO: Instantiate provider config
        self.provider_config: AbstractProviderConfig
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
        # Calculate storage size and duration
        size_gb, duration_seconds = self.calculate_storage_size(
            row, billing_period_days
        )

        if size_gb <= 0 or duration_seconds <= 0:
            return False  # Not a valid disk

        # Generate storage ID
        storage_id = row.get("LineNumber", "")
        if not storage_id:
            logger.error("No line number for %s", row.get("ProductName", ""))
            return False

        # Get storage characteristics
        storage_type = self.get_storage_type(row)
        replication_type = self.get_replication_type(row)

        # Size validation
        if size_gb > 32767:  # Maximum Azure disk size
            logger.warning("Unusually large disk: %sGB for %s", size_gb, storage_id)

        # Create or update storage resource
        if storage_id not in storage_dict:
            storage_dict[storage_id] = self.create_storage_resource(
                row,
                storage_id,
                size_gb,
                storage_type,
                replication_type,
                duration_seconds,
            )

        # Add temporal data
        timestamp = row.get("Date", datetime.now().strftime("%Y-%m-%d"))
        storage_dict[storage_id].time_points.append(timestamp)

        # Region validation
        region = row.get("ResourceLocation", "unknown")
        if not region or region == "unknown":
            logger.warning("Missing region for %s", storage_id)
        return True

    # TODO: ca dégage
    def get_replication_type(row: dict) -> str:
        """
        Extracts replication type from ProductName or MeterName.

        Args:
            row: CSV row data

        Returns:
            str: Replication type (LRS/GRS/ZRS/etc.)
        """
        product_name = row.get("ProductName", "").upper()
        meter_name = row.get("MeterName", "").upper()

        text_to_search = f"{product_name} {meter_name}"

        if "RA-GZRS" in text_to_search or "RAGZRS" in text_to_search:
            return "RA_GZRS"
        if "GZRS" in text_to_search:
            return "GZRS"
        if "RA-GRS" in text_to_search or "RAGRS" in text_to_search:
            return "RA_GRS"
        if "GRS" in text_to_search:
            return "GRS"
        if "ZRS" in text_to_search:
            return "ZRS"
        if "LRS" in text_to_search:
            return "LRS"

        return "LRS"  # Default

    def calculate_storage_size(
        self, row: dict[str, str], billing_period_days: int
    ) -> tuple[float, int]:
        """
        Calculate storage size AND duration according to UnitOfMeasure methodology.

        Args:
            row: CSV row data containing storage billing information
            billing_period_days: Number of days in the billing period

        Returns:
            tuple[float, int]: (size_gb, duration_seconds) or (0.0, 0) for non-disk resources
        """
        unit_of_measure = row.get("UnitOfMeasure", "")
        quantity = str_to_float(row.get("Quantity", "0"))
        product_name = row.get("ProductName", "")

        if unit_of_measure == "1 GiB/Hour":
            # Premium SSD v2 / dynamic disks
            size_gb = (quantity / 24) * 1.07374182  # GiB → GB conversion
            duration_seconds = 86400  # * billing_period_days # 1 day * number of days
            return size_gb, duration_seconds

        if unit_of_measure == "1/Month":
            # Classic disks with SKU (P10, P20, etc.)
            # Extract size from SKU in ProductName, quantity represents number of disks
            sku_size = self.extract_size_from_product_name(product_name)
            if sku_size > 0:
                size_gb = sku_size
                duration_seconds = int(round(billing_period_days * quantity * 86400))
                return size_gb, duration_seconds

            # Log warning for missing SKU but return 0 to exclude
            logger.warning("No SKU size found for 1/Month: %s", product_name)
            return 0.0, 0

        if unit_of_measure == "1 GB/Month":  # Snapshots
            return 0.0, 0
            # IMP: Snapshots needs lower ratios?
            # size_gb = quantity  # * billing_period_days
            # duration_seconds = 86400  # 1 day
            # return size_gb, duration_seconds

        if unit_of_measure in ["1", "1/Hour"]:  # Performance options or unknown
            return 0.0, 0

        if unit_of_measure in ["100", "10K", "10K/Month"]:  # Operations (I/O, tags...)
            return 0.0, 0

        if (
            unit_of_measure == "1 GB"
        ):  # Network transfers (e.g., geo-replication, retrieval)
            return 0.0, 0

        if (
            unit_of_measure == "1M"
        ):  # Operations per million (Blob inventory, Change Feed)
            return 0.0, 0

        # Unknown UnitOfMeasure
        logger.warning("Unknown UnitOfMeasure: %s, %s", unit_of_measure, product_name)
        return 0.0, 0

    def extract_size_from_product_name(self, product_name: str) -> float:
        """
        Extracts size from ProductName containing SKU.
        Examples:
        - "Premium SSD Managed Disks - P15 LRS - EU West" -> P15 = 256 GB
        - "Standard HDD Managed Disks - S4 - LRS - Disk - EU West" -> S4 = 32 GB

        Args:
            product_name: Product name containing SKU information

        Returns:
            float: Size in GB, 0.0 if not found
        """
        # Pattern to capture SKUs: P15, S4, E10, etc.
        sku_pattern = r"\b([PES]\d+)\b"
        matches = re.findall(sku_pattern, product_name.upper())

        for match in matches:
            disk_sku_mapping = self.provider_config.get_disk_sku_size_mapping()
            # TODO: check if dict.get() works
            if match in disk_sku_mapping:
                return float(disk_sku_mapping[match])

        return 0.0
