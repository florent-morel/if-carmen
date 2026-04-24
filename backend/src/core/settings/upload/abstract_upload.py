
from __future__ import annotations

import logging
from abc import ABC
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class AbstractUpload(ABC, BaseSettings):
    """
    Main abstract class to provide fields & methods for upload configuration
    used by the dameon.
    """
