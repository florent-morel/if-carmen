"""
Base Resource schema for carbon calculations.

Defines the base Resource class containing common fields for all resource types
including energy consumption and carbon emission tracking capabilities.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from backend.src.common.constants import (
    SOURCE_SAMPLE_DURATION_SECONDS,
    SOURCE_RESOURCE_ID,
    SOURCE_RESOURCE_TYPE,
    SOURCE_REGION,
    SOURCE_SAMPLE_TIMESTAMP,
    SOURCE_PROVIDER,
    SOURCE_RESOURCE_NAME,
    SOURCE_COST,
)


class ResourceType(Enum):
    """Supported resources types."""

    VIRTUAL_MACHINE = "VirtualMachine"
    STORAGE = "Storage"
    MISC_SERVICES = "MiscServices"


class Resource(ABC, BaseModel):
    """
    Base schema for all resource types (compute, storage, network, etc.).

    Contains common fields for energy consumption and carbon emission tracking
    that are shared across all resource types.
    """

    resource_type: ResourceType = None
    timestamp: str = None

    id: str  # Unique identifier for the resource
    name: str | None = None
    provider: str | None = None
    carbon_intensity: float = 0.0
    pue: float = 1.0
    region: str | None = None
    cost: float = 0.0

    # List for each time point
    energy_consumed: list[float] = Field(default_factory=list)
    carbon_operational: list[float] = Field(default_factory=list)
    carbon_embodied: list[float] = Field(default_factory=list)
    carbon_emitted: list[float] = Field(default_factory=list)
    time_points: list = Field(
        default_factory=list
    )  # time for VM, timestamp for Pod/App
    duration_seconds: list[int] = Field(default_factory=list)

    # Total for all time points
    total_energy_consumed: float = 0.0
    total_carbon_operational: float = 0.0
    total_carbon_embodied: float = 0.0
    total_carbon_emitted: float = 0.0

    # Dynamic columns dictionary
    dict_custom_columns: dict[str, str] = {}

    @field_validator("duration_seconds", mode="before")
    @classmethod
    def normalize_duration_seconds(cls, value: Any) -> list[int]:
        """Allow scalar duration input while storing a normalized list[int]."""
        if value is None or value == "":
            return []

        if isinstance(value, (list, tuple)):
            try:
                return [int(v) for v in value]
            except (TypeError, ValueError) as err:
                raise ValueError(
                    "duration_seconds must be an integer or list of integers"
                ) from err

        try:
            return [int(value)]
        except (TypeError, ValueError) as err:
            raise ValueError(
                "duration_seconds must be an integer or list of integers"
            ) from err

    @staticmethod
    def common_mandatory_columns() -> list[str]:
        list_mandatory_columns: list[str] = [
            SOURCE_RESOURCE_ID,
            SOURCE_RESOURCE_TYPE,
            SOURCE_RESOURCE_NAME,
            SOURCE_PROVIDER,
            SOURCE_REGION,
            SOURCE_SAMPLE_TIMESTAMP,
            SOURCE_SAMPLE_DURATION_SECONDS,
            SOURCE_COST,
        ]
        return list_mandatory_columns
