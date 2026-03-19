"""
Defines the abstract base class HardwareModel for implementing hardware specific carbon models in the Amadeus Service.
All specific hardware models should inherit from this class.
"""

from abc import ABC, abstractmethod
from backend.src.common import constants


class HardwareModel(ABC):
    """
    This class is a base class for amadeus model carbon components.
    All components should inherit from this class, since there are
    some common methods.
    """

    def __init__(self, time_interval):
        self.time_interval = time_interval

    @abstractmethod
    def get_power_consumption(self, component):
        """
        Returns the power consumption, in kW.
        """
        raise NotImplementedError("Subclasses must implement get_power_consumption")

    def __get_component_with_energy_consumption(self, component):
        """
        Returns the component with the energy consumption, in kWh.
        """
        power_consumed = self.get_power_consumption(component)
        component.energy_consumed = [
            power_consumed[i] * self.time_interval / 3600
            for i in range(len(power_consumed))
        ]

        return component

    def get_component_with_carbon_emissions(self, component):
        """
        Returns the component with the carbon emitted, in gCO2e.
        """
        component = self.__get_component_with_energy_consumption(component)
        component.carbon_emitted = [
            component.energy_consumed[i] * constants.CARBON_INTENSITY_EUROPE
            for i in range(len(component.energy_consumed))
        ]

        return component
