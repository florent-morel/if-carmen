"""
sci-m model of IF
"""

from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.common.constants import (
    IF_INPUT_INPUT_PARAMETERS,
    IF_INPUT_OUTPUT_PARAMETER,
    IF_INPUT_CARBON,
    IF_INPUT_CARBON_EMBODIED,
    IF_INPUT_CARBON_EMBODIED_TXT,
    IF_INPUT_CARBON_GCO2,
    IF_INPUT_STORAGE_EMBODIED,
    IF_INPUT_SUM,
)


class SciM(ModelUtilities):
    """
    Adds the sci-m-cpu and the storage embodied emissions for the VMs
    """

    def __init__(self):
        config = {
            IF_INPUT_INPUT_PARAMETERS: [IF_INPUT_CARBON_EMBODIED, IF_INPUT_STORAGE_EMBODIED],
            IF_INPUT_OUTPUT_PARAMETER: IF_INPUT_CARBON_EMBODIED,
        }
        output_metadata = [
            Metadata(IF_INPUT_CARBON, IF_INPUT_CARBON_GCO2, IF_INPUT_CARBON_EMBODIED_TXT, IF_INPUT_SUM, IF_INPUT_SUM)
        ]
        super().__init__("builtin", "Sum", config, output_metadata)
