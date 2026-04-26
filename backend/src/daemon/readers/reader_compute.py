"""
Base module for reading and processing compute resource data.
"""

import csv
import logging
from logging import config
from logging import config
from pathlib import Path
from backend.src.daemon.readers.abstract_reader import AbstractReader

from pydantic import ValidationError
from collections import Counter

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.helpers.daemon_helpers import (
    create_vm,
)
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.schemas.resource import Resource
from backend.src.utils.helpers import str_to_float
from backend.src.common.known_exception import (
    KnownException,
)
from backend.src.common.errors import ErrorCode
from backend.src.daemon.readers.helpers.daemon_helpers import (
    log_missing_regions,
)
from backend.src.core.settings.config_carbon_intensity import (
    CarbonIntensityConfig,
)

logger = logging.getLogger(__name__)


class Reader_Compute(AbstractReader):
    """
    Implementation base class for reading virtual machines resource data.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config
        logger.info("initializing local compute reader.")
        # TODO: Instantiate provider config
        self.carbon_intensity_config: CarbonIntensityConfig

        self.list_resources_to_process: list[Resource]
        # These are guaranteed to be non-None after config loader validation
        # Resolve path to absolute to handle relative paths correctly
        self.input_path: Path = Path(str(self.config.source.input_path)).resolve()

        self.missing_regions: Counter = Counter()
        self.missing_providers: Counter = Counter()
        logger.info(
            "local compute reader initialized with source path %s",
            self.input_path,
        )

    @property
    def list_resources_to_process(self) -> list[Resource] | None:
        return self.list_resources_to_process

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

            self.process_csv_data(self, csv_data, vm_dict)

            self._log_processing_results(self, vm_dict)

            return list(vm_dict.values())

        except Exception as e:
            logger.error("failed to read files from local filesystem %s", str(e))
            raise

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
                    if row["Region"] not in known_regions:
                        self.missing_regions[row["Region"]] += 1
                    if row["Provider"] not in config.provider_configs:
                        self.missing_providers[row["Provider"]] += 1
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

    def _log_processing_results(
        self,
        vm_dict: dict[str, VirtualMachine],
        missing_region_vm_count: dict[str, int],
    ) -> None:
        """
        Log the results of the processing operation.

        Args:
            vm_dict: Dictionary of processed VirtualMachine objects.
            missing_region_vm_count: Dictionary of missing regions and counts.
            missing_files: Set of missing files.
        """
        logger.info("processing completed found %d compute resources", len(vm_dict))

        if missing_region_vm_count:
            log_missing_regions(missing_region_vm_count)

        logger.info("local compute reader processing finished successfully")

    def calculate_vm_count_for_missing_regions(
        self, missing_region_vm_count: dict[str, int], region: str
    ):
        """
        Fills the missing_region_vm_count dictionary.
        Args:
            missing_region_vm_count Dict[str, int]: Dictionary with the information of missing regions and
            the corresponding VM count.
            region str: Current VM's region.
        def get_vms() -> list
        """
        if region not in self.config_carbon_intensity.get_dict_ci_per_location():
            if region not in missing_region_vm_count:
                missing_region_vm_count[region] = 1
            else:
                missing_region_vm_count[region] += 1
