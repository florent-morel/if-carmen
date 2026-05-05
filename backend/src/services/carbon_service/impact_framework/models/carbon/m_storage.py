"""
Storage Services Embodied Emissions model for IF
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


class MStorage(ModelUtilities):
    """
    Model for storage embodied emissions calculation.
    Input: storage size in GB
    Output: emissions in gCO2e
    """

    def __init__(self, provider_config: AbstractProviderConfig | None = None):
        # provider_config kept for API compatibility; embodied coefficients come
        # from carbon_values.yaml via config.carbon_intensity_config.
        self.provider_config = provider_config
        config = {
            "input-parameters": [
                "storage/requested",
                "storage/embodied-coefficient",
                "duration/seconds",
            ],  # in GB
            "output-parameter": " = 'carbon-embodied' / 126230400",  # in gCO2e
        }
        output_metadata = [
            Metadata(
                "carbon-embodied", "gCO2e", "Storage embodied emissions", "sum", "sum"
            )
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)

    def fill_inputs(self, storage_resource: StorageResource, time_index: int):
        """
        Fills the storage embodied inputs based on storage type.
        Coefficients are read from carbon_values.yaml (config.carbon_intensity_config).
        """
        from backend.src.core.yaml_config_loader import config as app_config

        embodied_dict = (
            app_config.carbon_intensity_config.get_storage_embodied()
            if app_config.carbon_intensity_config
            else None
        ) or {}
        storage_type = storage_resource.storage_type.lower()
        embodied_coefficient = embodied_dict.get(
            storage_type, embodied_dict.get("unknown")
        )
        if embodied_coefficient is None:
            raise ValueError(
                f"No storage embodied coefficient for type '{storage_type}' and no 'unknown' "
                "fallback defined in carbon_values.yaml. Add an 'unknown' entry under "
                "'storage_embodied'."
            )

        return {"storage/embodied-coefficient": embodied_coefficient}
