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
    # TODO: check if this is really necessary
    # storage_size: list[float] = Field(default_factory=list)  # in GB
    # storage_energy: list[float] = Field(default_factory=list)
    # total_storage_energy: float = 0.0
    # storage_embodied: list[float] = Field(default_factory=list)
    # total_storage_embodied: float = 0.0

    def __init_(self):
        super().__init_()
        self.resource_type = ResourceType.VIRTUAL_MACHINE.value
