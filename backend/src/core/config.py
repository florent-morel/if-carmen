"""
Config module including all the settings of the Carbon Engine
"""

import logging
import os.path
from functools import lru_cache
from pathlib import Path
from datetime import datetime

from os import getenv
import sys
from typing import List

import colorlog
import urllib3
from pydantic_settings import BaseSettings
from pydantic import field_validator
from backend.src.common.enums import LogLevel
from backend.src.common.known_exception import KnownException
from backend.src.utils.helpers import read_file

logger = logging.getLogger(__name__)


class FastAPIConfig(BaseSettings):
    """
    Configuration class for FastAPI settings.
    """

    API_STR: str = "/api"
    TITLE: str = "Carbon Engine API"
    DESCRIPTION: str = "The Amadeus Software Carbon Footprint initiative"
    DOCS_URL: str = f"{API_STR}/docs"
    REDOCS_URL: str = f"{API_STR}/redocs"
    OPENAPI_URL: str = f"{API_STR}/openapi"


class UvicornConfig(BaseSettings):
    """
    Configuration class for Uvicorn settings.
    """

    HOST: str
    PORT: int
    RELOAD: bool
    TIME_OUT: int


class ThanosConfig(BaseSettings):
    """
    Configuration class for Thanos settings.
    """

    # by default
    TENANT_ID: str = getenv("TENANT_ID")
    SCOPE: str = "f47334a5-9498-422e-a2f0-31b74e9220dd/.default"
    CLIENT_ID: str = getenv("CLIENT_ID")
    CLIENT_SECRET: str = getenv("CLIENT_SECRET")
    AUTHORITY: str = f"https://login.microsoftonline.com/{TENANT_ID}"
    ENDPOINT_TIME_SERIES: str = (
        "https://thanos-world.argos.global.amadeus.net/api/v1/query_range"
    )
    ENDPOINT_TIME_POINT: str = (
        "https://thanos-world.argos.global.amadeus.net/api/v1/query"
    )
    CLUSTER_GROUPING_LEVEL: int

    # pylint: disable=no-self-argument
    @field_validator("CLUSTER_GROUPING_LEVEL")
    def check_cluster_group_level(cls, level):
        """
        Validates the clustering grouping level.
        """
        if level <= 0:
            raise ValueError("CLUSTER_GROUPING_LEVEL must be greater than 0")
        return level


class ReefBiConfig(BaseSettings):
    """
    Configuration class for ReefBi settings.
    """

    STORAGE_ACCOUNT_NAME: str = "stpneccpcba01ccpapp1aree"
    CONTAINER_NAME: str = "carbon-footprint"


class FinOpsConfig(BaseSettings):
    """
    Configuration class for FinOps settings.
    """

    STORAGE_ACCOUNT_URL: str = "https://finops1agobsa3b99861d983.blob.core.windows.net/"
    CONTAINER_NAME_UPLOAD: str = "green-prd-rawamacarbonme"
    CONTAINER_NAME_READ: str = "green-prd-curadpazvmusg"
    CONTAINER_NAME_STORAGE: str = "orange-prd-curamaazbilldaily"
    FOLDER_FORMAT: str = (
        "format={format}/version={version}/year={year}/month={month:02d}/"
    )
    FILE_FORMAT: str = "{group}_vm_usage-{year}-{month:02d}-{day:02d}-{counter:02d}.csv"
    FILE_STORAGE_FORMAT: str = "az_adp_final_bill-{year}-{month:02d}-{day:02d}.parquet"
    FILE_GROUPS: list[str]
    REPORT_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "daemon", "report"
    )
    REPORT_HEADERS: List[List[str]] = [
        [
            # Common columns
            "Date",
            "ResourceType",
            "Id",
            "Name",
            "Region",
            "Subscription",
            "EnergyKWH",
            "OperationalCarbonGramsCO2eq",
            "EmbodiedCarbonGramsCO2eq",
            "TotalCarbonGramsCO2eq",
            "CarbonIntensity",
            # VM columns
            "VMSize",
            "Service",
            "Instance",
            "Environment",
            "Partition",
            "Component",
            # Storage columns
            "StorageType",
            "ReplicationType",
            "SizeGB",
        ]
    ]
    COST_REPORT_HEADERS: List[List[str]] = [
        [
            "Date",
            "Id",
            "Name",
            "Region",
            "Subscription",
            "CarbonIntensity",
            "ServicesCostEUR",
            "ServicesEnergykWh",
            "ServicesOperationalCarbonGramsCO2eq",
            "ServicesEmbodiedCarbonGramsCO2eq",
        ]
    ]


class Settings(BaseSettings):
    """
    Main settings class for the Carbon Engine.
    """

    FASTAPI: FastAPIConfig = FastAPIConfig()
    THANOS: ThanosConfig
    REEFBI: ReefBiConfig
    FINOPS: FinOpsConfig
    UVICORN: UvicornConfig
    TEST_ENV: bool = os.getenv("TEST_ENV", "False").lower() in ("true", "1", "t")
    LOG_LEVEL: LogLevel = LogLevel.INFO
    IF_CLOUD_METADATA_FILEPATH: str = (
        "https://raw.githubusercontent.com/Green-Software-Foundation/if-data/main/cloud"
        "-metdata-azure-instances.csv"
    )
    CARMEN_CONFIG_FILEPATH: str = os.getenv("CARMEN_CONFIG_FILEPATH", "config.yaml")


def configure_logger(validated_settings):
    """
    Configures the logger based on the provided settings.

    Args:
        validated_settings (Settings): The settings object containing logger configuration.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("msal").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)

    # Set log level according to configuration
    log_level = getattr(logging, validated_settings.LOG_LEVEL.value)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Basic log format
    log_format = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Add console handler with colors
    console_handler = colorlog.StreamHandler()
    console_format = "%(log_color)s" + log_format
    console_formatter = colorlog.ColoredFormatter(
        console_format,
        datefmt=date_format,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    if validated_settings.TEST_ENV:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "logs",
        )
        os.makedirs(log_dir, exist_ok=True)

        # Create log file with current date
        log_file = os.path.join(
            log_dir, f"carbon_engine_{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, mode="w")
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        logger.info("Log file created at: %s", log_file)

    logger.debug("Logger configured with level %s.", validated_settings.LOG_LEVEL.value)
    logger.debug(
        "Application starting with environment: %s",
        "TEST" if validated_settings.TEST_ENV else "PRODUCTION",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns settings using LRU cache.

    Returns:
        Settings: An instance of Settings class containing the app settings.

    Raises:
        KnownException: If the settings cannot be validated.
    """

    json_dict = read_file(os.path.join(Path(__file__).parent, "config.json"))
    try:
        validated_settings = Settings.model_validate(json_dict)
        configure_logger(validated_settings)
        logger.info("Settings validated.")
    except ValueError as err:
        logger.exception("Settings validation failed")
        raise KnownException("Settings cannot be validated") from err
    return validated_settings


try:
    settings = get_settings()
except KnownException:
    logger.exception("Settings validation error")
    sys.exit(0)
