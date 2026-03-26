"""
Module to handle the common fields of compute resources
"""

from __future__ import annotations

from pydantic import Field
from backend.src.schemas.resource import Resource


class ComputeResource(Resource):
    """
    Base schema for compute resources (VMs, pods, applications).
    Extends Resource with compute-specific fields for CPU, memory, storage capacity,
    and network I/O tracking.
    """

    cpu_energy: list[float] = Field(default_factory=list)
    memory_energy: list[float] = Field(default_factory=list)
    cpu_power: list[float] = Field(default_factory=list)
    requested_cpu: list[float] = Field(default_factory=list)  # in cores (pod),
    # nb_vcpus (virtual_machine) but cloud-metadata retrieves it
    cpu_util: list[float] = Field(default_factory=list)
    storage_capacity: list[float] = Field(default_factory=list)
    network_io: list[float] = Field(default_factory=list)
    requested_memory: list[float] = Field(default_factory=list)  # in bytes
    total_cpu_energy: float = 0.0
    total_memory_energy: float = 0.0
