"""
This file contains all the constants used in the project.
"""

import os
from datetime import timedelta
from backend.src.common.enums import SamplingRate
from enum import Enum
from pathlib import Path

# CPU_MIN_ELECTRICITY_RATIO_AZURE = 0.78  # watt per core
# CPU_MAX_ELECTRICITY_RATIO_AZURE = 3.76  # watt per core
# MEMORY_ELECTRICITY_RATIO_AZURE = 0.392  # watt per GB

# European Average for 2024 (Source: https://ourworldindata.org/grapher/carbon-intensity-electricity)
# Carbon intensity fallback is now loaded from config/carbon_intensity.yaml (default_carbon_intensity)
# CARBON_INTENSITY_EUROPE = 281  # gCO2 per kWh
# CPU_THRESHOLD: int = 1000000  # 1.000.000 cores
# MEMORY_THRESHOLD: int = 100000000000000  # 100.000 TB

RATE_TO_DURATION = {
    SamplingRate.FIFTEEN_SECONDS: timedelta(seconds=15),
    SamplingRate.THIRTY_SECONDS: timedelta(seconds=30),
    SamplingRate.ONE_MINUTE: timedelta(minutes=1),
    SamplingRate.FIVE_MINUTES: timedelta(minutes=5),
    SamplingRate.THIRTY_MINUTES: timedelta(minutes=30),
    SamplingRate.ONE_HOUR: timedelta(hours=1),
    SamplingRate.SIX_HOURS: timedelta(hours=6),
    SamplingRate.ONE_DAY: timedelta(days=1),
}

# Reader constants
CSV_PATH: str = "CSV_PATH"
CSV_FILE_ENCODING: str = "utf-8"


SOURCE_RESOURCE_ID = "ResourceId"
SOURCE_RESOURCE_GROUP = "ResourceGroup"
SOURCE_PROVIDER = "Provider"
SOURCE_REGION = "Region"
SOURCE_NAME = "Name"
SOURCE_SIZE = "Size"
SOURCE_COST = "Cost"
SOURCE_RESOURCE_TYPE = "ResourceType"
SOURCE_RESOURCE_TYPE_COMPUTE = "Compute"
SOURCE_RESOURCE_TYPE_STORAGE = "Storage"
SOURCE_RESOURCE_TYPE_SERVICE = "Service"
SOURCE_PRODUCT_NAME = "ProductName"
SOURCE_METER_NAME = "MeterName"
SOURCE_DATE = "Date"
SOURCE_TIME = "Time"
# TODO: Rename as it is disk size
SOURCE_QUANTITY = "Quantity"
SOURCE_UNIT_OF_MEASURE = "UnitOfMeasure"
SOURCE_STORAGE_SIZE_GB = "StorageSizeGB"
SOURCE_STORAGE_DURATION_SECONDS = "StorageDurationSeconds"
SOURCE_AVG_CPU_PERCENTAGE = "AverageCpuPercentage"
SOURCE_DISK_SIZE_GB = "DiskSizeGb"
SOURCE_NB_VCPUS = "NbVCpus"
UNKNOWN = "Unknown"

# Computation formats
HOURLY_INTERVAL_SECONDS: int = 3600
DAILY_SECONDS: int = 86400
SAMPLING_RATE_IN_SECONDS = 86400  # 24 hours
EXPECTED_LIFESPAN = 126230400  # 4 years in seconds
EXECUTION_DATE: str = "EXECUTION_DATE"
DATE_FORMAT: str = "%Y-%m-%d"
FORMAT_STORAGE_ONE_GIB_PER_HOUR: str = "1 GiB/Hour"
FORMAT_STORAGE_ONE_PER_MONTH: str = "1/Month"
MAX_STORAGE_SIZE_GB_WARNING_THRESHOLD: int = 32767

# TODO: add VM, storage and services chunk size as configurable settings

# TODO: do this in a cleaner way (project root)
current_file = Path(__file__)
project_root = (
    current_file.parent.parent.parent.parent
)  # backend/tests/conftest.py -> carbon-engine/
IF_FILES_DIR = os.path.join(
    # os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    project_root,
    "etc",
    "impact_framework",
)

PLUGIN_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "misc-services-model-plugin/build",
)

# MODELS STRING CONSTANTS
MODELS_INSTANCE_CLASS = "instance-class"
MODELS_CPU_CORES_AVAIL = "cpu-cores-available"
MODELS_CPU_CORES_UTILIZED = "cpu-cores-utilized"
MODELS_CPU_TDP = "cpu-tdp"
MODELS_MEMORY_AVAIL = "memory-available"

#TODO: To be cleaned up. Do we really need singular and plural versions of these constants?
IF_INPUT_INPUT_PARAMETER = "input-parameter"
IF_INPUT_INPUT_PARAMETERS = "input-parameters"
IF_INPUT_OUTPUT_PARAMETER = "output-parameter"
IF_INPUT_OUTPUT_PARAMETERS = "output-parameters"

IF_INPUT_CPU_TDP = "cpu/thermal-design-power"
IF_INPUT_CPU_UTILIZATION = "cpu/utilization"
IF_INPUT_CPU_TDP_RATIO = "tdp-ratio"

IF_INPUT_VCPU_ALLOCATED = "vcpus-allocated"
IF_INPUT_VCPU_TOTAL = "vcpus-total"

IF_INPUT_MEMORY_REQUESTED = "memory/requested"

IF_INPUT_COST = "cost"

IF_INPUT_ENERGY = "energy"
IF_INPUT_ENERGY_TXT = "Energy consumption"
IF_INPUT_ENERGY_KWH = "kWh"
IF_INPUT_PUE = "pue"
IF_INPUT_CPU_SLASH_ENERGY = "cpu/energy"
IF_INPUT_MEMORY_SLASH_ENERGY = "memory/energy"
IF_INPUT_STORAGE_SLASH_ENERGY = "storage/energy"
IF_INPUT_STORAGE_SLASH_REQUESTED = "storage/requested"
IF_INPUT_STORAGE_SLASH_EMBODIED = "storage/embodied-coefficient"
IF_INPUT_DURATION_SLASH_SECONDS = "duration/seconds"
# IF_INPUT_

IF_INPUT_CARBON = "carbon"
IF_INPUT_CARBON_TXT = "Carbon emissions"
IF_INPUT_CARBON_EMBODIED = "carbon-embodied"
IF_INPUT_CARBON_EMBODIED_TXT = "Embodied carbon emissions"
IF_INPUT_CARBON_OPERATIONAL = "carbon-operational"
IF_INPUT_CARBON_OPERATIONAL_TXT = "Operational carbon emissions"
IF_INPUT_CARBON_GCO2 = "gCO2e"


IF_INPUT_RESOURCES_RESERVED = "resources-reserved"
IF_INPUT_RESOURCES_TOTAL = "resources-total"

IF_INPUT_GRID_CARBON_INTENSITY = "grid/carbon-intensity"

IF_INPUT_COMPUTE_ENERGY = "compute-energy"
IF_INPUT_COMPUTE_EMBODIED = "compute-embodied"
IF_INPUT_COMPUTE_COST = "compute-cost"

IF_INPUT_STORAGE_ENERGY = "storage-energy"
IF_INPUT_STORAGE_EMBODIED = "storage-embodied"
IF_INPUT_STORAGE_EMBODIED_TXT = "Storage embodied emissions"
IF_INPUT_STORAGE_COST = "storage-cost"

IF_INPUT_MISC_SERVICES_ENERGY = "misc-services-energy"
IF_INPUT_MISC_SERVICES_ENERGY_TXT = "Total energy consumed for the services"
IF_INPUT_MISC_SERVICES_OPERATIONAL = "misc-services-operational"
IF_INPUT_MISC_SERVICES_EMBODIED = "misc-services-embodied"
IF_INPUT_MISC_SERVICES_CAPEX = "Services capex emissions"
IF_INPUT_MISC_SERVICES_OPEX = "Services opex emissions"

IF_INPUT_CARBON_INTENSITY = "carbon-intensity"

IF_INPUT_TIMESTAMP = "timestamp"
IF_INPUT_SUM = "sum"

CARMEN_LOGO = """
                                                        ##
                                     ###                ###
                                    ####                ####
                                   #####                #####
                                  #####                 ######
                                 #####                 ########
                                 ####                  ########
                                #####                 ##########
                               #####                  ##########
                              #####                  ###########    #
                             #####                   ############   ##
                             ####                   #############    ##
                            #####                  ##############    ##
                           #####                  ################   ###
                          #####                  #################   ####
                         #####                  ############ #####   #####
                         #####                  ############ #####    #####
                        #####                  ############# #####     ####
                        ####                   ############# #####     #####
                       ####                   #############  ####       ####
                       ####                   #############  ####       ####
                       ####                   ############   ####       ####
                       #####                  ############   ###        ####
                        #####                  ##########    ###       #####
                        #####                  ##########    ##       #####
                         #####                 #########    ###      #####
                          #####                 ########    ##      #####
                           #####                 ######    ##      #####
                            #####                %####    ##       #####
                             ####%                ####            #####
                             #####                ###            #####
                              #####              ###            #####
                               #####            ###            #####
                                #####           ##             #####
                                 #####                        #####
                                 #####                       #####
                                  #####                     #####
                                   #####                   #####
                                    ####                   ####
                                     ###                    ###





                         #####     ##     ######  ###   ###  ######  ###   #
                        ##  ##    ####    ##  ##  ###   ###  ##      ###   #
                        #%   ##   ####    ##  ##  ####  ###  ##      ####  #
                       ##         # ##    ##  ##  #### ####  ######  ## ## #
                       ##        ##  ##   #####   ## # ####  ######  ## ## #
                        #    ##  ######   ## ##   ## ### ##  ##      ##  ###
                        ### ##  ##   ##   ##  ##  ## ### ##  ##      ##  ###
                         #####  ##    ##  ##  ##  ##  ## ##  ######  ##   ##
"""
