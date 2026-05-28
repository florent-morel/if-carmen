"""
Energy model in which sci-e value is multiplied by PUE value
"""

import logging

from backend.src.schemas.compute_resource import ComputeResource
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.common.constants import (
    IF_INPUT_INPUT_PARAMETERS,
    IF_INPUT_OUTPUT_PARAMETER,
    IF_INPUT_ENERGY,
    IF_INPUT_ENERGY_KWH,
    IF_INPUT_PUE,
)

logger = logging.getLogger(__name__)


class SciEPue(ModelUtilities):
    """
    Concrete class for the Energy model with Power Usage Effectiveness value
    """

    def __init__(self):
        config = {IF_INPUT_INPUT_PARAMETERS: [IF_INPUT_ENERGY, IF_INPUT_PUE], IF_INPUT_OUTPUT_PARAMETER: IF_INPUT_ENERGY}
        output_metadata = [
            Metadata(
                IF_INPUT_ENERGY, IF_INPUT_ENERGY_KWH, "Energy consumption multiplied by PUE", "sum", "sum"
            )
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)

    @staticmethod
    def fill_inputs(compute_resource: ComputeResource, time_index: int):
        """
        Fills the time point specific input values.
        """
        pue = compute_resource.pue
        logger.info(f"{IF_INPUT_PUE}: {pue}")
        return {IF_INPUT_PUE: pue}
