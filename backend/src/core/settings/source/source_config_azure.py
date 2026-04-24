
from backend.src.core.settings.source.abstract_source_config import (
    AbstractSourceConfig
)

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    MissingParametersError,
)


class AzureSourceConfig(AbstractSourceConfig):
    """Azure Blob Storage source configuration."""

    storage_account_url: str | None = None
    container_name_read: str | None = None

    def validate_specific_configuration(self):
        """
        Validate source configuration parameters dedicated to Azure.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        # Check Azure source settings
        missing: list[str] = []
        if not self.source.azure.storage_account_url:
            missing.append("storage_account_url")
        if not self.source.azure.container_name_read:
            missing.append("container_name_read")

        if missing:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, missing
            )

        if (
            self.source.azure.storage_account_url
            and not self.source.azure.storage_account_url.startswith("https://")
        ):
            raise ValueError("storage account url must be a valid https url")
