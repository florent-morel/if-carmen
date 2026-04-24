
from backend.src.core.settings.source.abstract_source_config import (
    AbstractSourceConfig
)

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    MissingParametersError,
)


class LocalSourceConfig(AbstractSourceConfig):
    """Local file system source configuration."""

    source_path: str | None = None

    def validate_configuration(self):
        """
        Validate source configuration parameters.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        if not self.source.local.source_path:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["source_path"]
            )
