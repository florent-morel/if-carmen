"""
This script is used to map PaaS value retrieved from Thanos to their respective azure regions,
and used to calculate carbon intensity depending on their region and time range by using CAW.
"""

from functools import lru_cache
from backend.src.common import constants
from backend.src.utils.helpers import remove_unnecessary
from backend.src.common.constants import ZONES


class PaasCiMapper:
    """
    Provides methods to calculate carbon intensity based on PaaS values and time range,
    and to map PaaS values to their respective Azure regions.
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
    @lru_cache(1000)  # we have 14 different azure regions
    def calculate_ci(zone: str) -> float:
        if zone in constants.REGION_TO_COUNTRY_CARBON_INTENSITY:
            return constants.REGION_TO_COUNTRY_CARBON_INTENSITY[zone][
                "carbon_intensity"
            ]
        return (
            constants.CARBON_INTENSITY_EUROPE
        )  # fallback to default european average in case of a new region

    @staticmethod
    def get_ci_from_paas(paas: str) -> float:
        zone = PaasCiMapper.__extract_zone_from_paas(paas)
        return PaasCiMapper.calculate_ci(zone)
