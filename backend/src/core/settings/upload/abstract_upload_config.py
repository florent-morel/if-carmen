
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pydantic_settings import BaseSettings

from backend.src.core.settings.credentials.abstract_credentials import (
    AbstractCredentialsConfig
)

logger = logging.getLogger(__name__)


class AbstractUploadConfig(ABC, BaseSettings):
    """
    Main abstract class to provide fields & methods for upload configuration
    used by the dameon.
    """

    def __init__(self):
        self.list_credentials: list[AbstractCredentialsConfig]

    @abstractmethod
    def validate_configuration(self):
        """
        Validate source configuration parameters.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        # Loop on all credentials and validate them
        for credential in self.list_credentials:
            credential.validate_configuration()

        self.validate_specific_configuration()

    @abstractmethod
    def validate_specific_configuration(self):
        pass
