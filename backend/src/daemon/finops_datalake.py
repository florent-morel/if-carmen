"""
This module handles interactions with a FinOps datalake using Azure Blob Storage.
"""

import csv
import os
import io
import logging
import time
from typing import Dict, List, Any, Set
from collections import defaultdict
import requests
import pandas as pd
import pyarrow.parquet as pq
import pyarrow
from pydantic import ValidationError
from azure.storage.blob import ContainerClient, BlobServiceClient
from azure.identity import ClientSecretCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from backend.src.common.known_exception import KnownException
from backend.src.core.config import settings
from backend.src.daemon.daemon_helpers import (
    log_missing_regions,
    calculate_vm_count_for_missing_regions,
    create_vm,
)
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.schemas.storage_resource import StorageResource
from backend.src.utils.helpers import str_to_float
from backend.src.daemon.storage_helpers import (
    calculate_billing_period_days,
    process_storage_row,
)

logger = logging.getLogger(__name__)


class FinOpsDatalake:
    """
    A class to handle interactions with a FinOps datalake using Azure Blob Storage.

    Attributes:
        storage_account_url (str): The URL of the Azure Storage account.
        container_name_read (str): The name of the container in the Azure Blob Storage to read infrastrucute files.
        container_name_upload (str): The name of the container in the Azure Blob Storage where files will be uploaded.
        azure_instances (pd.DataFrame): The DataFrame containing the "instance-class" data from the
        cloud-metdata-azure-instances.csv file.
        credential (ClientSecretCredential): The client secret credential authenticates as a service principal using a
        client secret
    """

    def __init__(
        self,
        storage_account_url,
        container_name_read,
        container_name_upload,
        client_id,
        secret,
        tenant_id,
    ):
        """
        Initializes the FinOpsDatalake with necessary Azure account details.

        Parameters:
            storage_account_url (str): The URL of the Azure Storage account.
            container_name_read (str): The name of the container in the Azure Blob Storage.
            container_name_upload (str): The name of the container in the Azure Blob Storage where files will be
            uploaded.
            client_id (str): The Azure Active Directory client ID.
            secret (str): The secret key for the client ID.
            tenant_id (str): The Azure Active Directory tenant ID.
        """

        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=secret,
        )
        self.storage_account_url = storage_account_url
        self.container_name_read = container_name_read
        self.container_name_upload = container_name_upload
        self.azure_instances = self.load_azure_instances()

    def upload_file_to_datalake(self, file_path, blob_name):
        """
        Uploads a file to the specified container in the Azure Blob Storage.

        Parameters:
            file_path (str): The path of the file to be uploaded.
            blob_name (str): The path (including filename) where the file will be stored in the blob storage.
        Returns:
            None
        """

        try:
            container_client = ContainerClient(
                account_url=self.storage_account_url,
                container_name=self.container_name_upload,
                credential=self.credential,
            )
            with open(file_path, "rb") as data:
                container_client.upload_blob(name=blob_name, data=data, overwrite=True)
                logger.info(
                    "File '%s' successfully uploaded to FinOps datalake container '%s'.",
                    blob_name,
                    self.container_name_upload,
                )

        except FileNotFoundError as ex:
            logger.exception(
                "File '%s' not found at path '%s'",
                os.path.basename(file_path),
                os.path.dirname(file_path),
            )
            raise KnownException(f"File not found: {file_path}") from ex
        except ValueError as ex:
            logger.exception(
                "Invalid parameter for upload: file_path='%s', blob_name='%s'",
                file_path,
                blob_name,
            )
            raise KnownException(f"Invalid parameter for upload: {str(ex)}") from ex
        except HttpResponseError as ex:
            status_code = getattr(ex, "status_code", "Unknown")
            logger.exception(
                "Azure HTTP error (status %s) while uploading file '%s'",
                status_code,
                blob_name,
            )
            raise KnownException(
                f"Azure service error ({status_code}) while uploading: {blob_name}"
            ) from ex
        except TypeError as ex:
            logger.exception(
                "Type error while uploading file '%s': %s", blob_name, str(ex)
            )
            raise KnownException(f"Type error in upload parameters: {str(ex)}") from ex

    def read_file_from_datalake(
        self, file_dict, destination_folder
    ) -> List[VirtualMachine]:
        """
        Reads a file from the specified container in the Azure Blob Storage.

        Parameters:
            file_dict (Dict[str, List[str]): The dictionary of the files where keys as the file group and values as the
            list of file names
            destination_folder (str): The folder where the downloaded file will be saved.

        Returns:
             List[VirtualMachine]: A list of Virtual machines
        """

        blob_service_client = BlobServiceClient(
            account_url=self.storage_account_url, credential=self.credential
        )

        container_client = blob_service_client.get_container_client(
            self.container_name_read
        )
        missing_cloud_instances: Dict[str, Set[str]] = defaultdict(set)
        missing_blobs: Set[str] = set()
        vm_dict: Dict[str, VirtualMachine] = {}
        missing_region_vm_count: Dict[str, int] = {}
        for file_group in file_dict:
            logger.info("Reading file group '%s'...", file_group)

            for blob_name in file_dict[file_group]:
                blob_path = os.path.join(destination_folder, blob_name)
                blob_client = container_client.get_blob_client(blob_path)

                try:
                    blob_data = blob_client.download_blob().readall().decode("utf-8")

                except ResourceNotFoundError:
                    missing_blobs.add(blob_name)
                    continue

                except TypeError:
                    logger.exception(
                        "Type error processing file from datalake for file group %s",
                        file_group,
                    )
                    raise
                except KeyError:
                    logger.exception(
                        "Key error processing file from datalake for file group %s",
                        file_group,
                    )
                    raise

                if not self.process_vm_csv_data(
                    blob_data, vm_dict, missing_cloud_instances, missing_region_vm_count
                ):
                    logger.warning("Resource is empty! Skipped file: %s", blob_name)

        log_missing_regions(missing_region_vm_count)
        self.create_missing_instances_report(missing_cloud_instances, missing_blobs)

        return list(vm_dict.values())

    @staticmethod
    def create_missing_instances_report(
        missing_cloud_instances: Dict[str, Set[str]], missing_blobs: Set[str]
    ):
        """
        Creates a report of missing cloud instances and blobs.

        Args:
            missing_cloud_instances (Dict[str, Set[str]]):A dictionary with cloud instance keys and sets of missing
            instances.
            missing_blobs (Set[str]): A set of missing blob file names.
        """
        with open(
            os.path.join(settings.FINOPS.REPORT_DIR, "missing_instances_report.txt"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write("Nonexist Cloud Instances:\n")
            total_vms = 0

            for key, instances in missing_cloud_instances.items():
                file.write(f"{key}\n")
                total_vms += len(instances)  # Sum the instances as you iterate

            # Write the total number of instances
            file.write(f"Total excluded VMs: {total_vms}\n\n")

            file.write("Nonexistent files:\n")
            for item in missing_blobs:
                file.write(f"{item}\n")

        logger.info(
            "Missing instances report created with %d cloud instance types and %d missing files.",
            len(missing_cloud_instances),
            len(missing_blobs),
        )

    def process_vm_csv_data(
        self,
        blob_data: str,
        vm_dict: Dict[str, VirtualMachine],
        missing_cloud_instances: Dict[str, Set[str]],
        missing_region_vm_count: Dict[str, int],
    ) -> bool:
        """
        Processes CSV data from the blob and updates the virtual machine dictionary.

        Args:
            missing_region_vm_count (Dict[str, int]): Dictionary with the information of missing regions and
            the corresponding VM count.
            blob_data (str): The CSV data read from the blob, as a string.
            vm_dict (Dict[str, VirtualMachine]): The dictionary containing VirtualMachine objects, indexed by their ID.
            missing_cloud_instances (Dict[str, Set[str]]): The missing cloud instance classes, vm sizes.
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

            if vm_size not in self.azure_instances["instance-class"].values:
                missing_cloud_instances[vm_size].add(vm_id)
                continue

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

    def read_parquet_from_datalake(
        self, folder_path: str, file_name: str
    ) -> List[Dict[Any, Any]]:
        """
        Reads a Parquet file from the specified container in the Azure Blob Storage and extracts specified columns.

        Parameters:
            folder_path (str): The folder path where the file is located.
            file_name (str): The name of the file to read.

        Returns:
            Dict[str, str]: A list of dictionaries containing the extracted data.
        """
        columns_to_read = [
            "Resource Id",
            "Subscription Id",
            "Meter Category",
            "Storage Product",
            "Meter",
            "Resource Region",
            "Storage Disk Size (TB)",
        ]

        try:
            blob_service_client = BlobServiceClient(
                account_url=self.storage_account_url, credential=self.credential
            )

            container_client = blob_service_client.get_container_client(
                self.container_name_read
            )
            blob_path = os.path.join(folder_path, file_name)
            blob_client = container_client.get_blob_client(blob_path)

            try:
                blob_data = blob_client.download_blob().readall()
            except ResourceNotFoundError:
                logger.warning("Resource not found! Skipped file: %s", file_name)
                raise

            try:
                table = pq.read_table(io.BytesIO(blob_data), columns=columns_to_read)
                storage_data = [
                    dict(zip(columns_to_read, row))
                    for row in table.to_pydict().values()
                ]
            except pyarrow.ArrowInvalid as ex:
                logger.exception(
                    "Invalid Parquet data format in file '%s': %s", file_name, str(ex)
                )
                raise
            except ValueError as ex:
                logger.exception(
                    "Value error processing data in file '%s': %s", file_name, str(ex)
                )
                raise

            return storage_data

        except (IOError, OSError):
            logger.exception("I/O error reading file '%s'", file_name)
            raise
        except AttributeError:
            logger.exception("Attribute error processing file '%s'", file_name)
            raise
        except Exception:
            logger.exception(
                "Unexpected error reading file '%s' from datalake", file_name
            )
            raise

    def process_storage_csv(
        self, csv_data: str, storage_dict: Dict[str, StorageResource]
    ) -> bool:
        """
        Parse CSV data into StorageResource objects.

        Args:
            csv_data: Raw CSV data as string
            storage_dict: Dictionary to store processed storage resources

        Returns:
            bool: True if data was found and processed, False otherwise
        """
        rows = csv_data.splitlines()
        if len(rows) <= 1:
            return False

        csv_reader = csv.DictReader(rows)
        data_found = False

        # Debug counters
        total_rows = 0
        total_storage_rows = 0
        not_storage_rows = 0
        disk_rows = 0
        excluded_rows = 0

        billing_period_days = calculate_billing_period_days(csv_data)

        logger.info("Processing CSV...")

        for row in csv_reader:
            total_rows += 1

            # Filter for MeterCategory = "Storage"
            meter_category = row.get("MeterCategory", "").lower()
            if "storage" not in meter_category:
                not_storage_rows += 1
                continue

            total_storage_rows += 1

            # Process storage row using helper
            try:
                if process_storage_row(row, billing_period_days, storage_dict):
                    disk_rows += 1
                    data_found = True
                else:
                    excluded_rows += 1
            except Exception as e:
                logger.exception(
                    "Error processing storage row %s: %s",
                    row.get("LineNumber", ""),
                    str(e),
                )
                excluded_rows += 1
                continue

        logger.info("CSV processed")

        # Summary logging
        logger.debug("Storage processing summary:")
        logger.debug("  Total rows: %s", total_rows)
        logger.debug("  Total Storage rows: %s", total_storage_rows)
        logger.debug("  Not Storage rows: %s", not_storage_rows)
        logger.debug("  Excluded rows: %s", excluded_rows)
        logger.debug("  Disk rows (processed): %s", disk_rows)
        logger.debug("  Billing period days: %s", billing_period_days)

        return data_found

    @staticmethod
    def create_co2_report(
        vms: List[VirtualMachine],
        storage_resources: List[StorageResource],
        date: str,
        out_file: str,
    ):
        """
        Creates a CSV report containing all resource types.
        Handles VMs, Storage, and future resource categories in one file.
        """
        vms = vms or []
        storage_resources = storage_resources or []

        logger.info(
            "Creating CSV report with %d VMs and %d storage resources...",
            len(vms),
            len(storage_resources),
        )
        start = time.time()

        with open(out_file, mode="w", newline="", encoding="utf-8") as report:
            writer = csv.writer(report)
            writer.writerows(settings.FINOPS.REPORT_HEADERS)

            total_carbon = 0
            total_energy = 0

            # Separate counters for VMs and Storage
            vm_carbon = 0
            storage_carbon = 0
            vm_energy = 0
            storage_energy = 0

            # Add VMs
            for vm in vms:
                vm.total_carbon_emitted = (
                    vm.total_carbon_operational + vm.total_carbon_embodied
                )
                vm_carbon += vm.total_carbon_emitted
                vm_energy += vm.total_energy_consumed

                row = [
                    # Common columns
                    date,
                    "VM",
                    vm.id,
                    vm.name,
                    vm.region,
                    vm.subscription,
                    vm.total_energy_consumed,
                    vm.total_carbon_operational,
                    vm.total_carbon_embodied,
                    vm.total_carbon_emitted,
                    vm.carbon_intensity,
                    # VM columns
                    vm.vm_size,
                    vm.service,
                    vm.instance,
                    vm.environment,
                    vm.partition,
                    vm.component,
                    # Storage columns
                    "",
                    "",
                    "",
                ]
                writer.writerow(row)

            # Add Storage
            for storage in storage_resources:
                storage.total_carbon_emitted = (
                    storage.total_carbon_operational + storage.total_carbon_embodied
                )
                storage_carbon += storage.total_carbon_emitted
                storage_energy += storage.total_energy_consumed

                row = [
                    # Common columns
                    date,
                    "Storage",
                    storage.id,
                    storage.name,
                    storage.region,
                    storage.subscription,
                    storage.total_energy_consumed,
                    storage.total_carbon_operational,
                    storage.total_carbon_embodied,
                    storage.total_carbon_emitted,
                    storage.carbon_intensity,
                    # VM columns
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    # Storage columns
                    storage.storage_type,
                    storage.replication_type,
                    storage.size_gb,
                ]
                writer.writerow(row)

            # Calculate totals
            total_carbon = vm_carbon + storage_carbon
            total_energy = vm_energy + storage_energy

        elapsed_time = time.time() - start
        logger.info("CSV report created in %.2f seconds", elapsed_time)
        logger.info(
            "  Resources: %d VMs + %d Storage = %d total",
            len(vms),
            len(storage_resources),
            len(vms) + len(storage_resources),
        )
        logger.info(
            "  Energy breakdown: %.2f kWh VMs + %.2f kWh Storage = %.2f kWh total",
            vm_energy,
            storage_energy,
            total_energy,
        )
        logger.info(
            "  Carbon breakdown: %.0f gCO2 VMs + %.0f gCO2 Storage = %.0f gCO2 total",
            vm_carbon,
            storage_carbon,
            total_carbon,
        )
        logger.info("Report saved to: %s", out_file)


    @staticmethod
    def load_azure_instances() -> pd.DataFrame:
        """
        Loads Azure instances from a specified CSV file located at a URL.

        This method attempts to access the URL specified in the settings, checks if the url is accessible,
        and then loads the "instance-class" column from the CSV file into a pandas DataFrame.

        Returns:
            pd.DataFrame: The DataFrame containing the "instance-class" data from the CSV file.

        Raises:
            KnownException:If there is an error in accessing the URL or reading the CSV file,
            the exception is logged and re-raised as a KnownException.
        """

        url = settings.IF_CLOUD_METADATA_FILEPATH
        try:
            response = requests.head(url, timeout=10)
            response.raise_for_status()
            instance_class_df = pd.read_csv(url, usecols=["instance-class"])
            return instance_class_df
        except requests.exceptions.RequestException:
            logger.exception(
                "Error loading the cloud-metdata-azure-instances.csv file from web"
            )
            raise
