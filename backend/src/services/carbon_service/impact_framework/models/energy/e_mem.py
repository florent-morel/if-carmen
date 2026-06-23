"""
Memory Energy Consumption model made with IF builtins
"""

from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)


class EMem(ModelUtilities):
    """
    Concrete class for the Memory Energy Consumption model made with IF builtins
    """

    def __init__(self):
        config = {
            "input-parameters": ["memory/power", "duration/seconds"],
            "output-parameter": " = 'memory/energy' / 3600",
        }
        output_metadata = [
            Metadata("memory/energy", "kWh", "Memory energy consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)
