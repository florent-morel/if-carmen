
from backend.src.core.settings.upload.abstract_upload_config import (
    AbstractUploadConfig
)

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    MissingParametersError,
)


class AzureUploadConfig(AbstractUploadConfig):
    """Azure Blob Storage upload configuration."""

    container_name_upload: str | None = None
    blob_name: str | None = None

    def validate_configuration(self):
        """
        Validate source configuration parameters.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        # Check Azure credentials (shared with source)
        # TODO: call credentials validation method

        # Check Azure upload settings
        missing: list[str] = []
        if not self.upload.azure.container_name_upload:
            missing.append("container_name_upload")

        if missing:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, missing
            )
