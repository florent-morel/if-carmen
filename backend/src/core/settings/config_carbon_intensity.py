

import logging


logger = logging.getLogger(__name__)


class CarbonIntensityConfig():
    """
    Configuration class for supported providers.
    """

    def __init__(self):
        self.dict_ci_per_location: dict[str: int]

    def get_dict_ci_per_location(self) -> dict[str: int] | None:
        return self.dict_ci_per_location
