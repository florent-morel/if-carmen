import logging

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.core.settings import FinOpsConfig

logger = logging.getLogger(__name__)


class Writer_Compute(AbstractWriter):

    def build_content(vms: list[VirtualMachine]):

        # Add VMs
        for vm in vms:
            # Build common columns
            row = super.build_common_content(vm)

            # VM specific columns
            row[FinOpsConfig.HEADER_COMPUTE_VM_SIZE] = vm.vm_size
            row[FinOpsConfig.HEADER_COMPUTE_SERVICE] = vm.service
            row[FinOpsConfig.HEADER_COMPUTE_INSTANCE] = vm.instance
            row[FinOpsConfig.HEADER_COMPUTE_ENVIRONMENT] = vm.environment
            row[FinOpsConfig.HEADER_COMPUTE_PARTITION] = vm.partition
            row[FinOpsConfig.HEADER_COMPUTE_COMPONENT] = vm.component

            super.writer.write(row)

        logger.info(
            " Rows built for %d resources",
            len(vms),
        )
