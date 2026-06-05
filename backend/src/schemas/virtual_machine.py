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
    SOURCE_AVG_CPU_PERCENTAGE,
    SOURCE_TIME,
    SOURCE_DISK_SIZE_GB,
    SOURCE_COST,
)


class VirtualMachine(ComputeResource):
    """
    Schema for virtual machine specifics.
    """

    # instance: str | None = None
    # environment: str | None = None
    # partition: str | None = None
    vm_size: str | None = None  # cloud/instance-type in IF
    # service: str | None = None
    # component: str | None = None
    resource_type: ResourceType = ResourceType.VIRTUAL_MACHINE
    vcpu_count: int | None = None  # from NbVCpus billing column; used as TDP fallback for unknown types
    storage_size: list[float] = Field(default_factory=list)  # in GB

    @staticmethod
    def mandatory_columns() -> list[str]:
        list_mandatory_columns: list[str] = [
            SOURCE_RESOURCE_ID,
            SOURCE_RESOURCE_TYPE,
            SOURCE_PROVIDER,
            SOURCE_REGION,
            SOURCE_AVG_CPU_PERCENTAGE,
            SOURCE_TIME,
            SOURCE_DISK_SIZE_GB,
            SOURCE_COST,
        ]
        return list_mandatory_columns
