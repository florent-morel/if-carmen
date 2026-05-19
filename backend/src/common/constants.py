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

# Reader Storage constants
CSV_PATH: str = "CSV_PATH"
CSV_FILE_TEST: str = "etc/sample_data/test_data/storage_test.csv"
CSV_FILE_ENCODING: str = "utf-8"

HOURLY_INTERVAL_SECONDS: int = 3600
DAILY_SECONDS: int = 86400
SAMPLING_RATE_IN_SECONDS = 86400  # 24 hours
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
    "cost-model-plugin/build",
)

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
