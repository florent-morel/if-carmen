from __future__ import annotations

import logging
import time

from backend.src.common.constants import (
    HOURLY_INTERVAL_SECONDS,
)
from backend.src.common.known_exception import KnownException
from backend.src.daemon.carbon_daemon_result import ResourceDaemonResult
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.schemas.resource import Resource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)


class Runner_Compute(AbstractRunner):
    """
    Implementation of the Runner for the Virtual Machine Type.
    """

    def __init__(self):
        self.resource_daemon_result: ResourceDaemonResult | None

    #
    # Resources built by the reader to be handled by the runner
    @property
    def resource_daemon_result(self) -> ResourceDaemonResult | None:
        return self.resource_daemon_result

    def run(self, list_resources_to_process: list[Resource]) -> ResourceDaemonResult:
        """
        Run the Impact Framework and build result for Virtual Machines Resource Type.

        Returns:
            ResourceDaemonResult containing execution results
        """
        start_time = time.time()

        try:
            logger.info("Starting Virtual Machine runner execution")

            # vms = self.read_infrastructure_data(ResourceType.VIRTUAL_MACHINE)
            # if not vms:
            #     raise KnownException(
            #         ErrorCode.DATA_FETCH_NO_RESULTS,
            #         details="No virtual machines found in data source",
            #     )

            processed_vms = self.process_carbon_calculations(list_resources_to_process)

            execution_time = time.time() - start_time

            resourceDaemonResult = self.create_ResourceDaemonResult(
                True, execution_time, processed_vms
            )

            logger.info(
                "VM Carbon Daemon execution completed successfully. processed %d VMs in %.2f seconds",
                len(resourceDaemonResult.list_processed_resources),
                execution_time,
            )
            logger.info(
                "VM Carbon Daemon execution completed successfully. "
                "Processed %d VMs in %.2f seconds",
                len(resourceDaemonResult.list_processed_resources),
                resourceDaemonResult.total_energy_consumed,
                resourceDaemonResult.total_carbon_emitted,
            )

            return resourceDaemonResult

        except KnownException as e:
            execution_time = time.time() - start_time
            error_msg = f"known error during daemon execution: {e.formatted_string}"
            logger.error(error_msg)

            return ResourceDaemonResult(
                success=False, execution_time=execution_time, error_message=error_msg
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"unexpected error during daemon execution: {str(e)}"
            logger.exception(error_msg)

            return ResourceDaemonResult(
                success=False, execution_time=execution_time, error_message=error_msg
            )

    def process_carbon_calculations(
        self, list_resources_to_process: list[Resource]
    ) -> list[Resource]:
        """
        Process virtual machines through the carbon calculation engine.

        Scope:
            - cpu
            - memory
            - VM disks

        Args:
            vms: List of virtual machines to process

        Returns:
            List of virtual machines with carbon calculations

        Raises:
            Exception: If carbon processing fails
        """
        process_start_time = time.time()

        try:
            logger.info(
                "starting carbon calculations for %d VMs",
                len(list_resources_to_process),
            )

            carbon_service = ioc_util.resolve(
                CarbonService, "IFVm", HOURLY_INTERVAL_SECONDS
            )

            if carbon_service is None:
                raise RuntimeError("failed to resolve CarbonService from IoC container")

            processed_vms: list[VirtualMachine] = carbon_service.run_engine(
                list_resources_to_process
            )

            process_time = time.time() - process_start_time

            logger.info("carbon calculations completed in %.2f seconds", process_time)

            return processed_vms

        except Exception as e:
            logger.error("failed to process carbon calculations: %s", str(e))
            raise
