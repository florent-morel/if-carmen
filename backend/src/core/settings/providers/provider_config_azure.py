import logging


from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)

logger = logging.getLogger(__name__)


class Provider_Config_Azure(AbstractProviderConfig):
    """
    Configuration class for Azure Provider.
    """

    def get_pue(self) -> float | None:
        return self.pue

    def get_electricity_ratios(self) -> dict[str, float] | None:
        return self.electricity_ratios

    def get_storage_replication_factors(self) -> dict[str, int] | None:
        return self.storage_replication_factors

    def get_storage_embodied(self) -> dict[str, int] | None:
        return self.storage_embodied

    def get_disk_sku_size_mapping(self) -> dict[str, int] | None:
        return self.disk_sku_size_mapping

    def get_regions(self) -> dict[str, str] | None:
        return self.regions
