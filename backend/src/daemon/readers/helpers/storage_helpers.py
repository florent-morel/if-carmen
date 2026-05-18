"""
Storage processing helper functions
"""

from __future__ import annotations

import csv
import logging
import re
from datetime import datetime

from backend.src.schemas.storage_resource import StorageResource
from backend.src.utils.helpers import str_to_float, get_row_data
from backend.src.utils.paas_ci_mapper import PaasCiMapper

logger = logging.getLogger(__name__)


def date_delta(csv_data: str) -> int:
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
    # TODO: this should be in each provider yaml config
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
        provider=row.get("Provider", ""),
        storage_type=storage_type,
        replication_type=replication_type,
        size_gb=size_gb,
        region=region,
        subscription=row.get("SubscriptionId", "unknown"),
        resource_group=row.get("ResourceGroup", "unknown"),
        carbon_intensity=PaasCiMapper.calculate_ci(region),
        time_points=[],
        duration_seconds=duration_seconds,
        billing_cost=get_row_data(row["BillingCost"]),
    )


# TODO: ca dégage vers la config des providers
def get_replication_type(row: dict) -> str:
    """
    Extracts replication type from ProductName or MeterName.

    Returns:
        str: Replication type (LRS/GRS/ZRS/RA_GRS/etc.)
    """
    product_name = row.get("ProductName", "").upper()
    meter_name = row.get("MeterName", "").upper()
    text = f"{product_name} {meter_name}"

    if "RA-GZRS" in text or "RAGZRS" in text:
        return "RA_GZRS"
    if "GZRS" in text:
        return "GZRS"
    if "RA-GRS" in text or "RAGRS" in text:
        return "RA_GRS"
    if "GRS" in text:
        return "GRS"
    if "ZRS" in text:
        return "ZRS"
    if "LRS" in text:
        return "LRS"
    return "LRS"  # default


def extract_size_from_product_name(product_name: str, disk_sku_mapping: dict) -> float:
    """
    Extracts disk size in GB from a SKU embedded in ProductName.
    Examples:
      "Premium SSD Managed Disks - P15 LRS - EU West" -> P15 = 256 GB
      "Standard HDD Managed Disks - S4 - LRS - Disk"  -> S4  =  32 GB

    Args:
        product_name: Product name containing SKU information
        disk_sku_mapping: Mapping of SKU code -> size in GB (from provider config)

    Returns:
        float: Size in GB, 0.0 if not found
    """
    sku_pattern = r"\b([PES]\d+)\b"
    for match in re.findall(sku_pattern, product_name.upper()):
        if match in disk_sku_mapping:
            return float(disk_sku_mapping[match])
    return 0.0


def calculate_storage_size(
    row: dict,
    billing_period_days: int,
    disk_sku_mapping: dict,
) -> tuple[float, int]:
    """
    Calculate storage size and duration according to UnitOfMeasure methodology.

    Args:
        row: CSV row data containing storage billing information
        billing_period_days: Number of days in the billing period
        disk_sku_mapping: SKU -> size mapping from provider config

    Returns:
        tuple[float, int]: (size_gb, duration_seconds), or (0.0, 0) for non-disk rows
    """
    unit_of_measure = row.get("UnitOfMeasure", "")
    quantity = str_to_float(row.get("Quantity", "0"))
    product_name = row.get("ProductName", "")

    if unit_of_measure == "1 GiB/Hour":
        # Premium SSD v2 / dynamic disks — GiB → GB conversion
        size_gb = (quantity / 24) * 1.07374182
        return size_gb, 86400

    if unit_of_measure == "1/Month":
        # Classic disks with SKU (P10, P20, S4, …)
        sku_size = extract_size_from_product_name(product_name, disk_sku_mapping)
        if sku_size > 0:
            duration_seconds = int(round(billing_period_days * quantity * 86400))
            return sku_size, duration_seconds
        logger.warning("No SKU size found for 1/Month: %s", product_name)
        return 0.0, 0

    if unit_of_measure in (
        "1 GB/Month",
        "1",
        "1/Hour",
        "100",
        "10K",
        "10K/Month",
        "1 GB",
        "1M",
    ):
        return 0.0, 0  # snapshots, perf options, ops, network transfers — excluded

    logger.warning("Unknown UnitOfMeasure: %s, %s", unit_of_measure, product_name)
    return 0.0, 0


def _process_storage_row(
    row: dict,
    billing_period_days: int,
    storage_dict: dict[str, StorageResource],
    disk_sku_mapping: dict | None = None,
) -> bool:
    """
    Process a single CSV row and add storage resource to storage_dict.
    Returns True if a valid storage resource was processed.

    Args:
        row: CSV row data
        billing_period_days: Billing period in days
        storage_dict: Dictionary to store storage resources
        disk_sku_mapping: SKU -> size mapping (from provider config)

    Returns:
        bool: True if valid storage was processed, False otherwise
    """
    if disk_sku_mapping is None:
        disk_sku_mapping = {}

    size_gb, duration_seconds = calculate_storage_size(
        row, billing_period_days, disk_sku_mapping
    )

    if size_gb <= 0 or duration_seconds <= 0:
        return False

    storage_id = row.get("LineNumber", "")
    if not storage_id:
        logger.error("No line number for %s", row.get("ProductName", ""))
        return False

    storage_type = get_storage_type(row)
    replication_type = get_replication_type(row)

    if size_gb > 32767:
        logger.warning("Unusually large disk: %sGB for %s", size_gb, storage_id)

    if storage_id not in storage_dict:
        storage_dict[storage_id] = create_storage_resource(
            row, storage_id, size_gb, storage_type, replication_type, duration_seconds
        )

    timestamp = row.get("Date", datetime.now().strftime("%Y-%m-%d"))
    storage_dict[storage_id].time_points.append(timestamp)

    region = row.get("ResourceLocation", "unknown")
    if not region or region == "unknown":
        logger.warning("Missing region for %s", storage_id)

    return True
