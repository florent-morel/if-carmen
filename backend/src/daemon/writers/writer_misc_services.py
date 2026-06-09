import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.core.settings import ReportConfig
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)


class Writer_Misc_Services(AbstractWriter):
    def write_content(self, resources: list[MiscServicesResource]):
        logger.info(
            "Starting write_content for resource %s.",
            ResourceType.MISC_SERVICES,
        )

        # Add resources
        for resource in resources:
            # Build common columns
            row = super().write_common_content(resource)

            # No Misc services specific columns

            self.csv_dict_writer.writerow(row)

            self.csv_dict_writer.writerow(row)

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
