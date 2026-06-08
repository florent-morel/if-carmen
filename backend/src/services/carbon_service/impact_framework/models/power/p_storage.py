"""
Storage Services Power Consumption model made with IF builtins based on disk type (SSD/HDD)
"""

from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)


class PStorage(ModelUtilities):
    """
    Concrete class for the Storage Power Consumption model made with IF builtins.

    Input units:
    - storage_size: GB
    Output units:
    - power: kW
    """

    def __init__(self, provider_config: AbstractProviderConfig | None = None):
        self.provider_config = provider_config
        config = {
            "input-parameters": ["storage/requested", "power/coefficient"],
            "output-parameter": "storage/power",  # in kW
        }
        output_metadata = [
            Metadata("storage/power", "kW", "Storage Power consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)

    def fill_inputs(self, storage_resource: StorageResource, time_index: int):
        """
        Fills the storage input values from the storage resource.

        Args:
            storage_resource: The storage resource containing data
            time_index: The time index for which to get the data

        Returns:
            Dict containing storage input in GB and the power coefficient based on storage type
        """
        from backend.src.core.yaml_config_loader import config as app_config

        global_ratios = (
            app_config.carbon_values_config.get_storage_electricity_ratios()
            if app_config.carbon_values_config
            else None
        ) or {}
        provider_ratios = (
            (self.provider_config.get_storage_electricity_ratios() or {})
            if self.provider_config
            else {}
        )
        # Provider-specific values override the global defaults.
        ratios = {**global_ratios, **provider_ratios}
        storage_type = storage_resource.storage_type.lower()
        power_coefficient = ratios.get(storage_type, ratios.get("unknown"))
        if power_coefficient is None:
            raise ValueError(
                f"No electricity ratio for storage type '{storage_type}' and no"
                " 'unknown' fallback found. Add an 'unknown' entry under"
                " 'storage_electricity_ratios' in carbon_values.yaml."
            )

        replication_factors = (
            (self.provider_config.get_storage_replication_factors() or {})
            if self.provider_config
            else {}
        )
        replication_factor = replication_factors.get(
            storage_resource.replication_type.lower(), 1
        )

        effective_size = storage_resource.size_gb * replication_factor

        return {
            "storage/requested": effective_size,
            "power/coefficient": power_coefficient,
        }
