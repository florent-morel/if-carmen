"""
This module implements the amadeus memory model.
"""

# pylint: disable=E0401# pylint: disable=E0401
from backend.src.common import constants
from backend.src.services.carbon_service.amadeus.hardware_models.hardware_model import (
    HardwareModel,
)


class MemoryModel(HardwareModel):
    """
    This class implements the memory model.
    """

    def get_power_consumption(self, component):
        """
        Returns the power consumption, in kW.
        """
        power_consumed = [
            component.requested_memory[i]
            * constants.MEMORY_ELECTRICITY_RATIO_AZURE
            * pow(10, -12)
            for i in range(len(component.requested_memory))
        ]

        return power_consumed
