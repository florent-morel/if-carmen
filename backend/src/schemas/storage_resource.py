"""
Storage Resource schema for carbon calculations.

Defines the StorageResource class representing Azure storage devices (SSDs, HDDs)
with storage-specific properties and carbon emission tracking capabilities.
"""

from __future__ import annotations

from pydantic import Field
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.common.constants import (
    DAILY_SECONDS,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_METER_CATEGORY,
    SOURCE_DATE,
    SOURCE_PROVIDER,
    SOURCE_UNIT_OF_MEASURE,
    SOURCE_QUANTITY,
    SOURCE_PRODUCT_NAME,
    SOURCE_BILLING_COST,
)


class StorageResource(Resource):
    """
    Schema for storage resource specifics.

    Represents storage devices like SSDs, HDDs with storage-specific properties
    including type, replication, size, and storage-related energy consumption.
    """

    storage_type: str  # e.g., "Premium_SSD", "Standard_HDD"
    replication_type: str  # e.g., "LRS", "ZRS", "GRS", "GZRS"
    size_gb: float  # Size in GB
    # resource_group: str | None = None
    storage_energy: list[float] = Field(default_factory=list)
    total_storage_energy: float = 0.0
    storage_embodied: list[float] = Field(default_factory=list)
    total_storage_embodied: float = 0.0
    duration_seconds: int = DAILY_SECONDS
    resource_type: ResourceType = ResourceType.STORAGE

    @staticmethod
    def mandatory_columns() -> list[str]:
        list_mandatory_columns: list[str] = [
            SOURCE_RESOURCE_ID,
            SOURCE_REGION,
            SOURCE_METER_CATEGORY,
            SOURCE_PROVIDER,
            SOURCE_DATE,
            SOURCE_UNIT_OF_MEASURE,
            SOURCE_QUANTITY,
            SOURCE_PRODUCT_NAME,
            SOURCE_BILLING_COST,

        ]
        return list_mandatory_columns
