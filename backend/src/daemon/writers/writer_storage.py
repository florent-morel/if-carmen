import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.storage_resource import StorageResource
from backend.src.core.settings import ReportConfig
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class Writer_Storage(AbstractWriter):
    def write_content(self, resources: list[StorageResource]):
        logger.info(
            "Starting write_content for resource %s.", ResourceType.STORAGE
        )

        # Add resources
        for resource in resources:
            # Build common columns
            row = super().write_common_content(resource)

            # Storage specific columns
            row[ReportConfig.STORAGE_TYPE] = resource.storage_type
            row[ReportConfig.STORAGE_REPLICATION_TYPE] = resource.replication_type
            row[ReportConfig.STORAGE_SIZE_GB] = resource.size_gb

            self.csv_dict_writer.writerow(row)

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
