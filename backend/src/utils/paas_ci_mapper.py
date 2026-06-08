"""
This script is used to map PaaS value retrieved from Thanos to their respective azure regions,
and used to calculate carbon intensity depending on their region and time range by using CAW.
"""

from functools import lru_cache
from backend.src.utils.helpers import remove_unnecessary
from backend.src.core.yaml_config_loader import config


class PaasCiMapper:
    """
    Provides methods to calculate carbon intensity based on PaaS values and time range,
    and to map PaaS values to their respective regions.
    """

    @staticmethod
    def __extract_zone_from_paas(paas: str) -> str:
        """
        Extracts a zone from a given PaaS value by matching against zone_aliases
        defined in each provider's configuration.
        :param paas: The paas value string from which to extract the location.
        :return: The extracted location or None if no match is found.
        """
        zone_aliases = config.zone_aliases

        # Check direct PaaS value match (digits stripped, uppercased)
        direct_loc = remove_unnecessary(paas.upper())
        if direct_loc in zone_aliases:
            return zone_aliases[direct_loc]

        # Check each hyphen-separated part
        parts = paas.upper().split("-")
        for part in parts:
            loc = remove_unnecessary(part)
            if loc in zone_aliases:
                return zone_aliases[loc]

        # No match found
        return None

    @staticmethod
    @lru_cache(1000)
    def calculate_ci(zone: str) -> float:
        ci_config = config.carbon_values_config
        default_ci = ci_config.default_carbon_intensity
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
