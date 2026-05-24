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
        from backend.src.core.yaml_config_loader import config as app_config

        global_ratios = (
            app_config.carbon_intensity_config.get_storage_electricity_ratios()
            if app_config.carbon_intensity_config
            else None
        ) or {}
        provider_ratios = (
            (provider_config.get_storage_electricity_ratios() or {}) if provider_config else {}
        )
        # Provider-specific values override the global defaults.
        ratios = {**global_ratios, **provider_ratios}
        coefficient = ratios.get("unknown")
        if coefficient is None:
            raise ValueError(
                "No 'unknown' electricity ratio found. Add an 'unknown' entry"
                " under 'storage_electricity_ratios' in carbon_values.yaml."
            )
        config = {
            "input-parameter": "storage/requested",  # in GB
            "coefficient": coefficient,  # kW/GB
            "output-parameter": "storage/power",  # in kW
        }
        output_metadata = [
            Metadata("storage/power", "kW", "Storage Power consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Coefficient", config, output_metadata)

    @staticmethod
    def fill_inputs(virtual_machine: VirtualMachine, time_index: int):
        """
        Fills the storage input values from the virtual machine.

        Args:
            virtual_machine: The virtual machine containing storage data
            time_index: The time index for which to get the data

        Returns:
            Dict containing storage input in GB
        """
        # Storage size in GB
        storage = virtual_machine.storage_size[time_index]
        return {"storage/requested": storage}
