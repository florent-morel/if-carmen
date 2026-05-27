import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.core.settings import ReportConfig

logger = logging.getLogger(__name__)


class Writer_Compute(AbstractWriter):
    def write_content(self, resources: list[VirtualMachine]):
        logger.info(
            "Starting write_content for resource %s.", VirtualMachine.resource_type
        )

        for resource in resources:
            # Build common columns
            row = super().write_common_content(resource)

            # VM specific columns
            row[ReportConfig.COMPUTE_VM_SIZE] = resource.vm_size
            row[ReportConfig.COMPUTE_SERVICE] = resource.service
            row[ReportConfig.COMPUTE_INSTANCE] = resource.instance
            row[ReportConfig.COMPUTE_ENVIRONMENT] = resource.environment
            row[ReportConfig.COMPUTE_PARTITION] = resource.partition
            row[ReportConfig.COMPUTE_COMPONENT] = resource.component

        logger.info(
            " Rows built for %d resources",
            len(resources),
        )
