"""
Base module for reading and processing compute resource data.
"""

import csv
import logging
from collections import Counter
from pathlib import Path

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

    def __init__(self, daemon_config: DaemonConfig):
        self.config: DaemonConfig = daemon_config
        logger.info("initializing local compute reader.")

        self.input_path: Path = Path(str(self.config.source.input_path)).resolve()
        self.known_regions: set[str] = {
            region
            for pc in config.provider_configs.values()
            if pc.get_regions()
            for region in pc.get_regions()
        }
        self.missing_regions: Counter = Counter()
        self.missing_providers: Counter = Counter()
        logger.info(
            "local compute reader initialized with source path %s",
            self.input_path,
        )

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

            self._log_processing_results(vm_dict)

            self.list_resources_to_process = list(vm_dict.values())
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
                    if row["Region"] not in self.known_regions:
                        self.missing_regions[row["Region"]] += 1
                    if row["Provider"] not in config.provider_configs:
                        self.missing_providers[row["Provider"]] += 1
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

    def _log_processing_results(self, vm_dict: dict[str, VirtualMachine]) -> None:
        """
        Log the results of the processing operation.
        """
        logger.info("processing completed found %d compute resources", len(vm_dict))

        for region, count in self.missing_regions.items():
            logger.warning(
                "unknown region '%s': %d VMs — using default carbon intensity",
                region,
                count,
            )
        for provider, count in self.missing_providers.items():
            logger.warning(
                "unknown provider '%s': %d VMs — using default PUE",
                provider,
                count,
            )

        logger.info("local compute reader processing finished successfully")
