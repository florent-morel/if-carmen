import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.storage_resource import StorageResource
from backend.src.core.settings import FinOpsConfig

logger = logging.getLogger(__name__)


class Writer_Storage(AbstractWriter):

    def build_content(resources: list[StorageResource]):

        # Add resources
        for storage_resource in resources:
            # Build common columns
            row = super.build_common_content(storage_resource)

            # storage_resource specific columns
            row[FinOpsConfig.HEADER_STORAGE_TYPE] = storage_resource.storage_type
            row[FinOpsConfig.HEADER_STORAGE_REPLICATION_TYPE] = storage_resource.replication_type
            row[FinOpsConfig.HEADER_STORAGE_SIZE_GB] = storage_resource.size_gb
            # TODO: Needed???
            row[FinOpsConfig.HEADER_STORAGE_] = storage_resource.resource_group
            row[FinOpsConfig.HEADER_STORAGE_] = storage_resource.total_storage_embodied
            row[FinOpsConfig.HEADER_STORAGE_] = storage_resource.duration_seconds

            writer.write(row)

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
