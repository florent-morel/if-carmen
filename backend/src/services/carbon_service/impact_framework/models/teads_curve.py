"""
CPU model of IF
"""
import logging

from backend.src.schemas.compute_resource import ComputeResource
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.common.constants import (
    IF_INPUT_TIMESTAMP,
    IF_INPUT_CPU_UTILIZATION,
    IF_INPUT_INPUT_PARAMETER,
    IF_INPUT_OUTPUT_PARAMETER,
    IF_INPUT_CPU_TDP_RATIO,
)
logger = logging.getLogger(__name__)

class TeadsCurve(ModelUtilities):
    """
    Concrete class for teads-curve model of IF to be used in CPU energy calculation
    """

    def __init__(self):
        config = {
            "method": "linear",
            # teads-curve data points
            # TODO: Magic numbers representing the curve? To be moved to carbon_values.yaml
            "x": [0, 10, 50, 100],  # x-axis represents cpu/utilization (in %)
            "y": [0.12, 0.32, 0.75, 1.02],  # y-axis represents the tdp ratio (no unit)
            IF_INPUT_INPUT_PARAMETER: IF_INPUT_CPU_UTILIZATION,
            IF_INPUT_OUTPUT_PARAMETER: IF_INPUT_CPU_TDP_RATIO,
        }
        super().__init__("builtin", "Interpolation", config)

    @staticmethod
    def fill_inputs(compute_resource: ComputeResource, time_index: int):
        """
        Fills the teads-curve input val. from the pod
        """
        timestamp = compute_resource.time_points[time_index]
        logger.debug(f"{IF_INPUT_TIMESTAMP}: {timestamp}")
        cpu_utilization = min(compute_resource.cpu_util[time_index] * 100, 100)
        logger.debug(f"{IF_INPUT_CPU_UTILIZATION}: {cpu_utilization}")
        return {
            IF_INPUT_TIMESTAMP: timestamp,
            IF_INPUT_CPU_UTILIZATION: cpu_utilization,
        }
