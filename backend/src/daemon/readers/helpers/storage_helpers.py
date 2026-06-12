"""
Storage processing helper functions
"""

from __future__ import annotations

import logging
from datetime import datetime

from backend.src.schemas.storage_resource import StorageResource
from backend.src.utils.helpers import(
    str_to_float,
    get_row_data,
    process_custom_columns,
)
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.common.constants import (
    MAX_STORAGE_SIZE_GB_WARNING_THRESHOLD,
    SOURCE_PROVIDER,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_STORAGE_DURATION_SECONDS,
    SOURCE_STORAGE_SIZE_GB,
    SOURCE_DATE,
    DATE_FORMAT,
    UNKNOWN,
)

logger = logging.getLogger(__name__)


def get_storage_type(row: dict) -> str:
    """
    Extracts storage type from ProductName.
    Uses explicit mapping then fallback on keywords.

    Args:
        row: CSV row data

    Returns:
        str: Storage type (SSD/HDD/Unknown)
    """
    product_name = row.get(SOURCE_PRODUCT_NAME, "").lower()

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
    return UNKNOWN


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
    product_name = row.get(SOURCE_PRODUCT_NAME, "")
    region = row.get(SOURCE_REGION, UNKNOWN)

    return StorageResource(
        id=storage_id,
        name=product_name,
        provider=row.get(SOURCE_PROVIDER, ""),
        storage_type=storage_type,
        replication_type=replication_type,
        size_gb=size_gb,
        region=region,
        carbon_intensity=PaasCiMapper.calculate_ci(region),
        time_points=[],
        duration_seconds=duration_seconds,
        cost=get_row_data(row[SOURCE_COST]),
    )


# TODO: ca dégage vers la config des providers
def get_replication_type(row: dict) -> str:
    """
    Extracts replication type from ProductName.

    Returns:
        str: Replication type (LRS/GRS/ZRS/RA_GRS/etc.)
    """
    product_name = row.get(SOURCE_PRODUCT_NAME, "").upper()

    if "RA-GZRS" in product_name or "RAGZRS" in product_name:
        return "RA_GZRS"
    if "GZRS" in product_name:
        return "GZRS"
    if "RA-GRS" in product_name or "RAGRS" in product_name:
        return "RA_GRS"
    if "GRS" in product_name:
        return "GRS"
    if "ZRS" in product_name:
        return "ZRS"
    if "LRS" in product_name:
        return "LRS"
    return "LRS"  # default


def _process_storage_row(
    row: dict,
    storage_dict: dict[str, StorageResource],
) -> bool:
    """
    Process a single CSV row and add storage resource to storage_dict.
    Returns True if a valid storage resource was processed.

    Args:
        row: CSV row data
        storage_dict: Dictionary to store storage resources

    Returns:
        bool: True if valid storage was processed, False otherwise
    """
    storage_id = row.get(SOURCE_RESOURCE_ID, "")
    if not storage_id:
        logger.error("No ResourceID found for %s", row.get(SOURCE_RESOURCE_ID, ""))
        return False

    size_gb_raw = row.get(SOURCE_STORAGE_SIZE_GB)
    duration_seconds_raw = row.get(SOURCE_STORAGE_DURATION_SECONDS)

    if size_gb_raw in (None, ""):
        logger.error("Missing %s for %s", SOURCE_STORAGE_SIZE_GB, storage_id)
        return False

    if duration_seconds_raw in (None, ""):
        logger.error("Missing %s for %s", SOURCE_STORAGE_DURATION_SECONDS, storage_id)
        return False

    try:
        size_gb = str_to_float(size_gb_raw)
        duration_seconds_value = str_to_float(duration_seconds_raw)
    except ValueError:
        logger.error(
            "Invalid normalized storage inputs for %s: %s=%r, %s=%r",
            storage_id,
            SOURCE_STORAGE_SIZE_GB,
            size_gb_raw,
            SOURCE_STORAGE_DURATION_SECONDS,
            duration_seconds_raw,
        )
        return False

    if size_gb <= 0:
        logger.error("%s must be positive for %s", SOURCE_STORAGE_SIZE_GB, storage_id)
        return False

    if duration_seconds_value <= 0:
        logger.error(
            "%s must be positive for %s",
            SOURCE_STORAGE_DURATION_SECONDS,
            storage_id,
        )
        return False

    if not duration_seconds_value.is_integer():
        logger.error(
            "%s must be an integer number of seconds for %s",
            SOURCE_STORAGE_DURATION_SECONDS,
            storage_id,
        )
        return False

    duration_seconds = int(duration_seconds_value)
    storage_type = get_storage_type(row)
    replication_type = get_replication_type(row)

    if size_gb > MAX_STORAGE_SIZE_GB_WARNING_THRESHOLD:
        logger.warning("Unusually large disk: %sGB for %s", size_gb, storage_id)

    if storage_id not in storage_dict:
        storage_dict[storage_id] = create_storage_resource(
            row, storage_id, size_gb, storage_type, replication_type, duration_seconds
        )

    timestamp = row.get(SOURCE_DATE, datetime.now().strftime(DATE_FORMAT))
    storage_dict[storage_id].time_points.append(timestamp)

    region = row.get(SOURCE_REGION, UNKNOWN)
    if not region or region == UNKNOWN:
        logger.warning("Missing region for %s", storage_id)

    # End of row process, fetch custom columns
    process_custom_columns(storage_dict[storage_id], row,
                           StorageResource.mandatory_columns())

    return True
