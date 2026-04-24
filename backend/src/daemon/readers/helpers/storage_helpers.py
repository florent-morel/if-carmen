"""
Storage processing helper functions
"""

from __future__ import annotations

import csv
import logging
import re
from datetime import datetime

from backend.src.schemas.storage_resource import StorageResource
from backend.src.utils.helpers import str_to_float
from backend.src.utils.paas_ci_mapper import PaasCiMapper

logger = logging.getLogger(__name__)


def calculation_period_days(csv_data: str) -> int:
    """
    Calculate billing period days dynamically from CSV BillingPeriodStartDate and BillingPeriodEndDate.
    Format: 4/1/2025 4/30/2025
    """
    rows = csv_data.splitlines()
    if len(rows) <= 1:
        logger.error("CSV error, defaulting period size to 30 days")
        return 30  # Default fallback

    csv_reader = csv.DictReader(rows)

    for row in csv_reader:
        start_date_str = row.get("BillingPeriodStartDate", "")
        end_date_str = row.get("BillingPeriodEndDate", "")

        if start_date_str and end_date_str:
            try:
                # Parse dates in M/D/YYYY format
                start_date = datetime.strptime(start_date_str, "%m/%d/%Y")
                end_date = datetime.strptime(end_date_str, "%m/%d/%Y")

                # Calculate difference in days
                billing_days = (
                    end_date - start_date
                ).days + 1  # +1 to include both start and end days

                logger.debug(
                    "Billing period: %s to %s = %s days",
                    start_date_str,
                    end_date_str,
                    billing_days,
                )
                return billing_days

            except ValueError as e:
                logger.warning(
                    "Error parsing billing dates: %s, %s - %s",
                    start_date_str,
                    end_date_str,
                    e,
                )
                continue

    logger.warning("Could not determine billing period from CSV, using default 30 days")
    return 30


def get_storage_type(row: dict) -> str:
    """
    Extracts storage type from ProductName.
    Uses explicit mapping then fallback on keywords.

    Args:
        row: CSV row data

    Returns:
        str: Storage type (SSD/HDD/Unknown)
    """
    product_name = row.get("ProductName", "").lower()

    # Check keywords in ProductName
    if (
        "ssd" in product_name
        or "ultra disk" in product_name
        or "premium page blob" in product_name
    ):
        return "SSD"
    if "hdd" in product_name:
        return "HDD"

    logger.warning("Unknown disk type for %s", product_name)
    return "Unknown"


def create_storage_resource(
    row: dict,
    storage_id: str,
    size_gb: float,
    storage_type: str,
    replication_type: str,
    duration_seconds: int,
) -> StorageResource:
    """
    Creates a StorageResource from CSV row data.
    Centralizes all the creation logic for consistency.

    Args:
        row: CSV row data
        storage_id: Unique identifier for the storage
        size_gb: Calculated storage size
        storage_type: SSD/HDD/Unknown
        replication_type: LRS/GRS/ZRS/etc.
        duration_seconds: Duration in seconds

    Returns:
        StorageResource: Complete storage resource object
    """
    product_name = row.get("ProductName", "")
    region = row.get("ResourceLocation", "unknown")

    return StorageResource(
        id=storage_id,
        name=product_name,
        storage_type=storage_type,
        replication_type=replication_type,
        size_gb=size_gb,
        region=region,
        subscription=row.get("SubscriptionId", "unknown"),
        resource_group=row.get("ResourceGroup", "unknown"),
        carbon_intensity=PaasCiMapper.calculate_ci(region),
        time_points=[],
        duration_seconds=duration_seconds,
    )
