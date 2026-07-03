"""
This file contains the necessary mocks for the methods in FinopsDatalake class.
"""

from datetime import datetime
import os
import csv
import re
import logging

from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.utils.helpers import str_to_float
from backend.src.daemon.readers.helpers.virtual_machine_helpers import get_row_data
from backend.src.common.constants import (
    SOURCE_PROVIDER,
    SOURCE_NAME,
    SOURCE_RESOURCE_ID,
    SOURCE_RESOURCE_TYPE_SERVICE,
    SOURCE_REGION,
    SOURCE_VM_AVG_CPU_UTIL_PERCENT,
    SOURCE_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_DATE,
    SOURCE_TIME,
    SOURCE_VM_SIZE,
    SOURCE_VM_NB_VCPUS,
    DATE_FORMAT,
    SOURCE_VM_DISK_SIZE_GB,
    UNKNOWN,
)

# Fallback values used when building mock VMs that have no real provider/region data.
_DEFAULT_CARBON_INTENSITY = 281  # gCO2/kWh
_DEFAULT_PUE = 1.5

logger = logging.getLogger(__name__)


def _process_vm_file(file_name, vms_dict, config: DaemonConfig):
    """
    Processes a file by extracting the hour from the file name, determining the sample file path,
    and reading and processing the CSV file if it exists.
    Args:
        file_name (str): The name of the file to process.
        vms_dict (dict): A dictionary to store the processed data.
    Returns:
        None
    """
    hour = _extract_hour_from_file_name(file_name)
    sample_file = _get_vm_sample_file_path(hour, config)
    logger.debug(f"Attempting to read file: {file_name} -> {sample_file}")
    if os.path.exists(sample_file):
        _read_and_process_vm_csv(sample_file, vms_dict)
    else:
        logger.debug(f"Sample file not found: {sample_file}")


def _get_vm_sample_file_path(hour, config: DaemonConfig):
    """
    Returns the path to the sample file for the given hour.
    Args:
        hour (int): The hour for which to get the sample file path.
    Returns:
        str: The path to the sample file.
    """
    return os.path.join(
        os.path.dirname(config.source.input_path), "test_data", f"vm_usage_hour_"
    f"{hour}.csv"
    )


def _read_and_process_vm_csv(sample_file, vms_dict):
    """
    Reads a CSV file and processes each row using the provided dictionary.
    Args:
        sample_file (str): The path to the CSV file to be read.
        vms_dict (dict): A dictionary to store or process the data from the CSV rows.
    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there is an error reading the file.
    """
    with open(sample_file, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        rows_found = False
        for row in csv_reader:
            rows_found = True
            _process_vm_row(row, vms_dict)
        if not rows_found:
            logger.debug(f"Resource is empty! Skipped file: {sample_file}")


def _process_vm_row(row, vms_dict):
    """
    Processes a single row of CSV data and updates the virtual machines dictionary.
    Args:
        row (dict): A dictionary representing a row of CSV data with keys such as "Id", "AverageVmCpuUtilPercent",
        and "Time".
        vms_dict (dict): A dictionary where the keys are VM IDs and the values are VirtualMachine objects.
    Returns:
        None
    """
    vm_id = row.get("Id", "")
    avg_cpu = (
        str_to_float(row["AverageVmCpuUtilPercent"]) / 100
        if row["AverageVmCpuUtilPercent"]
        else 0
    )
    time_point = (
        row["Time"] if "Time" in row and row["Time"] else datetime.now().isoformat()
    )
    storage = str_to_float(row["VmDiskSizeGb"])

    if vm_id in vms_dict:
        vms_dict[vm_id].cpu_util.append(avg_cpu)
        vms_dict[vm_id].time_points.append(time_point)
        vms_dict[vm_id].storage_size.append(storage)
    else:
        new_vm = _create_virtual_machine(row)
        new_vm.cpu_util.append(avg_cpu)
        new_vm.time_points.append(time_point)
        new_vm.storage_size.append(storage)
        vms_dict[vm_id] = new_vm


def _create_virtual_machine(row):
    """Constructs a VirtualMachine from a single CSV row using default fallback values for carbon intensity and PUE."""
    return VirtualMachine(
        id=row[SOURCE_RESOURCE_ID],
        region=row[SOURCE_REGION],
        vm_size=row[SOURCE_VM_SIZE],
        name=get_row_data(row[SOURCE_NAME]),
        provider=get_row_data(row[SOURCE_PROVIDER]),
        storage_size=[],
        pue=_DEFAULT_PUE,
        carbon_intensity=_DEFAULT_CARBON_INTENSITY,
    )


def _extract_hour_from_file_name(file_name):
    """
    Extracts the hour from a file name suffix like "..._<H>.csv".
    Accepts one- or two-digit hours in the 0-23 range.
    Example: vm_usage_hour_0.csv -> hour = 0
    Example: vm_usage_hour_13.csv -> hour = 13
    """
    match = re.search(r"_((?:[01]?\d|2[0-3]))\.csv", file_name)
    if match:
        return int(match.group(1))
    return 0


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

csv_test_csv_path = "etc/sample_data/test_data/storage_test.csv"


def read_sample_storage_data(file_dict, _destination_folder):
    """
    Reads storage data from CSV files and returns a list of StorageResource objects.
    Mirrors read_sample_vm_data — each unique ResourceId maps to one StorageResource.
    """
    storage_dict = {}
    for group, files in file_dict.items():
        logger.info(f"Reading storage file group '{group}'...")
        for file_name in files:
            _process_storage_file(file_name, storage_dict)
    return list(storage_dict.values())


def _process_storage_file(file_name, storage_dict):
    """Resolves the sample file path for a storage file name and delegates to the CSV reader."""
    sample_file = os.path.join(os.path.dirname(
        __file__), "test_data", file_name)
    logger.info(f"Attempting to read storage file: {sample_file}")
    if os.path.exists(sample_file):
        _read_and_process_storage_csv(sample_file, storage_dict)
    else:
        logger.info(f"Storage sample file not found: {sample_file}")


def _read_and_process_storage_csv(sample_file, storage_dict):
    """Opens a storage CSV file and processes each row into storage_dict."""
    with open(sample_file, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        rows_found = False
        for row in csv_reader:
            rows_found = True
            _process_storage_row(row, storage_dict)
        if not rows_found:
            logger.info(f"Storage file is empty! Skipped: {sample_file}")


def _process_storage_row(row, storage_dict):
    """Adds a StorageResource for a new ResourceId; skips rows already present in storage_dict."""
    resource_id = row.get("ResourceId", "")
    if resource_id not in storage_dict:
        storage_dict[resource_id] = _create_storage_resource(row)


def _create_storage_resource(row):
    """
    Creates a StorageResource from input CSV row (storage_test.csv format).
    Columns: TODO
    """
    product_name = row.get("ProductName", "")

    # Derive storage_type from meter/product name
    if "Premium SSD" in product_name or "Premium LRS" in product_name:
        storage_type = "Premium_SSD"
    elif "Ultra" in product_name:
        storage_type = "Ultra_Disk"
    else:
        storage_type = "Standard_HDD"

    # Derive replication type from meter name (LRS, GRS, ZRS, GZRS)
    for rep in ("GZRS", "ZRS", "GRS", "LRS"):
        if rep in product_name:
            replication_type = rep
            break
    else:
        replication_type = "LRS"

    return StorageResource(
        id=row.get("ResourceId", ""),
        name=row.get("ProductName", ""),
        provider=row.get("Provider", ""),
        region=row.get("ResourceLocation", ""),
        storage_type=storage_type,
        replication_type=replication_type,
        size_gb=str_to_float(row.get("Quantity", "0")),
        carbon_intensity=_DEFAULT_CARBON_INTENSITY,
    )


# ---------------------------------------------------------------------------
# Misc Services
# ---------------------------------------------------------------------------


def read_sample_misc_services_data(file_dict, _destination_folder):
    """
    Reads misc_services (Misc Services model) data from CSV files and returns a list of
    MiscServicesResource objects.  Mirrors read_sample_vm_data.
    """
    misc_dict = {}
    for group, files in file_dict.items():
        logger.info(f"Reading misc_services file group '{group}'...")
        for file_name in files:
            _process_misc_services_file(file_name, misc_dict)
    return list(misc_dict.values())


def _process_misc_services_file(file_name, misc_dict):
    """Resolves the sample file path for a misc_services file name and delegates to the CSV reader."""
    sample_file = os.path.join(os.path.dirname(
        __file__), "test_data", file_name)
    logger.info(f"Attempting to read misc_services file: {sample_file}")
    if os.path.exists(sample_file):
        _read_and_process_misc_services_csv(sample_file, misc_dict)
    else:
        logger.info(f"misc_services sample file not found: {sample_file}")


def _read_and_process_misc_services_csv(sample_file, misc_dict):
    """Opens a misc_services CSV file and processes each row into misc_dict."""
    with open(sample_file, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        rows_found = False
        for row in csv_reader:
            rows_found = True
            _process_misc_services_row(row, misc_dict)
        if not rows_found:
            logger.info(f"misc_services file is empty! Skipped: {sample_file}")


def _process_misc_services_row(row, misc_dict):
    """Upserts a MiscServicesResource into misc_dict, accumulating cost across multiple billing rows for the same ResourceId."""
    resource_id = row.get("ResourceId", "")
    if resource_id not in misc_dict:
        misc_dict[resource_id] = _create_misc_services_resource(row)
    else:
        # Accumulate cost across multiple billing rows for the same resource
        misc_dict[resource_id].cost += str_to_float(
            row.get("Cost", "0")
        )


def _create_misc_services_resource(row):
    """
    Creates a MiscServicesResource from input CSV row (misc_services-model format).
    Columns: ResourceId, ProductName, ResourceLocation,
             Date, Cost, ...
    """
    return MiscServicesResource(
        id=row.get("ResourceId", ""),
        name=row.get("ProductName", ""),
        provider=row.get("Provider", ""),
        region=row.get("ResourceLocation", ""),
        carbon_intensity=_DEFAULT_CARBON_INTENSITY,
        cost=str_to_float(row.get("Cost", "0")),
    )
