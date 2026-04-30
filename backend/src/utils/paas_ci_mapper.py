"""
This script is used to map PaaS value retrieved from Thanos to their respective azure regions,
and used to calculate carbon intensity depending on their region and time range by using CAW.
"""

from functools import lru_cache
from backend.src.utils.helpers import remove_unnecessary
from backend.src.common.constants import ZONES
from backend.src.core.yaml_config_loader import config


class PaasCiMapper:
    """
    Provides methods to calculate carbon intensity based on PaaS values and time range,
    and to map PaaS values to their respective regions.
    """

    @staticmethod
    def __extract_zone_from_paas(paas: str) -> str:
        """
        Extracts a zone from a given PaaS value.
        :param paas: The paas value string from which to extract the location.
        :return: The extracted location or None if no match is found.
        """
        # Check impact_framework direct PaaS value matches
        direct_loc = remove_unnecessary(paas.upper())
        if direct_loc in ZONES:
            return ZONES[direct_loc]

        # Check for location between hyphens
        parts = paas.upper().split("-")
        for part in parts:
            loc = remove_unnecessary(part)
            if loc in ZONES:
                return ZONES[loc]

        # No match found - return None
        return None

    @staticmethod
    @lru_cache(1000)  # we have ~20 different azure regions
    def calculate_ci(zone: str) -> float:
        ci_config = config.carbon_intensity_config
        default_ci = config.defaults.carbon_intensity
        for provider_config in config.provider_configs.values():
            regions = provider_config.get_regions()
            if regions and zone in regions:
                country = regions[zone]
                return float(ci_config.get_ci_for_location(country, default_ci))
        return float(default_ci)

    @staticmethod
    def get_ci_from_paas(paas: str) -> float:
        zone = PaasCiMapper.__extract_zone_from_paas(paas)
        return PaasCiMapper.calculate_ci(zone)
