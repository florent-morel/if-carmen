from pydantic_settings import BaseSettings


class AbstractProviderConfig(BaseSettings):
    """
    Configuration schema loaded from a provider YAML file under
    CARMEN_PROVIDER_CONFIG_FILEPATH. All fields are optional.
    """

    pue: float | None = None
    electricity_ratios: dict[str, float] | None = None
    storage_electricity_ratios: dict[str, float] | None = None
    storage_replication_factors: dict[str, int] | None = None
    disk_sku_size_mapping: dict[str, int] | None = None
    regions: dict[str, str] | None = None

    def get_pue(self) -> float | None:
        return self.pue

    def get_cpu_max(self) -> float | None:
        """Return the maximum per-core TDP (W/core) for this provider, or None if not configured."""
        if self.electricity_ratios is None:
            return None
        return self.electricity_ratios.get("cpu_max")
