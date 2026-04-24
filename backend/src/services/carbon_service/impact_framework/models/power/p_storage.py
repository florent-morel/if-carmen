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

    def __init__(self):
        # TODO: Instantiate provider config
        self.provider_config: AbstractProviderConfig
        config = {
            "input-parameters": ["storage/requested", "power/coefficient"],
            "output-parameter": "storage/power",  # in kW
        }
        output_metadata = [
            Metadata("storage/power", "kW", "Storage Power consumption", "sum", "sum")
        ]
        super().__init__("builtin", "Multiply", config, output_metadata)

    # @staticmethod
    # TODO: check why this was static
    def fill_inputs(self, storage_resource: StorageResource, time_index: int):
        """
        Fills the storage input values from the storage resource.

        Args:
            storage_resource: The storage resource containing data
            time_index: The time index for which to get the data

        Returns:
            Dict containing storage input in GB and the power coefficient based on storage type
        """
        # Get the power coefficient based on storage type
            # TODO: check if dict.get() works
        ratio = self.provider_config.get_electricity_ratios().get("UNKNOWN"),  # kW/GB
        power_coefficient = self.provider_config.get_electricity_ratios().get(
            storage_resource.storage_type.upper(),
            ratio,
        )

        # Get the replication factor
            # TODO: check if dict.get() works
        replication_factor = self.provider_config.get_storage_replication_factors().get(
            storage_resource.replication_type.upper(), 1
        )

        # Calculate the effective storage size (considering replication)
        effective_size = storage_resource.size_gb * replication_factor

        return {
            "storage/requested": effective_size,
            "power/coefficient": power_coefficient,
        }
