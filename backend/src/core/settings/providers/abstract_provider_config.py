import logging
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class AbstractProviderConfig(BaseSettings):
    """
    Configuration class for all supported providers.

    All fields are optional — a provider YAML only needs to supply what it supports.
    Adding a new provider requires only a new directory and YAML file under
    config/cloud_providers/<name>/<name>.yaml; no code changes are needed.
    """

    pue: float | None = None
    electricity_ratios: dict[str, float] | None = None
    storage_electricity_ratios: dict[str, float] | None = None
    storage_replication_factors: dict[str, int] | None = None
    disk_sku_size_mapping: dict[str, int] | None = None
    regions: dict[str, str] | None = None
    zone_aliases: dict[str, str] | None = None

    def get_pue(self) -> float | None:
        return self.pue

    def get_electricity_ratios(self) -> dict[str, float] | None:
        return self.electricity_ratios

    def get_storage_electricity_ratios(self) -> dict[str, float] | None:
        return self.storage_electricity_ratios

    def get_storage_replication_factors(self) -> dict[str, int] | None:
        return self.storage_replication_factors

    def get_disk_sku_size_mapping(self) -> dict[str, int] | None:
        return self.disk_sku_size_mapping

    def get_regions(self) -> dict[str, str] | None:
        return self.regions

    def get_zone_aliases(self) -> dict[str, str] | None:
        return self.zone_aliases
