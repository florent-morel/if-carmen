
from backend.src.core.settings.upload.abstract_upload import (
    AbstractUpload
)


class LocalUploadConfig(AbstractUpload):
    """Local file system upload configuration."""

    upload_path: str | None = None
