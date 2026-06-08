"""
sci-o model of IF
"""
import logging

from backend.src.schemas.compute_resource import ComputeResource
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.common.constants import (
    IF_INPUT_GRID_CARBON_INTENSITY,
)
logger = logging.getLogger(__name__)


class SciO(ModelUtilities):
    """
    Concrete class for the Sci-O model of IF
    """

    def __init__(self):
        super().__init__('"@grnsft/if-plugins"', "SciO")

    # IMP: Cluster and VM specific not time!
    @staticmethod
    def fill_inputs(compute_resource: ComputeResource, time_index: int):
        """
        Fills the time point specific input values.
        """
        carbon_intensity = compute_resource.carbon_intensity
        logger.debug(f"{IF_INPUT_GRID_CARBON_INTENSITY}: {carbon_intensity}")
        return {IF_INPUT_GRID_CARBON_INTENSITY: carbon_intensity}
