
from backend.src.core.settings.credentials.abstract_credentials import (
    AbstractCredentials
)


class AzureCredentials(AbstractCredentials):
    """Azure authentication credentials."""

    client_id: str | None = None
    client_secret: str | None = None
    tenant_id: str | None = None
