"""
sci model of IF
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
    IF_INPUT_CARBON_TXT,
    IF_INPUT_CARBON_EMBODIED,
    IF_INPUT_CARBON_EMBODIED_TXT,
    IF_INPUT_CARBON_OPERATIONAL,
    IF_INPUT_CARBON_OPERATIONAL_TXT,
    IF_INPUT_CARBON_GCO2,
    IF_INPUT_SUM,
)


class Sci(ModelUtilities):
    """
    Concrete class for the SCI model of IF
    """

    def __init__(self):
        config = {
            IF_INPUT_INPUT_PARAMETERS: [IF_INPUT_CARBON_OPERATIONAL, IF_INPUT_CARBON_EMBODIED],
            IF_INPUT_OUTPUT_PARAMETER: IF_INPUT_CARBON,
        }
        input_metadata = [
            Metadata(
                IF_INPUT_CARBON_OPERATIONAL,
                IF_INPUT_CARBON_GCO2,
                IF_INPUT_CARBON_OPERATIONAL_TXT,
                IF_INPUT_SUM,
                IF_INPUT_SUM,
            ),
            Metadata(
                IF_INPUT_CARBON_EMBODIED, IF_INPUT_CARBON_GCO2, IF_INPUT_CARBON_EMBODIED_TXT, IF_INPUT_SUM, IF_INPUT_SUM
            ),
        ]
        output_metadata = [
            Metadata(IF_INPUT_CARBON, IF_INPUT_CARBON_GCO2, IF_INPUT_CARBON_TXT, IF_INPUT_SUM, IF_INPUT_SUM)
        ]
        super().__init__("builtin", "Sum", config, output_metadata, input_metadata)
