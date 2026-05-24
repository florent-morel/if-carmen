import logging
from pydantic import BaseModel
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class CountryCarbonIntensity(BaseModel):
    carbon_intensity: int


class DefaultMiscServicesConstants(BaseModel):
    """Default fallback values for misc services modelling when no compute/storage results are available."""

    compute_energy: float = 0.0
    compute_embodied: float = 0.0
    compute_cost: float = 0.0
    storage_energy: float = 0.0
    storage_embodied: float = 0.0
    storage_cost: float = 0.0


class CarbonIntensityConfig(BaseSettings):
    """
    TODO: update description
    Configuration class for carbon intensity per location.
    Loaded from carbon_intensity.yaml.
    """

    carbon_intensity_by_location: dict[str, CountryCarbonIntensity] = {}
    storage_embodied: dict[str, int] | None = None
    storage_electricity_ratios: dict[str, float] | None = None
    default_misc_services_constants: DefaultMiscServicesConstants = (
        DefaultMiscServicesConstants()
    )

    def get_known_locations(self) -> set[str]:
        return set(self.carbon_intensity_by_location.keys())

    def get_ci_for_location(self, location: str, default: int) -> int:
        entry = self.carbon_intensity_by_location.get(location)
        return entry.carbon_intensity if entry else default

    def get_storage_embodied(self) -> dict[str, int] | None:
        return self.storage_embodied
    
    def get_storage_electricity_ratios(self) -> dict[str, float] | None:
        return self.storage_electricity_ratios
