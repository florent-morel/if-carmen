
from backend.src.core.settings.credentials.abstract_credentials_config import (
    AbstractCredentialsConfig
)

from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import (
    MissingParametersError,
)


class AzureCredentialsConfig(AbstractCredentialsConfig):
    """Azure authentication credentials."""

    client_id: str | None = None
    client_secret: str | None = None
    tenant_id: str | None = None

    def validate_specific_configuration(self):
        """
        Validate source configuration parameters dedicated to Azure.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        # Check Azure credentials
        missing: list[str] = []
        if not self.credentials.client_id:
            missing.append("client_id")
        if not self.credentials.client_secret:
            missing.append("client_secret")
        if not self.credentials.tenant_id:
            missing.append("tenant_id")

        if missing:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, missing
            )
