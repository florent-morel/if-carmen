"""
Base module for reading and processing compute resource data.
"""

import csv
import logging
from pathlib import Path
from backend.src.daemon.readers.abstract_reader import AbstractReader

from pydantic import ValidationError

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.helpers.daemon_helpers import (
    calculate_vm_count_for_missing_regions,
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

logger = logging.getLogger(__name__)


class Reader_Compute(AbstractReader):
    """
    Implementation base class for reading virtual machines resource data.
    """

    def __init__(self, config: DaemonConfig):
        self.config: DaemonConfig = config
        logger.info("initializing local compute reader.")

        self.list_resources_to_process: list[Resource]
        # These are guaranteed to be non-None after config loader validation
        # Resolve path to absolute to handle relative paths correctly
        self.source_path: Path = Path(
            str(self.config.source.local.source_path)
        ).resolve()
        self.file_names: list[str] = self.config.source.file_names

        logger.info(
            "local compute reader initialized with source path %s files %d",
            self.source_path,
            len(self.file_names),
        )

    @property
    def list_resources_to_process(self) -> list[Resource] | None:
        return self.list_resources_to_process

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

    def read(self) -> list[VirtualMachine]:
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
            missing_region_vm_count: dict[str, int] = {}
            missing_files: set[str] = set()

            self._process_local_files(vm_dict, missing_region_vm_count, missing_files)

            self._log_processing_results(
                vm_dict, missing_region_vm_count, missing_files
            )

            return list(vm_dict.values())

        except Exception as e:
            logger.error("failed to read files from local filesystem %s", str(e))
            raise

    def _process_local_files(
        self,
        vm_dict: dict[str, VirtualMachine],
        missing_region_vm_count: dict[str, int],
        missing_files: set[str],
    ) -> None:
        """
        Process each file in the configured file list.

        Args:
            vm_dict: Dictionary to store processed VirtualMachine objects.
            missing_region_vm_count: Dictionary to track missing regions.
            missing_files: Set to track missing files.
        """
        total_files = len(self.file_names)
        logger.info("processing %d local files", total_files)

        for index, file_name in enumerate(self.file_names, 1):
            file_path = self.source_path / file_name
            logger.debug("processing file %d/%d %s", index, total_files, str(file_path))

            try:
                file_data = self._read_file_data(file_path)
                if file_data is None:
                    missing_files.add(file_name)
                    continue

                if not self.process_csv_data(
                    file_data, vm_dict, missing_region_vm_count
                ):
                    logger.warning("empty or invalid csv data in file %s", file_name)
                else:
                    logger.debug("successfully processed file %s", file_name)

            except Exception as e:
                logger.error(
                    "unexpected error processing file %s %s", file_name, str(e)
                )
                missing_files.add(file_name)

    def _read_file_data(self, file_path: Path) -> str | None:
        """
        Read file data from local filesystem.

        Args:
            file_path: Path to the file.

        Returns:
            File data as string, or None if file not found or read failed.
        """
        try:
            logger.debug("attempting to read file %s", file_path)

            if not file_path.exists():
                logger.warning("file does not exist %s", file_path)
                return None

            if not file_path.is_file():
                logger.warning("path is not a file %s", file_path)
                return None

            with file_path.open("r", encoding="utf-8") as file:
                file_data = file.read()

            logger.debug(
                "successfully read file %s %d bytes", file_path, len(file_data)
            )
            return file_data

        except FileNotFoundError:
            logger.warning("file not found %s", file_path)
            return None
        except PermissionError as e:
            logger.error("permission denied reading file %s %s", file_path, str(e))
            raise KnownException(
                ErrorCode.FILE_PERMISSION_DENIED,
                details=f"permission denied: {file_path}",
            ) from e
        except UnicodeDecodeError as e:
            logger.error("failed to decode file data for %s %s", file_path, str(e))
            return None
        except Exception as e:
            logger.error("unexpected error reading file %s %s", file_path, str(e))
            raise KnownException(
                ErrorCode.FILE_READ_ERROR, details=f"failed to read file: {file_path}"
            ) from e

    def _log_processing_results(
        self,
        vm_dict: dict[str, VirtualMachine],
        missing_region_vm_count: dict[str, int],
        missing_files: set[str],
    ) -> None:
        """
        Log the results of the processing operation.

        Args:
            vm_dict: Dictionary of processed VirtualMachine objects.
            missing_region_vm_count: Dictionary of missing regions and counts.
            missing_files: Set of missing files.
        """
        logger.info("processing completed found %d virtual machines", len(vm_dict))

        if missing_files:
            logger.warning(
                "missing files %d %s", len(missing_files), sorted(missing_files)
            )

        if missing_region_vm_count:
            log_missing_regions(missing_region_vm_count)

        logger.info("local compute reader processing finished successfully")
