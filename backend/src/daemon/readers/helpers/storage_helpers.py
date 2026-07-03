"""
Storage processing helper functions
"""

from __future__ import annotations

import logging
from datetime import datetime

from backend.src.schemas.storage_resource import StorageResource
from backend.src.utils.helpers import (
    str_to_float,
    get_row_data,
    parse_duration_seconds,
    process_custom_columns,
)
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.common.constants import (
    MAX_STORAGE_SIZE_GB_WARNING_THRESHOLD,
    SOURCE_PROVIDER,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_COST,
    SOURCE_RESOURCE_NAME,
    SOURCE_SAMPLE_DURATION_SECONDS,
    SOURCE_STORAGE_SIZE_GB,
    SOURCE_STORAGE_TYPE,
    SOURCE_STORAGE_REPLICATION_TYPE,
    SOURCE_SAMPLE_TIMESTAMP,
    DAILY_SECONDS,
    DATE_FORMAT,
    UNKNOWN,
)

logger = logging.getLogger(__name__)


def create_storage_resource(
    row: dict,
    storage_id: str,
    size_gb: float,
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
    Returns:
        StorageResource: Complete storage resource object
    """
    region = row.get(SOURCE_REGION, UNKNOWN)
    storage_type=UNKNOWN
    logger.info(f"storage_type: {storage_type}")

    return StorageResource(
        id=storage_id,
        name=row.get(SOURCE_RESOURCE_NAME, ""),
        provider=row.get(SOURCE_PROVIDER, ""),
        storage_type=row.get(SOURCE_STORAGE_TYPE, UNKNOWN),
        replication_type=row.get((SOURCE_STORAGE_REPLICATION_TYPE)),
        size_gb=size_gb,
        region=region,
        carbon_intensity=PaasCiMapper.calculate_ci(region),
        # TODO: study PUE implementation for storage energy computation
        time_points=[],
        duration_seconds=[],
        cost=get_row_data(row[SOURCE_COST]),
    )


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
        logger.error("No ResourceID found for %s",
                     row.get(SOURCE_RESOURCE_ID, ""))
        return False

    size_gb_raw = row.get(SOURCE_STORAGE_SIZE_GB)
    if size_gb_raw in (None, ""):
        logger.error("Missing %s for %s", SOURCE_STORAGE_SIZE_GB, storage_id)
        return False

    try:
        size_gb = str_to_float(size_gb_raw)
    except ValueError:
        logger.error(
            "Invalid normalized storage inputs for %s: %s=%r",
            storage_id,
            SOURCE_STORAGE_SIZE_GB,
            size_gb_raw,
        )
        return False

    duration_seconds = parse_duration_seconds(row, storage_id)
    if duration_seconds is None:
        return False

    if size_gb <= 0:
        logger.error("%s must be positive for %s",
                     SOURCE_STORAGE_SIZE_GB, storage_id)
        return False

    if size_gb > MAX_STORAGE_SIZE_GB_WARNING_THRESHOLD:
        logger.warning("Unusually large disk: %sGB for %s",
                       size_gb, storage_id)

    if storage_id not in storage_dict:
        storage_dict[storage_id] = create_storage_resource(
            row, storage_id, size_gb)

    timestamp = row.get(SOURCE_SAMPLE_TIMESTAMP,
                        datetime.now().strftime(DATE_FORMAT))
    storage_dict[storage_id].time_points.append(timestamp)
    storage_dict[storage_id].duration_seconds.append(duration_seconds)

    region = row.get(SOURCE_REGION, UNKNOWN)
    if not region or region == UNKNOWN:
        logger.warning("Missing region for %s", storage_id)

    # End of row process, fetch custom columns
    process_custom_columns(storage_dict[storage_id], row,
                           StorageResource.mandatory_columns())

    return True
