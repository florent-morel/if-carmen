"""
ECpu model that computes the energy consumption of the CPU
"""

from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)


class ECpu(ModelUtilities):
    """
    Concrete class for the CPU energy consumption model made with IF builtins
    """

    def __init__(self):
        config = {
            "input-parameters": ["cpu/power", "duration/seconds"],
            "output-parameter": " = 'cpu/energy' / 3600",
        }
        output_metadata = [
            Metadata("cpu/energy", "kWh", "CPU energy consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)
