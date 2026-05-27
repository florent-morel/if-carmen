"""
Module to handle the virtual machines to deserialize each row in a csv file retrieved from FinOps.
"""

from __future__ import annotations

from pydantic import Field
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.schemas.resource import ResourceType


class VirtualMachine(ComputeResource):
    """
    Schema for virtual machine specifics.
    """

    instance: str | None = None
    environment: str | None = None
    partition: str | None = None
    vm_size: str | None = None  # cloud/instance-type in IF
    service: str | None = None
    component: str | None = None
    resource_type: ResourceType = ResourceType.VIRTUAL_MACHINE
    vcpu_count: int | None = None  # from NbVCpus billing column; used as TDP fallback for unknown types
    storage_size: list[float] = Field(default_factory=list)  # in GB
