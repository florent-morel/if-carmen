"""
This module defines the Amadeus service class, which implements the CarbonService interface.
It provides functionality to compute carbon and energy metrics for components using Amadeus hardware models.
"""

from abc import ABC
from copy import deepcopy

from backend.src.services.carbon_service.amadeus.hardware_models.cpu_model import (
    CpuModel,
)
from backend.src.services.carbon_service.amadeus.hardware_models.memory_model import (
    MemoryModel,
)
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.schemas.pod import Pod


class AmadeusService(ABC, CarbonService):
    """
    This class implements the CarbonService interface and provides functionality to compute
    carbon and energy metrics for components using Amadeus hardware models.
    Attributes:
        cpu_model: Instance of CpuModel for CPU-related computations.
        memory_model: Instance of MemoryModel for memory-related computations.
    """

    def __init__(self, time_interval):
        self.cpu_model = CpuModel(time_interval)
        self.memory_model = MemoryModel(time_interval)

    async def run_engine(self, components, aggregation_level=None):
        """
        This method computes the carbon and energy metrics for the given components over the specified time interval by
        using Amadeus hardware models.

        Args:
            components: List of components for which metrics are to be computed.
            aggregation_level: Aggregation level for the computation, can be "app", "component"

        Returns:
            List[Component]: List of components with updated energy consumption and carbon emissions' metrics.
        """

        new_components = []

        for component in components:
            component_cpu = self.cpu_model.get_component_with_carbon_emissions(
                deepcopy(component)
            )
            component_memory = self.memory_model.get_component_with_carbon_emissions(
                deepcopy(component)
            )

            component_sum = component_cpu + component_memory

            new_components.append(component_sum)

        if aggregation_level == "app":
            apps = {}
            for component in new_components:
                if component.application not in apps:
                    apps[component.application] = []
                apps[component.application].append(deepcopy(component))

            new_components = []
            for app, app_components in apps.items():
                new_component = Pod()
                new_component.application = app
                new_component.name = "all"
                new_component.paas = "all"
                new_component.partition = "all"
                new_component.environment = "all"
                new_component.instance = "all"
                new_component.energy_consumed = [
                    sum(sum(c.energy_consumed) for c in app_components)
                ]
                new_component.carbon_emitted = [
                    sum(sum(c.carbon_emitted) for c in app_components)
                ]

                new_components.append(new_component)

        return new_components
