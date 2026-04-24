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

    def __init__(self):
        # TODO: Instantiate provider config
        self.provider_config: AbstractProviderConfig
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

    # @staticmethod
    # TODO: check why this was static
    def fill_inputs(self, storage_resource: StorageResource, time_index: int):
        """
        Fills the storage embodied inputs based on storage type.
        """
        # Get the embodied coefficient based on storage type
        embodied_storage_dict = self.provider_config.get_storage_embodied()
        embodied_coefficient = embodied_storage_dict.get(
            storage_resource.storage_type.upper(),
            embodied_storage_dict.get("UNKNOWN"),
        )

        return {"storage/embodied-coefficient": embodied_coefficient}
