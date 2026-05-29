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
CSV_FILE_TEST: str = "etc/sample_data/test_data/storage_test.csv"
CSV_FILE_ENCODING: str = "utf-8"


SOURCE_RESOURCE_ID = "ResourceId"
SOURCE_RESOURCE_GROUP = "ResourceGroup"
SOURCE_PROVIDER = "Provider"
SOURCE_SUBSCRIPTION = "Subscription"
SOURCE_SUBSCRIPTION_ID = "SubscriptionId"
SOURCE_REGION = "Region"
SOURCE_NAME = "Name"
SOURCE_SIZE = "Size"
SOURCE_SERVICE = "Service"
SOURCE_COMPONENT = "Component"
SOURCE_INSTANCE = "Instance"
SOURCE_ENVIRONMENT = "Environment"
SOURCE_METER_CATEGORY = "MeterCategory"
SOURCE_BILLING_COST = "BillingCost"
SOURCE_COMPUTE = "Compute"
SOURCE_STORAGE = "Storage"
SOURCE_CONSUMED_SERVICE = "ConsumedService"
SOURCE_PRODUCT_NAME = "ProductName"
SOURCE_METER_NAME = "MeterName"
SOURCE_PARTITION = "Partition"
SOURCE_DATE = "Date"
SOURCE_TIME = "Time"
SOURCE_QUANTITY = "Quantity"
SOURCE_UNIT_OF_MEASURE = "UnitOfMeasure"
SOURCE_AVG_CPU_PERCENTAGE = "AverageCpuPercentage"
SOURCE_DISK_SIZE_GB = "DiskSizeGb"
SOURCE_NB_VCPUS = "NbVCpus"
UNKNOWN = "Unknown"

HOURLY_INTERVAL_SECONDS: int = 3600
DAILY_SECONDS: int = 86400
SAMPLING_RATE_IN_SECONDS = 86400  # 24 hours
EXPECTED_LIFESPAN = 126230400  # 4 years in seconds
EXECUTION_DATE: str = "EXECUTION_DATE"
DATE_FORMAT: str = "%Y-%m-%d"

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

IF_INPUT_MISC_SERVICES_COST = "misc-services-cost"
IF_INPUT_MISC_SERVICES_ENERGY = "misc-services-energy"
IF_INPUT_MISC_SERVICES_ENERGY_TXT = "Total energy consumed for the services"
IF_INPUT_MISC_SERVICES_OPERATIONAL = "misc-services-operational"
IF_INPUT_MISC_SERVICES_EMBODIED = "misc-services-embodied"
IF_INPUT_MISC_SERVICES_CAPEX = "Services capex emissions"
IF_INPUT_MISC_SERVICES_OPEX = "Services opex emissions"

IF_INPUT_CARBON_INTENSITY = "carbon-intensity"

IF_INPUT_TIMESTAMP = "timestamp"
IF_INPUT_SUM = "sum"

# STORAGE_POWER_COEFFICIENT_MAPPING = {  # in kWh/GBh from https://www.cloudcarbonfootprint.org/docs/methodology/#storage
#     "SSD": 0.0000012,
#     "HDD": 0.00000065,
#     "UNKNOWN": 0.000000925,  # Average
# }
#
# STORAGE_EMBODIED_COEFFICIENT_MAPPING = {  # in gCO2e/GB from https://hotcarbon.org/assets/2022/pdf/hotcarbon22-tannu.pdf
#     "SSD": 160,
#     "HDD": 20,
#     "UNKNOWN": 90,  # Average
# }
#
# # Replication factors for different Azure storage types
# # https://docs.google.com/spreadsheets/d/1D7mIGKkdO1djPoMVmlXRmzA7_4tTiGZLYdVbfe85xQM/edit?gid=2008238628#gid=2008238628
# STORAGE_REPLICATION_FACTORS = {
#     "LRS": 3,  # Locally redundant storage - 3 copies in single physical location
#     "ZRS": 3,  # Zone redundant storage - 3 copies across availability zones
#     "GRS": 6,  # Geo redundant storage - 3 primary + 3 secondary copies
#     "RA_GRS": 6,  # Read-access geo redundant - same as GRS
#     "GZRS": 6,  # Geo-zone redundant - 3 copies across zones + 3 secondary
#     "RA_GZRS": 6,  # Read-access geo-zone - same as GZRS
# }
#
# # Azure Disk SKU to size mapping in GiB
# DISK_SKU_SIZE_MAPPING = {
#     # Premium SSD (P series)
#     "P1": 4,
#     "P2": 8,
#     "P3": 16,
#     "P4": 32,
#     "P6": 64,
#     "P10": 128,
#     "P15": 256,
#     "P20": 512,
#     "P30": 1024,
#     "P40": 2048,
#     "P50": 4096,
#     "P60": 8192,
#     "P70": 16384,
#     "P80": 32767,
#     # Standard SSD (E series)
#     "E1": 4,
#     "E2": 8,
#     "E3": 16,
#     "E4": 32,
#     "E6": 64,
#     "E10": 128,
#     "E15": 256,
#     "E20": 512,
#     "E30": 1024,
#     "E40": 2048,
#     "E50": 4096,
#     "E60": 8192,
#     "E70": 16384,
#     "E80": 32767,
#     # Standard HDD (S series)
#     "S4": 32,
#     "S6": 64,
#     "S10": 128,
#     "S15": 256,
#     "S20": 512,
#     "S30": 1024,
#     "S40": 2048,
#     "S50": 4096,
#     "S60": 8192,
#     "S70": 16384,
#     "S80": 32767,
# }
#
# Power usage effectiveness values for different cloud providers are now loaded from
# the provider YAML configs (e.g. config/cloud_providers/azure/azure.yaml)
# PUE_AZURE = 1.185
# PUE_AWS = 1.135
# PUE_GCP = 1.1

# 2024 Data (Source: https://ourworldindata.org/grapher/carbon-intensity-electricity)
# Carbon intensity per Azure region is now loaded from config/carbon_intensity.yaml
# REGION_TO_COUNTRY_CARBON_INTENSITY = {
#     "australiaeast": {"country": "New South Wales", "carbon_intensity": 552},
#     "centralus": {"country": "Iowa", "carbon_intensity": 384},
#     "eastasia": {"country": "Hong Kong", "carbon_intensity": 560},
#     "eastus": {"country": "Virginia", "carbon_intensity": 384},
#     "eastus2": {"country": "Virginia", "carbon_intensity": 384},
#     "francecentral": {"country": "France", "carbon_intensity": 44},
#     "francesouth": {"country": "France", "carbon_intensity": 44},
#     "germanywestcentral": {"country": "Germany", "carbon_intensity": 344},
#     "northcentralus": {"country": "Illinois", "carbon_intensity": 384},
#     "northeurope": {"country": "Ireland", "carbon_intensity": 280},
#     "southeastasia": {"country": "Singapore", "carbon_intensity": 499},
#     "swedencentral": {"country": "Sweden", "carbon_intensity": 36},
#     "uaenorth": {"country": "Dubai", "carbon_intensity": 493},
#     "uksouth": {"country": "London", "carbon_intensity": 211},
#     "westeurope": {"country": "Netherlands", "carbon_intensity": 253},
#     "westus": {"country": "California", "carbon_intensity": 384},
#     "westus2": {"country": "Washington", "carbon_intensity": 384},
#     "westus3": {"country": "Phoenix", "carbon_intensity": 384},
#     "centralindia": {"country": "India", "carbon_intensity": 708},
#     "southindia": {"country": "India", "carbon_intensity": 708},
# }

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
