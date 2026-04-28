import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.core.settings import ReportConfig

logger = logging.getLogger(__name__)


class Writer_Misc_Services(AbstractWriter):
    def write_content(resources: list[MiscServicesResource]):
        logger.info("Starting write_results for Misc Services resources.")

        # Add resources
        for resource in resources:
            # Build common columns
            row = super.write_common_content(resource)

            # resource specific columns
            row[ReportConfig.MISC_SERVICES_COST] = resource.services_cost

            super.writer.write(row)

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
