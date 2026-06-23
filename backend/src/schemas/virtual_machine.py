"""
Module to handle the virtual machines to deserialize each row in a csv file retrieved from FinOps.
"""

from __future__ import annotations

from pydantic import Field
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.schemas.resource import ResourceType
from backend.src.common.constants import (
    SOURCE_RESOURCE_ID,
    SOURCE_RESOURCE_TYPE,
    SOURCE_REGION,
    SOURCE_PROVIDER,
    SOURCE_VM_AVG_CPU_UTIL_PERCENT,
    SOURCE_TIME,
    SOURCE_DURATION_SECONDS,
    SOURCE_VM_DISK_SIZE_GB,
    # TODO: Add DISK_TYPE (akin to storage_type for storage resources, to be then propagated in computation)
    # At the moment we always fallback on the default values for the VMs' disk.
    SOURCE_COST,
)


class VirtualMachine(ComputeResource):
    """
    Schema for virtual machine specifics.
    """

    vm_size: str | None = None  # cloud/instance-type in IF
    resource_type: ResourceType = ResourceType.VIRTUAL_MACHINE
    vcpu_count: int | None = None  # from VmNbCpus billing column; used as TDP fallback for unknown types
    storage_size: list[float] = Field(default_factory=list)  # in GB

    @staticmethod
    def mandatory_columns() -> list[str]:
        list_mandatory_columns: list[str] = [
            SOURCE_RESOURCE_ID,
            SOURCE_RESOURCE_TYPE,
            SOURCE_PROVIDER,
            SOURCE_REGION,
            SOURCE_VM_AVG_CPU_UTIL_PERCENT,
            SOURCE_TIME,
            SOURCE_DURATION_SECONDS,
            SOURCE_VM_DISK_SIZE_GB,
            SOURCE_COST,
        ]
        return list_mandatory_columns
