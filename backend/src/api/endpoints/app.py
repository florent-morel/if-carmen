"""
This module defines API routes for retrieving resources and computing data for selected resources.

It contains endpoints for:
1. Retrieving available resources either paas, app or namespace.
2. Computing data (such as kWh, gCO2, etc.) for each pod of selected resource.
3. Computing data (such as kWh, gCO2, etc.) for a given Azure VM size, and its CPU load.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated
from fastapi import Query, APIRouter
from starlette.requests import Request

from backend.src.common.enums import SamplingRate
from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import (
    DataFetchError,
    ValidationError,
    DateValidationError,
    ComputationError,
)
from backend.src.schemas.pod import Pod
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils.helpers import (
    convert_to_seconds,
    validate_query_parameters,
    get_end_time,
    get_start_time,
)
from backend.src.services.argos_service import ArgosService
from backend.src.utils import ioc_util


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/", summary="Returns available paas, app or namespace values")
async def get_available_resources(
    selected_apps: Annotated[
        list[str] | None,
        Query(
            title="Selected Apps",
            description=(
                "Selected compute_resource for which a list of pods will be "
                "retrieved at the specified time interval"
            ),
            alias="app",
        ),
    ] = None,
    paas: Annotated[
        list[str] | None,
        Query(
            title="Platform as a Service (PaaS)",
            description="Platform as a Service (PaaS) to be used for the selected compute_resource.",
            alias="paas",
        ),
    ] = None,
) -> dict[str, list[str]]:
    """
    Retrieves a dictionary of available resources (paas, app or namespace).

    Returns:

        Dict[str, List[str]]: key as the resource type and value as the list of available resources.

    Raises:
        DataFetchError: If fetching available resources fails.
        ValidationError: If the provided parameters are invalid.
    """
    try:
        logger.info(
            "Fetching available resources for apps: %s, paas: %s",
            selected_apps,
            paas,
        )
        return await ArgosService().get_available_resources(selected_apps, paas)
    except (DataFetchError, ValidationError):
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching available resources")
        raise DataFetchError(
            ErrorCode.DATA_FETCH_FAILED,
            source="ArgosService",
            details=str(e),
        ) from e


@router.get(
    "/run-engine/",
    summary=(
        "Returns the computed data (such as kWh, gCO2, etc.) for each pod of "
        "the selected resources at application or pod level, in addition to "
        "the extracted data (CPU, memory, etc.)"
    ),
    response_model=list[ComputeResource] | dict[str, dict[str, dict[str, list[Pod]]]],
)
async def run_engine_for_selected_resources(
    request: Request,
    start_date: Annotated[
        datetime | None,
        Query(
            default_factory=get_start_time,
            title="Start date",
            description=(
                "Starting time for retrieving the list of app names "
                "within the specified time range.\n\n Format : YYYY-mm-dd HH:MM:SS "
                "\n\n Default value : current time minus 4 hours"
            ),
            alias="start-date",
        ),
    ],
    end_date: Annotated[
        datetime | None,
        Query(
            default_factory=get_end_time,
            title="End date",
            description=(
                "Ending time for retrieving the list of app names "
                "within the specified time range.\n\n Format : YYYY-mm-dd HH:MM:SS "
                "\n\n Default value : current time minus 1 hour"
            ),
            alias="end-date",
        ),
    ],
    sampling_rate: Annotated[
        SamplingRate,
        Query(title="Sampling rate", description="Sampling rate", alias="sampling"),
    ] = SamplingRate.THIRTY_MINUTES,
    selected_apps: Annotated[
        list[str] | None,
        Query(
            title="Selected Apps",
            description=(
                "Selected compute_resource for which a list of pods will be retrieved "
                "at the specified time interval"
            ),
            alias="app",
        ),
    ] = None,
    paas: Annotated[
        list[str],
        Query(
            title="Platform as a Service (PaaS)",
            description="Platform as a Service (PaaS) to be used for the selected compute_resource.",
            alias="paas",
        ),
    ] = ...,
    namespace: Annotated[
        list[str] | None,
        Query(
            title="Namespace",
            description="Namespace to be used for the selected paas or app",
            alias="namespace",
        ),
    ] = None,
    emission_breakdown_at_pod_level: bool = Query(
        default=False,
        title="Emission Breakdown",
        description="If True, metrics are computed at the pod level",
        alias="emission_breakdown",
    ),
) -> list[ComputeResource]:
    """
    Runs the carbon engine for each pod of selected compute resource and retrieves computed data (such as KWh,
    gCO2, etc.)

    Args:

        request (Request): The incoming request.

        start_date (datetime, optional): Starting time for the engine.

        end_date (datetime, optional): Ending time for the engine.

        sampling_rate (str, optional): Sampling rate.

        selected_apps (List[str], optional): Selected compute_resource for which a list of pods will be retrieved.

        paas (List[str]): Cluster name (stack value).

        namespace (List[str], optional): Application's namespace.

        emission_breakdown_at_pod_level (bool): Flag for the computation at the pod level.

    Returns:

        List[Pod]: Computed data for each pod of selected compute_resource at application level.

        Dict[str, Dict[str, Dict[str, List[Pod]]]]: Computed data for each pod of selected cluster, app and namespace
        at pod level.
    """
    # Validate query parameters
    allowed_params = {
        "start_date",
        "end_date",
        "sampling_rate",
        "start-date",
        "end-date",
        "sampling",
        "selected_apps",
        "app",
        "paas",
        "namespace",
        "emission_breakdown",
    }

    try:
        validate_query_parameters(request, allowed_params)
    except ValidationError:
        raise

    # Validate date range
    if start_date and end_date and start_date >= end_date:
        logger.error(
            "Invalid date range: start_date=%s, end_date=%s", start_date, end_date
        )
        raise DateValidationError(
            ErrorCode.VALIDATION_INVALID_DATE_RANGE,
            "date_range",
            f"start: {start_date}, end: {end_date}",
        )

    try:
        logger.info(
            "Running engine for resources - start: %s, end: %s, sampling: %s, apps: %s, paas: %s, namespaces: %s",
            start_date,
            end_date,
            sampling_rate,
            selected_apps,
            paas,
            namespace,
        )

        # Retrieve telemetry data
        compute_resources: list[
            ComputeResource
        ] = await ArgosService().retrieve_telemetry_data(
            start_date, end_date, sampling_rate, paas, selected_apps, namespace
        )

        if not compute_resources:
            logger.warning("No compute resources found for the given parameters")
            return []

        # Convert sampling rate and run carbon engine
        step_seconds = convert_to_seconds(sampling_rate.value)
        # ioc_key is embedded for now, it will be included to the request in the future for the model selection
        carbon_service = ioc_util.resolve(CarbonService, "IFApp", step_seconds)

        result = await carbon_service.run_engine(
            compute_resources, emission_breakdown_at_pod_level
        )

        logger.info("Engine execution completed successfully")
        return result

    except (DataFetchError, ValidationError, DateValidationError):
        raise
    except Exception as e:
        logger.exception("Unexpected error running carbon engine")
        raise ComputationError(
            ErrorCode.COMPUTATION_FAILED,
            operation="carbon engine execution",
            details=str(e),
        ) from e


# Improvement: Controller calls dependency, dependency calls service, service calls crud.
