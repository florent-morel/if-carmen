import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.storage_resource import StorageResource
from backend.src.core.settings import ReportConfig

logger = logging.getLogger(__name__)


class Writer_Storage(AbstractWriter):
    def write_content(resources: list[StorageResource]):
        logger.info(
            "Starting write_results for resource %s.", StorageResource.resource_type
        )

        # Add resources
        for resource in resources:
            # Build common columns
            row = super.build_common_content(resource)

            # resource specific columns
            row[ReportConfig.HEADER[ReportConfig.STORAGE]
                [ReportConfig.STORAGE_TYPE]] = resource.storage_type
            row[ReportConfig.HEADER[ReportConfig.STORAGE]
                [ReportConfig.STORAGE_REPLICATION_TYPE]] = resource.replication_type
            row[ReportConfig.HEADER[ReportConfig.STORAGE]
                [ReportConfig.STORAGE_SIZE_GB]] = resource.size_gb

            super.writer.write(row)

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
