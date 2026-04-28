import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.core.settings import ReportConfig

logger = logging.getLogger(__name__)


class Writer_Compute(AbstractWriter):
    def write_content(vms: list[VirtualMachine]):
        # Add VMs
        for vm in vms:
            # Build common columns
            row = super.write_common_content(vm)

            # VM specific columns
            row[ReportConfig.COMPUTE_VM_SIZE] = vm.vm_size
            row[ReportConfig.COMPUTE_SERVICE] = vm.service
            row[ReportConfig.COMPUTE_INSTANCE] = vm.instance
            row[ReportConfig.COMPUTE_ENVIRONMENT] = vm.environment
            row[ReportConfig.COMPUTE_PARTITION] = vm.partition
            row[ReportConfig.COMPUTE_COMPONENT] = vm.component

            super.writer.write(row)

        logger.info(
            " Rows built for %d resources",
            len(vms),
        )
