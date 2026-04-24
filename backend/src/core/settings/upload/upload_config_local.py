
from backend.src.core.settings.upload.abstract_upload_config import (
    AbstractUploadConfig
)

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    MissingParametersError,
)


class LocalUploadConfig(AbstractUploadConfig):
    """Local file system upload configuration."""

    upload_path: str | None = None

    def validate_configuration(self):
        """
        Validate source configuration parameters.

        Raises:
            MissingParametersError: If required parameters are missing.
        """

        if not self.upload.local.upload_path:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["upload_path"]
            )
