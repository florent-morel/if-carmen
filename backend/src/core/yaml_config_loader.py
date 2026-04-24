"""
Configuration loader for the Carbon Engine.

This module handles loading and validating YAML configuration files with support
for environment variable substitution using the ${VAR_NAME} syntax.
"""

from __future__ import annotations

import logging
import os
import sys
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import model_validator, ValidationError
from pydantic_settings import BaseSettings

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    ConfigFileError,
    ConfigValidationError,
    MissingParametersError,
)
from backend.src.core.settings import settings

from backend.src.core.settings.credentials.credentials_config_azure import (
    AzureCredentialsConfig,
)

logger = logging.getLogger(__name__)


class Labels(BaseSettings):
    """Configuration for Kubernetes labels used in queries and monitoring."""

    app_label: str = "label_app_kubernetes_io/part-of"
    cluster_label: str = "stack"
    pod_label: str = "pod"
    namespace_label: str = "namespace"


class ApiConfig(BaseSettings):
    """Configuration for API-related settings including Thanos integration."""

    thanos_url: str
    authentication: Literal["azure"] | None = None
    credentials: AzureCredentialsConfig | None = None
    scope: str | None = None
    external_labels: dict[str, str]
    labels: Labels = Labels()
    verify_ssl: bool = True

    @model_validator(mode="after")
    def validate_api_config(self) -> ApiConfig:
        """Validates that required credentials are present when using Azure authentication."""
        if self.authentication == "azure" and self.credentials is None:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS,
                ["client_id", "tenant_id", "client_secret"],
            )
        return self


class OrchestratorConfig(BaseSettings):
    """Carbon Daemon Orchestrator configuration."""

    list_supported_processors: list[str] = (
        "Processor_Compute",
        "Processor_Storage",
        "Processor_Misc_Services",
    )
    list_processors: list[str] | None = None


class DaemonConfig(BaseSettings):
    """
    Configuration for the Carbon Engine daemon.

    Organized into logical sub-configurations:
    - source: Where to read data from (azure blob storage or local files)
    - orchestrator: What kind of resources need to be processed for this daemon
      instance.
    """

    orchestrator: OrchestratorConfig = OrchestratorConfig()

    @model_validator(mode="after")
    def validate_daemon_configuration(self) -> DaemonConfig:
        """
        Validate daemon configuration parameters.

        Returns:
            The validated model.

        Raises:
            MissingParametersError: If required parameters are missing.
        """

        # Source configuration validation
        for source in self.list_source_configs:
            source.validate_configuration()

        return self

    #     @model_validator(mode="after")
    #     def validate_source_configuration(self) -> DaemonConfig:
    #         """
    #         Validate source configuration parameters.
    #
    #         Returns:
    #             The validated model.
    #
    #         Raises:
    #             MissingParametersError: If required parameters are missing.
    #         """
    #
    #         if self.source.type == "azure":
    #             # Check Azure credentials
    #             missing_creds: list[str] = []
    #             if not self.credentials.client_id:
    #                 missing_creds.append("client_id")
    #             if not self.credentials.client_secret:
    #                 missing_creds.append("client_secret")
    #             if not self.credentials.tenant_id:
    #                 missing_creds.append("tenant_id")
    #
    #             missing: list[str] = missing_creds
    #
    #             # Check Azure source settings
    #             missing_source: list[str] = []
    #             if not self.source.azure.storage_account_url:
    #                 missing_source.append("storage_account_url")
    #
    #             missing.append(missing_source)
    #
    #             if missing:
    #                 raise MissingParametersError(
    #                     ErrorCode.CONFIG_MISSING_PARAMETERS, missing
    #                 )
    #
    #             if (
    #                 self.source.azure.storage_account_url
    #                 and not self.source.azure.storage_account_url.startswith("https://")
    #             ):
    #                 raise ValueError("storage account url must be a valid https url")
    #
    #         elif self.source.type == "local" and not self.source.input_path:
    #             raise MissingParametersError(
    #                 ErrorCode.CONFIG_MISSING_PARAMETERS, ["input_path"]
    #             )
    #
    #         return self
    #
    #     @model_validator(mode="after")

    @model_validator(mode="after")
    def validate_orchestrator_configuration(self) -> DaemonConfig:
        """
        Validate orchestrator configuration parameters.

        Returns:
            The validated model.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        if not self.orchestrator.list_processors:
            logger.error(
                "No processor found in configuration."
                " Defaulting to Processor_Compute."
            )
            self.orchestrator.list_processors = ["Processor_Compute"]
        else:
            # Check that provided processors are supported.
            for processor in self.orchestrator.list_processors:
                if not self.orchestrator.list_supported_processors.index(processor):
                    logger.error(
                        "Invalid processor found in configuration:"
                        f" {processor}.  Removing it from list."
                    )
                    self.orchestrator.list_processors.remove(processor)

        return self

    @property
    def input_path(self) -> str | None:
        """Backward compatibility for input_path."""
        return self.source.input_path

    @property
    def output_path(self) -> str | None:
        """Backward compatibility for input_path."""
        return self.output.output_path

    @property
    def output_path(self) -> str | None:
        """Backward compatibility for input_path."""
        return self.output.output_path


class AppConfig(BaseSettings):
    """Root configuration class containing all Carbon Engine settings."""

    carmen_api: ApiConfig | None = None
    carmen_daemon: DaemonConfig | None = None


def env_constructor(loader: yaml.SafeLoader, node: yaml.ScalarNode) -> str:
    """
    YAML constructor for environment variable substitution.

    Supports ${VAR_NAME} syntax in YAML files.

    Args:
        loader: The YAML loader instance.
        node: The YAML node being processed.

    Returns:
        The processed string with environment variables substituted.
    """
    pattern = re.compile(r".*?\${(\w+)}.*?")
    value: str = loader.construct_scalar(node)
    matches: list[str] = pattern.findall(value)

    if matches:
        full_value = value
        for var in matches:
            env_value: str = os.environ.get(var, var)
            full_value = full_value.replace(f"${{{var}}}", env_value)
        return full_value

    return value


@lru_cache()
def load_and_validate_config() -> AppConfig:
    """
    Load and validate the configuration file for the Carbon Engine.

    Returns:
        The validated configuration object.

    Raises:
        ConfigFileError: If the configuration file is not found or invalid.
        ConfigValidationError: If configuration validation fails.
        MissingParametersError: If required parameters are missing.
    """
    main_config_file = settings.CARMEN_CONFIG_FILEPATH
    main_config_file_path = Path(main_config_file)

    if not main_config_file_path.exists():
        logger.error("Configuration file not found: %s", main_config_file)
        raise ConfigFileError(ErrorCode.CONFIG_FILE_MISSING, file_path=main_config_file)

    loader = yaml.SafeLoader
    loader.add_constructor("!env", env_constructor)

    try:
        with main_config_file_path.open("r", encoding="utf-8") as file:
            raw_config = yaml.load(file, Loader=loader)  # type: ignore[misc]

        if not raw_config or not isinstance(raw_config, dict):
            logger.error("Configuration file is empty or invalid: %s", main_config_file)
            raise ConfigFileError(
                ErrorCode.CONFIG_INVALID_FILE, file_path=main_config_file
            )

        if "carmen_api" not in raw_config and "carmen_daemon" not in raw_config:
            logger.error(
                "Required configuration sections missing in: %s", main_config_file
            )
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["carmen_api", "carmen_daemon"]
            )

        yaml_config = AppConfig(**raw_config)  # type: ignore[arg-type]

    except yaml.YAMLError as e:
        logger.error("YAML parsing error in %s: %s", main_config_file, str(e))
        raise ConfigFileError(
            ErrorCode.CONFIG_INVALID_YAML, file_path=main_config_file
        ) from e
    except ValidationError as e:
        logger.error("Configuration validation failed: %s", str(e))
        validation_errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        raise ConfigValidationError(
            ErrorCode.CONFIG_VALIDATION_FAILED, validation_errors=validation_errors
        ) from e
    except (ConfigFileError, MissingParametersError):
        raise
    except Exception as e:
        logger.error("Unexpected error loading configuration: %s", str(e))
        raise ConfigFileError(
            ErrorCode.CONFIG_INVALID_FILE, file_path=main_config_file
        ) from e

    return yaml_config


def get_config() -> AppConfig:
    """
    Get the application configuration.

    This function provides a way to access the configuration without
    directly calling the cached loader function.

    Returns:
        The application configuration object.

    Raises:
        FileNotFoundError: If the configuration file is not found.
        ValueError: If there's an error parsing or validating the configuration.
    """
    return load_and_validate_config()


try:
    config = load_and_validate_config()
    logger.info(
        "configuration loaded successfully from: %s", settings.CARMEN_CONFIG_FILEPATH
    )
except (ConfigFileError, ConfigValidationError, MissingParametersError) as e:
    logger.error("Failed to load configuration: %s", e.formatted_string)
    sys.exit(1)
except Exception as e:
    logger.error("Unexpected error during configuration loading: %s", str(e))
    sys.exit(1)
