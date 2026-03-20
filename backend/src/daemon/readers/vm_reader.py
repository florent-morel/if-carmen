"""
Base module for reading and processing compute resource data.
"""

import csv
import logging
from abc import ABC, abstractmethod

from pydantic import ValidationError

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.daemon_helpers import (
    calculate_vm_count_for_missing_regions,
    create_vm,
)
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.helpers import str_to_float

logger = logging.getLogger(__name__)


class Reader(ABC):
    """
    Abstract base class for reading compute resource data from various sources.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config

    @abstractmethod
    def read_files(self) -> list[VirtualMachine]:
        """
        Read and process files to extract virtual machine information.

        Returns:
            list[VirtualMachine]: List of virtual machines extracted from the data source.
        """

    def process_csv_data(
        self,
        blob_data: str,
        vm_dict: dict[str, VirtualMachine],
        missing_region_vm_count: dict[str, int],
    ) -> bool:
        """
        Processes CSV data from the blob and updates the virtual machine dictionary.

        Args:
            missing_region_vm_count (Dict[str, int]): Dictionary with the information of missing regions and
            the corresponding VM count.
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
            vm_size = row["Size"]
            vm_id = row["Id"]
            try:
                if vm_id not in vm_dict:
                    calculate_vm_count_for_missing_regions(
                        missing_region_vm_count, row["Region"]
                    )
                    new_vm = create_vm(row, vm_id, vm_size)
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
