
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class AbstractCredentialsConfig(ABC, BaseSettings):
    """
    Main abstract class to provide fields & methods for credentials configuration
    used by the dameon.
    """

    @abstractmethod
    def validate_configuration(self):
        """
        Validate credentials configuration parameters.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        self.validate_specific_configuration()

    @abstractmethod
    def validate_specific_configuration(self):
        pass
