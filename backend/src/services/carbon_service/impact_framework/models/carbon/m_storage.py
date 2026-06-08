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

from backend.src.common.constants import (
    IF_INPUT_INPUT_PARAMETERS,
    IF_INPUT_OUTPUT_PARAMETER,
    IF_INPUT_CARBON_EMBODIED,
    IF_INPUT_COMPUTE_ENERGY,
    IF_INPUT_COMPUTE_EMBODIED,
    IF_INPUT_COMPUTE_COST,
    IF_INPUT_STORAGE_ENERGY,
    IF_INPUT_STORAGE_EMBODIED,
    IF_INPUT_STORAGE_COST,
    IF_INPUT_COST,
    IF_INPUT_MISC_SERVICES_ENERGY,
    IF_INPUT_MISC_SERVICES_ENERGY_TXT,
    IF_INPUT_MISC_SERVICES_OPERATIONAL,
    IF_INPUT_MISC_SERVICES_EMBODIED,
    IF_INPUT_CARBON_INTENSITY,
    IF_INPUT_SUM,
    IF_INPUT_ENERGY_KWH,
    IF_INPUT_CARBON_GCO2,
    IF_INPUT_MISC_SERVICES_CAPEX,
    IF_INPUT_MISC_SERVICES_OPEX,
    IF_INPUT_TIMESTAMP,
    IF_INPUT_STORAGE_SLASH_REQUESTED,
    IF_INPUT_STORAGE_SLASH_EMBODIED,
    IF_INPUT_DURATION_SLASH_SECONDS,
    EXPECTED_LIFESPAN,
    IF_INPUT_STORAGE_EMBODIED_TXT,
)

class MStorage(ModelUtilities):
    """
    Model for storage embodied emissions calculation.
    Input: storage size in GB
    Output: emissions in gCO2e
    """

    def __init__(self, provider_config: AbstractProviderConfig | None = None):
        # provider_config kept for API compatibility; embodied coefficients come
        # from carbon_values.yaml via config.carbon_values_config.
        self.provider_config = provider_config
        config = {
            IF_INPUT_INPUT_PARAMETERS: [
                IF_INPUT_STORAGE_SLASH_REQUESTED,
                IF_INPUT_STORAGE_SLASH_EMBODIED,
                IF_INPUT_DURATION_SLASH_SECONDS,
            ],  # in GB
            IF_INPUT_OUTPUT_PARAMETER: f" = '{IF_INPUT_CARBON_EMBODIED}' / {EXPECTED_LIFESPAN}",  # in gCO2e
        }
        output_metadata = [
            Metadata(
                IF_INPUT_CARBON_EMBODIED, IF_INPUT_CARBON_GCO2, IF_INPUT_STORAGE_EMBODIED_TXT, IF_INPUT_SUM, IF_INPUT_SUM
            )
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)

    def fill_inputs(self, storage_resource: StorageResource, time_index: int):
        """
        Fills the storage embodied inputs based on storage type.
        Coefficients are read from carbon_values.yaml (config.carbon_values_config).
        """
        from backend.src.core.yaml_config_loader import config as app_config

        embodied_dict = (
            app_config.carbon_values_config.get_storage_embodied()
            if app_config.carbon_values_config
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

        return {IF_INPUT_STORAGE_SLASH_EMBODIED: embodied_coefficient}
