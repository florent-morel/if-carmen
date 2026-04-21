
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AbstractUploader(ABC):
    """
    Main abstract class to provide the methods for the implementation of the
    call to CO2 report file upload.
    """

    @abstractmethod
    def upload_report(self):
        pass
