"""
sci-e model of IF
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
    IF_INPUT_ENERGY,
    IF_INPUT_ENERGY_TXT,
    IF_INPUT_ENERGY_KWH,
    IF_INPUT_CPU_SLASH_ENERGY,
    IF_INPUT_MEMORY_SLASH_ENERGY,
    IF_INPUT_STORAGE_SLASH_ENERGY,
    IF_INPUT_SUM,
)

class SciE(ModelUtilities):
    """
    Abstract class for sci-e model of IF, indicating it shouldn't be instantiated directly
    without a subclass providing an implementation of fill_inputs.
    """

    def __init__(self):
        config = {
            IF_INPUT_INPUT_PARAMETERS: [IF_INPUT_CPU_SLASH_ENERGY, IF_INPUT_MEMORY_SLASH_ENERGY, IF_INPUT_STORAGE_SLASH_ENERGY],
            IF_INPUT_OUTPUT_PARAMETER: IF_INPUT_ENERGY,
        }
        output_metadata = [
            Metadata(IF_INPUT_ENERGY, IF_INPUT_ENERGY_KWH, IF_INPUT_ENERGY_TXT, IF_INPUT_SUM, IF_INPUT_SUM)
        ]
        super().__init__("builtin", "Sum", config, output_metadata)
