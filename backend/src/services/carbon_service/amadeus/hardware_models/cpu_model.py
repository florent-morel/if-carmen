"""
This module implements the amadeus CPU model.
"""

# pylint: disable=E0401
from backend.src.common import constants
from backend.src.services.carbon_service.amadeus.hardware_models.hardware_model import (
    HardwareModel,
)


class CpuModel(HardwareModel):
    """
    This class implements the CPU model.
    """

    @staticmethod
    def __get_cores_utilization(component):
        """
        Returns the  percentage of cores used.
        """
        core_util = [
            (
                component.used_cpu[i] / component.requested_cpu[i]
                if component.requested_cpu[i] != 0
                else 0
            )
            for i in range(len(component.used_cpu))
        ]

        return core_util

    def get_power_consumption(self, component):
        """
        Returns the power consumption, in kW.
        """
        cpu_max = constants.CPU_MAX_ELECTRICITY_RATIO_AZURE
        cpu_min = constants.CPU_MIN_ELECTRICITY_RATIO_AZURE
        core_util = self.__get_cores_utilization(component)

        power_consumed = [
            pow(10, -3)
            * (core_util[i] * (cpu_max - cpu_min) + cpu_min)
            * float(component.requested_cpu[i])
            for i in range(len(component.requested_cpu))
        ]

        return power_consumed
