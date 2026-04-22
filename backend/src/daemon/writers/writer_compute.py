import logging
from typing import Any, Iterable

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.virtual_machine import VirtualMachine

logger = logging.getLogger(__name__)


class Writer_Compute(AbstractWriter):

    def build_content(vms: list[VirtualMachine]) -> Iterable[Iterable[Any]]:

        # Add VMs
        list_rows = []
        for vm in vms:
            # Build common columns
            row = super.build_common_content(vm)

            # VM specific columns
            row.append(vm.vm_size)
            row.append(vm.service)
            row.append(vm.instance)
            row.append(vm.environment)
            row.append(vm.partition)
            row.append(vm.component)

            list_rows.append(row)

        logger.info(
            " Rows built for %d resources",
            len(vms),
        )
        return list_rows
