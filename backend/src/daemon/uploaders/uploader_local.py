

from __future__ import annotations

import logging
from backend.src.daemon.uploaders.abstract_uploader import AbstractUploader

logger = logging.getLogger(__name__)


class Uploader_Local(AbstractUploader):
    """
    Main abstract class to provide the methods for the implementation of the
    call to CO2 report file upload.
    """

    def upload_report(self):
        # TODO: Implement
        pass
