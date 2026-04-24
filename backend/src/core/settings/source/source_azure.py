
from backend.src.core.settings.source.abstract_source import (
    AbstractSource
)


class AzureSourceConfig(AbstractSource):
    """Azure Blob Storage source configuration."""

    storage_account_url: str | None = None
    container_name_read: str | None = None
