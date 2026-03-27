"""
Local filesystem reader strategy for processing virtual machine data from local CSV files.
"""

import logging
from pathlib import Path

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.daemon_helpers import log_missing_regions
from backend.src.daemon.readers.reader_compute import ReaderCompute
from backend.src.schemas.virtual_machine import VirtualMachine

logger = logging.getLogger(__name__)


class ReaderComputeLocal(ReaderCompute):
    """
    Local filesystem reader strategy for processing VM data from CSV files.

    This class implements the Reader interface to read and process virtual machine
    data stored in the local filesystem.
    """

    def __init__(self, config: DaemonConfig) -> None:
        """
        Initialize the local reader strategy.

        Args:
            config: Daemon configuration containing local source settings.

        Raises:
            ValueError: If required configuration parameters are missing or invalid.
        """
        super().__init__(config)
        logger.info("initializing local compute reader strategy")

        # These are guaranteed to be non-None after config loader validation
        # Resolve path to absolute to handle relative paths correctly
        self.source_path: Path = Path(
            str(self.config.source.local.source_path)
        ).resolve()
        self.file_names: list[str] = self.config.source.file_names

        logger.debug(
            "local compute reader initialized with source path %s files %d",
            self.source_path,
            len(self.file_names),
        )

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
