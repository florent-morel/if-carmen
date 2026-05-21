"""
Base module for reading and processing compute resource data.
"""

import csv
import logging

from pydantic import ValidationError

from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.readers.helpers.daemon_helpers import create_vm
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.schemas.resource import Resource
from backend.src.utils.helpers import str_to_float

logger = logging.getLogger(__name__)


class Reader_Compute(AbstractReader):
    """
    Implementation base class for reading virtual machines resource data.
    """

    def read(self, csv_data) -> list[VirtualMachine]:
        """
        Read and process VM data from local filesystem files.

        Returns:
            List of VirtualMachine objects containing the processed data.

        Raises:
            Exception: If file reading or processing fails.
        """
        logger.info("starting to read vm data from local filesystem")

        try:
            vm_dict: dict[str, VirtualMachine] = {}

            self.process_csv_data(csv_data, vm_dict)

            self.list_resources_to_process = list(vm_dict.values())

            self.log_processing_results(self)

            return self.list_resources_to_process

        except Exception as e:
            logger.error("failed to read files from local filesystem %s", str(e))
            raise

    def process_csv_data(
        self,
        blob_data: str,
        vm_dict: dict[str, VirtualMachine],
    ) -> bool:
        """
        Processes CSV data from the blob and updates the virtual machine dictionary.

        Args:
            blob_data (str): The CSV data read from the blob, as a string.
            vm_dict (Dict[str, VirtualMachine]): The dictionary containing VirtualMachine objects, indexed by their ID.
        Returns:
            bool: Returns True if the CSV data is processed successfully and contains data,
            False if the CSV data is empty (excluding the header row).
        """
        rows = blob_data.splitlines()
        if len(rows) == 1:
            return False
        csv_reader = csv.DictReader(rows)
        for row in csv_reader:
            vm_id = row["Id"]
            try:
                if vm_id not in vm_dict:
                    self.process_unknown_regions(row["Region"])
                    self.process_unknown_providers(row["Provider"])
                    new_vm = create_vm(row, vm_id)
                    vm_dict[vm_id] = new_vm

                vm_dict[vm_id].cpu_util.append(
                    str_to_float(row["AverageCpuPercentage"]) / 100
                )
                vm_dict[vm_id].time_points.append(row["Time"])
                vm_dict[vm_id].storage_size.append(str_to_float(row["DiskSizeGb"]))
            except ValidationError:
                logger.exception("Validation error for VM %s", vm_id)
                raise

        return True

    def log_processing_results(self) -> None:
        """
        Log the results of the processing operation.
        """
        logger.info("Processing completed found %d compute resources",
                    len(self.list_resources_to_process))

        self.log_unknown_info(self)

        logger.info("Local Reader processing finished successfully"
                    "for resource type compute.")
