
import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class AbstractProviderConfig(ABC):
    """
    Configuration class for supported providers.
    """

    def __init__(self):
        self.pue: float
        self.electricity_ratios: dict[str: float]
        self.storage_embodied: dict[str: int]
        self.storage_replication_factors: dict[str: int]
        self.disk_sku_size_mapping: dict[str: int]

    @property
    @abstractmethod
    def get_pue(self) -> float | None:
        pass

    @property
    @abstractmethod
    def get_electricity_ratios(self) -> dict[str: float] | None:
        pass

    @property
    @abstractmethod
    def get_storage_replication_factors(self) -> dict[str: int] | None:
        pass
