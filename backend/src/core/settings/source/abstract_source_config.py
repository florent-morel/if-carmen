
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pydantic_settings import BaseSettings
from typing import Literal

from backend.src.core.settings.credentials.abstract_credentials import (
    AbstractCredentials
)

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    MissingParametersError,
)

logger = logging.getLogger(__name__)


class AbstractSourceConfig(ABC, BaseSettings):
    """
    Main abstract class to provide fields & methods for source configuration
    used by the dameon.
    """

    def __init__(self):
        self.list_credentials: list[AbstractCredentials]
        self.file_names: list[str] = []

    def validate_configuration(self):
        """
        Validate source configuration parameters.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        # Validate file_names
        if not self.source.file_names:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["file_names"]
            )

        # Loop on all credentials and validate them
        for credential in self.list_credentials:
            credential.validate_configuration()

        self.validate_specific_configuration()

    @abstractmethod
    def validate_specific_configuration(self):
        pass
