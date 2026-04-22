"""
Config module including all the settings of the Carbon Engine
"""

from __future__ import annotations

import logging
import os
import os.path
from functools import lru_cache
from pathlib import Path
from datetime import datetime
from typing import Any
import colorlog
import urllib3
from pydantic_settings import BaseSettings
from pydantic import field_validator
from backend.src.common.enums import LogLevel
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import ConfigValidationError
from backend.src.utils.helpers import read_file

logger = logging.getLogger(__name__)


class FastAPIConfig(BaseSettings):
    """
    Configuration class for FastAPI settings.
    """

    API_STR: str = "/api"
    TITLE: str = "Carbon Engine API"
    DESCRIPTION: str = "The Green Software Foundation's if-carmen"
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

    CLUSTER_GROUPING_LEVEL: int

    # pylint: disable=no-self-argument
    @field_validator("CLUSTER_GROUPING_LEVEL")
    def check_cluster_group_level(cls, level: int) -> int:
        """
        Validates the clustering grouping level.

        Args:
            level: The clustering grouping level to validate.

        Returns:
            int: The validated clustering grouping level.

        Raises:
            ValueError: If the level is not greater than 0.
        """
        if level <= 0:
            raise ValueError("CLUSTER_GROUPING_LEVEL must be greater than 0")
        return level


class ReportConfig(BaseSettings):
    """
    Configuration class for FinOps settings.
    """

    COMMON: str = "COMMON"
    COMPUTE: str = "COMPUTE"
    STORAGE: str = "STORAGE"
    MISC_SERVICES: str = "MISC_SERVICES"

    # Common columns
    COMMON_DATE: str = "COMMON_DATE"
    COMMON_RESOURCE_TYPE: str = "COMMON_RESOURCE_TYPE"
    COMMON_ID: str = "COMMON_ID"
    COMMON_NAME: str = "COMMON_NAME"
    COMMON_REGION: str = "COMMON_REGION"
    COMMON_SUBSCRIPTION: str = "COMMON_SUBSCRIPTION"
    COMMON_ENERGY: str = "COMMON_ENERGY"
    COMMON_OPERATIONAL_CARBON: str = "COMMON_OPERATIONAL_CARBON"
    COMMON_EMBODIED_CARBON: str = "COMMON_EMBODIED_CARBON"
    COMMON_TOTAL_CARBON: str = "COMMON_TOTAL_CARBON"
    COMMON_CARBON_INTENSITY: str = "COMMON_CARBON_INTENSITY"

    # VM columns
    COMPUTE_VM_SIZE: str = "COMPUTE_VM_SIZE"
    COMPUTE_SERVICE: str = "COMPUTE_SERVICE"
    COMPUTE_INSTANCE: str = "COMPUTE_INSTANCE"
    COMPUTE_ENVIRONMENT: str = "COMPUTE_ENVIRONMENT"
    COMPUTE_PARTITION: str = "COMPUTE_PARTITION"
    COMPUTE_COMPONENT: str = "COMPUTE_COMPONENT"

    # Storage columns
    STORAGE_TYPE: str = "STORAGE_TYPE"
    STORAGE_REPLICATION_TYPE: str = "STORAGE_REPLICATION_TYPE"
    STORAGE_SIZE_GB: str = "STORAGE_SIZE_GB"

    # Misc services columns
    MISC_SERVICES_COST: str = "MISC_SERVICES_COST"

    HEADER = {
        # Common columns
        COMMON: {
           COMMON_DATE: "Date",
           COMMON_RESOURCE_TYPE: "ResourceType",
           COMMON_ID: "Id",
           COMMON_NAME: "Name",
           COMMON_REGION: "Region",
           COMMON_SUBSCRIPTION: "Subscription",
           COMMON_ENERGY: "EnergyKWH",
           COMMON_OPERATIONAL_CARBON: "OperationalCarbonGramsCO2eq",
           COMMON_EMBODIED_CARBON: "EmbodiedCarbonGramsCO2eq",
           COMMON_TOTAL_CARBON: "TotalCarbonGramsCO2eq",
           COMMON_CARBON_INTENSITY: "CarbonIntensity",
        },
        # VM columns
        COMPUTE: {
           COMPUTE_VM_SIZE: "VMSize",
           COMPUTE_SERVICE: "Service",
           COMPUTE_INSTANCE: "Instance",
           COMPUTE_ENVIRONMENT: "Environment",
           COMPUTE_PARTITION: "Partition",
           COMPUTE_COMPONENT: "Component",
        },
        # Storage columns
        STORAGE: {
           STORAGE_TYPE: "StorageType",
           STORAGE_REPLICATION_TYPE: "ReplicationType",
           STORAGE_SIZE_GB: "SizeGB",
        },
        # Misc services columns
        MISC_SERVICES: {
            MISC_SERVICES_COST: "ServicesCost",
        },
    }


    REPORT_HEADERS: list[list[str]] = [
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
            # Misc services columns
            "ServicesCost",
        ]
    ]

    COST_REPORT_HEADERS: list[list[str]] = [
        [
            "Date",
            "Id",
            "Name",
            "Region",
            "Subscription",
            "CarbonIntensity",
            "ServicesCost",
            "EnergyKWH",
            "OperationalCarbonGramsCO2eq",
            "EmbodiedCarbonGramsCO2eq",
        ]
    ]


class Settings(BaseSettings):
    """
    Main settings class for the Carbon Engine.
    """

    FASTAPI: FastAPIConfig = FastAPIConfig()
    THANOS: ThanosConfig
    FINOPS: ReportConfig
    UVICORN: UvicornConfig
    TEST_ENV: bool = os.getenv("TEST_ENV", "False").lower() in ("true", "1", "t")
    LOG_LEVEL: LogLevel = LogLevel.INFO
    IF_CLOUD_METADATA_FILEPATH: str = (
        "https://raw.githubusercontent.com/Green-Software-Foundation/if-data/main/cloud"
        "-metdata-azure-instances.csv"
    )
    CARMEN_CONFIG_FILEPATH: str = os.getenv("CARMEN_CONFIG_FILEPATH", "config.yaml")


def configure_logger(validated_settings: Settings) -> None:
    """
    Configures the logger based on the provided settings.

    Args:
        validated_settings: The settings object containing logger configuration.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("msal").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)

    # Set log level according to configuration
    log_level: int = getattr(logging, validated_settings.LOG_LEVEL.value)

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
        ConfigValidationError: If the settings cannot be validated.
    """

    json_dict: dict[str, Any] = read_file(
        os.path.join(Path(__file__).parent, "settings.json")
    )
    try:
        validated_settings = Settings.model_validate(json_dict)
        configure_logger(validated_settings)
        logger.info("Settings validated.")
    except ValueError as e:
        logger.exception("Settings validation failed")
        validation_errors = [str(e)]
        raise ConfigValidationError(
            ErrorCode.CONFIG_VALIDATION_FAILED,
            validation_errors=validation_errors,
        ) from e
    return validated_settings


try:
    settings = get_settings()
except ConfigValidationError as e:
    logger.error("Failed to validate settings: %s", e.formatted_string)
    os._exit(1)
except Exception as e:
    logger.exception("Failed to get settings: %s", str(e))
    os._exit(1)
