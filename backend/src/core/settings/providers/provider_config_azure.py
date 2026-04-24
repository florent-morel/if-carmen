
import logging


from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)

logger = logging.getLogger(__name__)


class Provider_Config_Azure(AbstractProviderConfig):
    """
    Configuration class for Azure Provider.
    """

    def __init__(self):
        self.pue: float
        self.electricity_ratios: dict[str: float]
        self.storage_embodied: dict[str: int]
        self.storage_replication_factors: dict[str: int]
        self.disk_sku_size_mapping: dict[str: int]

    def get_pue(self) -> float | None:
        return self.pue

    def get_electricity_ratios(self) -> dict[str: float] | None:
        return self.electricity_ratios

    def get_storage_replication_factors(self) -> dict[str: int] | None:
        return self.storage_replication_factors
