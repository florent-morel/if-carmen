"""
Storage Resource schema for carbon calculations.

Defines the StorageResource class representing Azure storage devices (SSDs, HDDs)
with storage-specific properties and carbon emission tracking capabilities.
"""

from __future__ import annotations

from pydantic import Field
from backend.src.schemas.compute_resource import Resource
from backend.src.common.constants import DAILY_SECONDS


class StorageResource(Resource):
    """
    Schema for storage resource specifics.

    Represents storage devices like SSDs, HDDs with storage-specific properties
    including type, replication, size, and storage-related energy consumption.
    """

    storage_type: str  # e.g., "Premium_SSD", "Standard_HDD"
    replication_type: str  # e.g., "LRS", "ZRS", "GRS", "GZRS"
    size_gb: float  # Size in GB
    subscription: str | None = None
    resource_group: str | None = None
    storage_embodied: list[float] = Field(default_factory=list)
    total_storage_embodied: float = 0.0
    duration_seconds: int = DAILY_SECONDS

    def __init_(self):
        super().__init_()
        self.name = "StorageResource"
