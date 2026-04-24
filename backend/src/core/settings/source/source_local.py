
from backend.src.core.settings.source.abstract_source import (
    AbstractSource
)


class LocalSourceConfig(AbstractSource):
    """Local file system source configuration."""

    source_path: str | None = None
