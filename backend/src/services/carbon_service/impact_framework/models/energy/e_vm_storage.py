"""
VM Storage Energy Consumption model made with IF builtins
"""

from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)


class EVmStorage(ModelUtilities):
    """
    Concrete class for the Storage Energy Consumption model made with IF builtins.
    Calculates energy consumption based on storage power and duration.

    Input units:
    - power: kW
    - duration: seconds
    Output units:
    - energy: kWh
    """

    def __init__(self):
        config = {
            "input-parameters": ["storage/power", "duration/seconds"],
            "output-parameter": " = 'storage/energy' / 3600",
        }
        output_metadata = [
            Metadata(
                "storage/energy", "kWh", "Storage energy consumption", "sum", "sum"
            )
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)
