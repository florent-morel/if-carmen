import logging
from abc import ABC, abstractmethod
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class AbstractProviderConfig(BaseSettings, ABC):
    """
    Configuration class for supported providers.
    """

    pue: float | None = None
    electricity_ratios: dict[str, float] | None = None
    storage_embodied: dict[str, int] | None = None
    storage_replication_factors: dict[str, int] | None = None
    disk_sku_size_mapping: dict[str, int] | None = None

    @property
    @abstractmethod
    def get_pue(self) -> float | None:
        pass

    @property
    @abstractmethod
    def get_electricity_ratios(self) -> dict[str, float] | None:
        pass

    @property
    @abstractmethod
    def get_storage_replication_factors(self) -> dict[str, int] | None:
        pass

    @property
    @abstractmethod
    def get_storage_embodied(self) -> dict[str, int] | None:
        pass

    @property
    @abstractmethod
    def get_disk_sku_size_mapping(self) -> dict[str, int] | None:
        pass
