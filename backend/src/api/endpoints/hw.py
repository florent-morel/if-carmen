"""
API module handling router of the hardware endpoints.
"""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Query, HTTPException
from starlette.requests import Request
from backend.src.schemas.response_models import HardwareResponse
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util
from backend.src.utils.helpers import validate_query_parameters
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.core.yaml_config_loader import config

router = APIRouter()


@router.get(
    "/run-engine-hardware/",
    summary="Returns the computed data (such as kWh, gCO2, etc.) for the selected VM type and CPU utilization.",
    response_model=list[HardwareResponse],
)
async def run_engine_for_selected_hardware(
    request: Request,
    vm_type: Annotated[
        str | None,
        Query(
            title="VM Type",
            description="VM type for the selected VMs.\n\n Example: Standard_E16as_v4",
            alias="virtual_machine-type",
        ),
    ],
    cpu_load: Annotated[
        list[float],
        Query(
            title="CPU Load (%)",
            description="CPU load for the selected VM type (%).\n\n Format: 0-100 \n\n",
            alias="cpu-load",
        ),
    ],
    storage_size: Annotated[
        list[float],
        Query(
            title="Storage Size (GB)",
            description="Storage size for the selected VM type (GB).\n\n",
            alias="storage-size",
        ),
    ],
    duration: Annotated[
        int | None,
        Query(
            title="Duration",
            description="Duration over which to calculate the carbon emissions in seconds",
            alias="duration",
        ),
    ],
) -> list[ComputeResource]:
    """
    Runs the carbon engine for selected VM type and CPU load and memory usage metrics and retrieves computed data
    (such as kWh, gCO2, etc.)

    Args:

        request (Request): The incoming request.

        duration (str, optional): Duration for the engine.

        cpu_load (List[float]): CPU load for the selected VM type.

        vm_type (str): VM type for the selected VMs.

    Returns:

        HardwareResponse: Computed data based on hardware inputs.
    """
    allowed_params = {
        "duration",
        "cpu-load",
        "storage-size",
        "virtual_machine-type",
    }
    validate_query_parameters(request, allowed_params)

    # Check if cpu load and storage size are the same length
    if len(cpu_load) != len(storage_size):
        raise HTTPException(
            status_code=400,
            detail="CPU load and storage size arrays must have the same length.",
        )

    provider = config.carmen_api.provider if config.carmen_api else None
    if not provider:
        raise HTTPException(
            status_code=400,
            detail="carmen_api.provider must be configured for hardware calculations.",
        )

    # Compute the sampling rate(step_seconds)
    num_of_data_points = len(cpu_load)
    step_seconds = round(duration / num_of_data_points)

    time_points = []
    for i in range(num_of_data_points):
        time_points.append(str(i * step_seconds))

    # input for run_engine()
    vms = [
        VirtualMachine(
            id="0",
            provider=provider,
            vm_size=vm_type,
            cpu_util=cpu_load,
            storage_size=storage_size,
            time_points=time_points,
            carbon_intensity=PaasCiMapper.calculate_ci(
                "germanywestcentral"
            ),  # mocked for now
        )
    ]

    carbon_service = ioc_util.resolve(CarbonService, "IFVm", duration)
    return carbon_service.run_engine(vms)
