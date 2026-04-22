import logging
from typing import Any, Iterable

from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.virtual_machine import VirtualMachine

logger = logging.getLogger(__name__)


class ComputeWriter(AbstractWriter):

    def build_content(vms: list[VirtualMachine]) -> Iterable[Iterable[Any]]:
        vm_carbon = 0
        vm_energy = 0

        # Add VMs
        list_rows = []
        for vm in vms:
            vm.total_carbon_emitted = (
                vm.total_carbon_operational + vm.total_carbon_embodied
            )
            vm_carbon += vm.total_carbon_emitted
            vm_energy += vm.total_energy_consumed

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

        logging.info("Total carbon emitted: %.2f kg CO2", vm_carbon)
        logging.info("Total energy consumed: %.2f kWh", vm_energy)
        logger.info(
            "  Resources: %d VMs",
            len(vms),
        )
        return list_rows

