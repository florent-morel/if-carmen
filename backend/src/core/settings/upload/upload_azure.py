
from backend.src.core.settings.upload.abstract_upload import (
    AbstractUpload
)


class AzureUploadConfig(AbstractUpload):
    """Azure Blob Storage upload configuration."""

    container_name_upload: str | None = None
    blob_name: str | None = None
