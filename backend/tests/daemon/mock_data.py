
"""
This file contains the necessary mocks for the methods in FinopsDatalake class.
"""

from datetime import datetime
import os
import csv
import re

from backend.src.common.constants import CARBON_INTENSITY_EUROPE
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.utils.helpers import str_to_float


def read_sample_vm_data(file_dict, _destination_forlder):
    """
    Reads VM data from multiple hourly sample CSV files and merges all hourly entries for each VM into a single object.
    """
    vms_dict = {}
    for group, files in file_dict.items():
        print(f"Reading file group '{group}'...")
        for file_name in files:
            process_file(file_name, vms_dict)
    return list(vms_dict.values())


def process_file(file_name, vms_dict):
    """
    Processes a file by extracting the hour from the file name, determining the sample file path,
    and reading and processing the CSV file if it exists.
    Args:
        file_name (str): The name of the file to process.
        vms_dict (dict): A dictionary to store the processed data.
    Returns:
        None
    """
    hour = extract_hour_from_file_name(file_name)
    sample_file = get_sample_file_path(hour)
    print(f"Attempting to read file: {file_name} -> {sample_file}")
    if os.path.exists(sample_file):
        read_and_process_csv(sample_file, vms_dict)
    else:
        print(f"Sample file not found: {sample_file}")


def get_sample_file_path(hour):
    """
    Returns the path to the sample file for the given hour.
    Args:
        hour (int): The hour for which to get the sample file path.
    Returns:
        str: The path to the sample file.
    """
    return os.path.join(
        os.path.dirname(__file__), "test_data", f"vm_usage_hour_{hour}.csv"
    )


def read_and_process_csv(sample_file, vms_dict):
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
            process_csv_row(row, vms_dict)
        if not rows_found:
            print(f"Resource is empty! Skipped file: {sample_file}")


def process_csv_row(row, vms_dict):
    """
    Processes a single row of CSV data and updates the virtual machines dictionary.
    Args:
        row (dict): A dictionary representing a row of CSV data with keys such as "Id", "AverageCpuPercentage",
        and "Time".
        vms_dict (dict): A dictionary where the keys are VM IDs and the values are VirtualMachine objects.
    Returns:
        None
    """

    vm_id = row.get("Id", "")
    avg_cpu = (
        str_to_float(row["AverageCpuPercentage"]) / 100
        if row["AverageCpuPercentage"]
        else 0
    )
    time_point = (
        row["Time"] if "Time" in row and row["Time"] else datetime.now().isoformat()
    )
    storage = str_to_float(row["DiskSizeGb"])

    if vm_id in vms_dict:
        vms_dict[vm_id].cpu_util.append(avg_cpu)
        vms_dict[vm_id].time_points.append(time_point)
        vms_dict[vm_id].storage_size.append(storage)
    else:
        new_vm = create_virtual_machine(row)
        new_vm.cpu_util.append(avg_cpu)
        new_vm.time_points.append(time_point)
        new_vm.storage_size.append(storage)
        new_vm.pue = 1.185
        new_vm.carbon_intensity = CARBON_INTENSITY_EUROPE
        vms_dict[vm_id] = new_vm


def create_virtual_machine(row):
    """
    Creates a VirtualMachine instance from a given row of data.
    """

    return VirtualMachine(
        id=row["Id"],
        region=row["Region"],
        vm_size=row["Size"],
        service=row["Service"] if row["Service"] != "-" else "",
        component=row["Component"] if row["Component"] != "-" else "",
        subscription=row["Subscription"] if row["Subscription"] != "-" else "",
        name=row["Name"],
        instance=row["Instance"] if row["Instance"] != "-" else "",
        environment=row["Environment"] if row["Environment"] != "-" else "",
        partition=row["Partition"] if row["Partition"] != "-" else "",
        storage_size=[],
        carbon_intensity=319,
    )


def extract_hour_from_file_name(file_name):
    """
    Extracts the hour from a file name like usage_YYYY-MM-DD_H.csv
    Example: usage_2024-12-09_0.csv -> hour = 0
    """
    match = re.search(r"-(\d{2})\.csv", file_name)
    if match:
        return int(match.group(1))
    return 0
