"""
VM Storage Embodied Emissions model for IF
"""

from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)


class MVmStorage(ModelUtilities):
    """
    Model for storage embodied emissions calculation.
    Input: storage size in GB
    Output: emissions in gCO2e
    """

    def __init__(self):
        config = {
            "input-parameters": [
                "storage/requested",
                "storage/embodied-coefficient",
                "duration/seconds",
            ],  # in GB
            "output-parameter": " = 'storage-embodied' / 126230400",  # in gCO2e
        }
        output_metadata = [
            Metadata(
                "storage-embodied", "gCO2e", "Storage embodied emissions", "sum", "sum"
            )
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)
