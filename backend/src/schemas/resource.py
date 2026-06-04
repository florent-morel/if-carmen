"""
Base Resource schema for carbon calculations.

Defines the base Resource class containing common fields for all resource types
including energy consumption and carbon emission tracking capabilities.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


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
    provider: str | None = None

    id: str  # Unique identifier for the resource
    name: str | None = None
    carbon_intensity: float = 0.0
    pue: float = 1.0
    region: str | None = None
    # subscription: Optional[str] = None
    billing_cost: float = 0.0

    # List for each time point
    energy_consumed: list[float] = Field(default_factory=list)
    carbon_operational: list[float] = Field(default_factory=list)
    carbon_embodied: list[float] = Field(default_factory=list)
    carbon_emitted: list[float] = Field(default_factory=list)
    time_points: list = Field(
        default_factory=list
    )  # time for VM, timestamp for Pod/App

    # Total for all time points
    total_energy_consumed: float = 0.0
    total_carbon_operational: float = 0.0
    total_carbon_embodied: float = 0.0
    total_carbon_emitted: float = 0.0

    # Dynamic columns dictionary
    dict_custom_columns: dict[str, str] = {}
