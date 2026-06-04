"""
Base module for reading and processing compute resource data.
"""

import csv
import logging

from pydantic import ValidationError

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.readers.helpers.daemon_helpers import create_vm
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.helpers import str_to_float
from backend.src.utils.helpers import (
    process_custom_columns,
)

from backend.src.common.constants import (
    SOURCE_PROVIDER,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_AVG_CPU_PERCENTAGE,
    SOURCE_TIME,
    SOURCE_DISK_SIZE_GB,
)

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

            self.log_processing_results()

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

        total_rows = 0
        new_vm_rows = 0
        duplicate_rows = 0
        skipped_rows = 0
        excluded_rows = 0

        for row in csv_reader:
            total_rows += 1
            consumed_service = row.get(SOURCE_CONSUMED_SERVICE, "")
            if consumed_service.lower() != SOURCE_COMPUTE.lower():
                skipped_rows += 1
                continue
            vm_id = row[SOURCE_RESOURCE_ID]
            try:
                if vm_id not in vm_dict:
                    self.process_unknown_regions(row[SOURCE_REGION])
                    self.process_unknown_providers(row[SOURCE_PROVIDER])
                    new_vm = create_vm(row, vm_id)
                    vm_dict[vm_id] = new_vm
                    new_vm_rows += 1
                else:
                    duplicate_rows += 1

                vm_dict[vm_id].cpu_util.append(
                    str_to_float(row[SOURCE_AVG_CPU_PERCENTAGE]) / 100
                )
                vm_dict[vm_id].time_points.append(row[SOURCE_TIME])
                vm_dict[vm_id].storage_size.append(str_to_float(row[SOURCE_DISK_SIZE_GB]))
                # End of row process, fetch custom columns
                process_custom_columns(vm_dict[vm_id], row)
            except ValidationError:
                logger.exception("Validation error for VM %s", vm_id)
                excluded_rows += 1
                raise

        self.dict_log_info["total_rows"] = total_rows
        self.dict_log_info["new_vm_rows"] = new_vm_rows
        self.dict_log_info["duplicate_rows"] = duplicate_rows
        self.dict_log_info["skipped_rows"] = skipped_rows
        self.dict_log_info["excluded_rows"] = excluded_rows

        return True

    def log_processing_results(self) -> None:
        """
        Log the results of the processing operation.
        """
        logger.info("Processing completed found %d compute resources",
                    len(self.list_resources_to_process))

        logger.debug("Compute processing summary:")
        logger.debug("  Total rows: %s", self.dict_log_info.get("total_rows", 0))
        logger.debug("  New VM rows: %s", self.dict_log_info.get("new_vm_rows", 0))
        logger.debug("  Duplicate rows (time-series): %s", self.dict_log_info.get("duplicate_rows", 0))
        logger.debug("  Excluded rows: %s", self.dict_log_info.get("excluded_rows", 0))

        self.log_unknown_info()

        logger.info("Local Reader processing finished successfully"
                    "for resource type compute.")
