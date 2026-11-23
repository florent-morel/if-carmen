"""
VM Storage Power Consumption model made with IF builtins based on disk type (SSD/HDD)
"""

from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)
from backend.src.core.yaml_config_loader import config


class PVmStorage(ModelUtilities):
    """
    Concrete class for the Storage Power Consumption model made with IF builtins.

    Input units:
    - storage_size: GB
    Output units:
    - power: kW
    """

    def __init__(self, provider_config: AbstractProviderConfig | None = None):
        self.provider_config = provider_config

        global_ratios = (
            config.carbon_values_config.storage_electricity_ratios or {}
            if config.carbon_values_config
            else {}
        )
        provider_ratios = (
            provider_config.storage_electricity_ratios or {}
            if provider_config
            else {}
        )
        ratios = {**global_ratios, **provider_ratios}
        coefficient = ratios.get("unknown")
        if coefficient is None:
            raise ValueError(
                "Missing 'unknown' entry under storage_electricity_ratios in carbon_values.yaml."
            )
        model_config = {
            "input-parameter": "storage/requested",  # in GB
            "coefficient": coefficient,  # kW/GB
            "output-parameter": "storage/power",  # in kW
        }
        output_metadata = [
            Metadata("storage/power", "kW", "Storage Power consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Coefficient", model_config, output_metadata)

    @staticmethod
    def fill_inputs(virtual_machine: VirtualMachine, time_index: int):
        """Return requested VM storage size (GB) for the given time index."""
        storage = virtual_machine.storage_size[time_index]
        return {"storage/requested": storage}
