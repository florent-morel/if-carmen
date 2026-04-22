import logging
from typing import Any, Iterable

from backend.src.core.settings import settings
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.storage_resource import StorageResource

logger = logging.getLogger(__name__)


class Writer_Storage(AbstractWriter):

    def build_content(resources: list[StorageResource]) -> Iterable[Iterable[Any]]:

        # Add resources
        list_rows = []
        for storage_resource in resources:
            # Build common columns
            row = super.build_common_content(storage_resource)

            # storage_resource specific columns
            row.append(storage_resource.storage_type)
            row.append(storage_resource.replication_type)
            row.append(storage_resource.size_gb)
            row.append(storage_resource.resource_group)
            row.append(storage_resource.total_storage_embodied)
            row.append(storage_resource.duration_seconds)

            list_rows.append(row)

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
        return list_rows
