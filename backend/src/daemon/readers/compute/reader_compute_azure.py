"""
Azure reader strategy for processing virtual machine data from Azure Blob Storage.
"""

import logging

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobClient, ContainerClient

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.helpers.daemon_helpers import log_missing_regions
from backend.src.daemon.readers.reader_compute import ReaderCompute
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.azure_utils import (
    create_blob_service_client,
    initialize_azure_client,
)

logger = logging.getLogger(__name__)


class ReaderComputeAzure(ReaderCompute):
    """
    Azure Blob Storage reader strategy for processing VM data from CSV files.

    This class implements the Reader interface to read and process virtual machine
    data stored in Azure Blob Storage containers.
    """

    def __init__(self, config: DaemonConfig) -> None:
        """
        Initialize the Azure reader strategy.

        Args:
            config: Daemon configuration containing Azure credentials and settings.

        Raises:
            ValueError: If required configuration parameters are missing.
            ClientAuthenticationError: If Azure authentication fails.
        """
        super().__init__(config)
        logger.info("initializing azure compute reader strategy")

        self.credentials: ClientSecretCredential = initialize_azure_client(config)

        # These are guaranteed to be non-None after config loader validation
        self.storage_account_url: str = str(
            self.config.source.azure.storage_account_url
        )
        self.container_name_read: str = str(
            self.config.source.azure.container_name_read
        )
        self.file_names: list[str] = self.config.source.file_names

        logger.debug(
            "azure compute reader initialized with container %s files %d",
            self.container_name_read,
            len(self.file_names),
        )

    def read(self) -> list[VirtualMachine]:
        """
        Read and process VM data from Azure Blob Storage files.

        Returns:
            List of VirtualMachine objects containing the processed data.

        Raises:
            Exception: If blob service initialization or processing fails.
        """
        logger.info("starting to read vm data from azure blob storage")

        try:
            blob_service_client = create_blob_service_client(
                self.storage_account_url, self.credentials
            )
            container_client = blob_service_client.get_container_client(
                self.container_name_read
            )

            vm_dict: dict[str, VirtualMachine] = {}
            missing_region_vm_count: dict[str, int] = {}
            missing_blobs: set[str] = set()

            self._process_blob_files(
                container_client, vm_dict, missing_region_vm_count, missing_blobs
            )

            self._log_processing_results(
                vm_dict, missing_region_vm_count, missing_blobs
            )

            return list(vm_dict.values())

        except Exception as e:
            logger.error("failed to read files from azure blob storage %s", str(e))
            raise

    def _process_blob_files(
        self,
        container_client: ContainerClient,
        vm_dict: dict[str, VirtualMachine],
        missing_region_vm_count: dict[str, int],
        missing_blobs: set[str],
    ) -> None:
        """
        Process each blob file in the configured file list.

        Args:
            container_client: Azure container client.
            vm_dict: Dictionary to store processed VirtualMachine objects.
            missing_region_vm_count: Dictionary to track missing regions.
            missing_blobs: Set to track missing blob files.
        """
        total_files = len(self.file_names)
        logger.info("processing %d blob files", total_files)

        for index, blob_path in enumerate(self.file_names, 1):
            logger.debug("processing file %d/%d %s", index, total_files, str(blob_path))

            try:
                blob_data = self._download_blob_data(container_client, str(blob_path))
                if blob_data is None:
                    missing_blobs.add(blob_path)
                    continue

                if not self.process_csv_data(
                    blob_data, vm_dict, missing_region_vm_count
                ):
                    logger.warning("empty or invalid csv data in file %s", blob_path)
                else:
                    logger.debug("successfully processed file %s", blob_path)

            except Exception as e:
                logger.error(
                    "unexpected error processing file %s %s", blob_path, str(e)
                )
                missing_blobs.add(blob_path)

    def _download_blob_data(
        self, container_client: ContainerClient, blob_path: str
    ) -> str | None:
        """
        Download blob data from Azure storage.

        Args:
            container_client: Azure container client.
            blob_path: Path to the blob file.

        Returns:
            Blob data as string, or None if blob not found or decode failed.
        """
        try:
            logger.debug("attempting to download blob %s", blob_path)
            blob_client: BlobClient = container_client.get_blob_client(blob_path)

            if not blob_client.exists():
                logger.warning("blob does not exist %s", blob_path)
                return None

            blob_data: str = blob_client.download_blob().readall().decode("utf-8")  # type: ignore[misc]
            logger.debug(
                "successfully downloaded blob %s %d bytes", blob_path, len(blob_data)
            )
            return blob_data

        except ResourceNotFoundError:
            logger.warning("blob file not found %s", blob_path)
            return None
        except UnicodeDecodeError as e:
            logger.error("failed to decode blob data for %s %s", blob_path, str(e))
            return None
        except Exception as e:
            error_str = str(e)
            if "InvalidResourceName" in error_str:
                logger.error("invalid blob name format for azure %s", blob_path)
                logger.error("error details %s", error_str)
                logger.info(
                    "consider url encoding the blob path or checking the naming convention"
                )
            else:
                logger.error(
                    "unexpected error downloading blob %s %s", blob_path, error_str
                )
            return None

    def _log_processing_results(
        self,
        vm_dict: dict[str, VirtualMachine],
        missing_region_vm_count: dict[str, int],
        missing_blobs: set[str],
    ) -> None:
        """
        Log the results of the processing operation.

        Args:
            vm_dict: Dictionary of processed VirtualMachine objects.
            missing_region_vm_count: Dictionary of missing regions and counts.
            missing_blobs: Set of missing blob files.
        """
        logger.info("processing completed found %d virtual machines", len(vm_dict))

        if missing_blobs:
            logger.warning(
                "missing blob files %d %s", len(missing_blobs), sorted(missing_blobs)
            )

        if missing_region_vm_count:
            log_missing_regions(missing_region_vm_count)

        logger.info("azure compute reader processing finished successfully")
