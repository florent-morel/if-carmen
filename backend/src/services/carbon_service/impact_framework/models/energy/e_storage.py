"""
Storage Services Energy Consumption model made with IF builtins
"""

from backend.src.common.constants import DAILY_SECONDS

from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)


class EStorage(ModelUtilities):
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
            "output-parameter": " = 'energy' / 3600",
        }
        output_metadata = [
            Metadata("energy", "kWh", "Storage energy consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)

    @staticmethod
    def fill_inputs(storage_resource: StorageResource, time_index: int):
        """
        Fills the storage energy input values from the storage resource.

        Returns:
            Dict containing duration in seconds for energy calculation
        """
        if time_index < len(storage_resource.duration_seconds):
            duration_seconds = int(storage_resource.duration_seconds[time_index])
        else:
            duration_seconds = DAILY_SECONDS
        return {"duration/seconds": duration_seconds}
