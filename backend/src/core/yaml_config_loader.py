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
from functools import cached_property
from pydantic import model_validator, ValidationError
from pydantic_settings import BaseSettings

from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import (
    ConfigFileError,
    ConfigValidationError,
    MissingParametersError,
)
from backend.src.core.settings import settings

from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)
from backend.src.core.settings.config_carbon_values import (
    CarbonValuesConfig,
)

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
    provider: str | None = None

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


class SourceConfig(BaseSettings):
    input_path: str | None = None


class OutputConfig(BaseSettings):
    output_path: str | None = None


class DaemonConfig(BaseSettings):
    """
    Configuration for the Carbon Engine daemon.

    Organized into logical sub-configurations:
    - source: Where to read data from (azure blob storage or local files)
    - orchestrator: What kind of resources need to be processed for this daemon
      instance.
    """

    orchestrator: OrchestratorConfig = OrchestratorConfig()
    source: SourceConfig = SourceConfig()
    output: OutputConfig = OutputConfig()

    @model_validator(mode="after")
    def validate_source_configuration(self) -> DaemonConfig:
        """
        Validate daemon configuration parameters.

        Returns:
            The validated model.

        Raises:
            MissingParametersError: If required parameters are missing.
        """

        # Source configuration validation
        if self.source.input_path is None:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS,
                ["input_path"],
            )
        return self

    @model_validator(mode="after")
    def validate_output_configuration(self) -> DaemonConfig:
        """
        Validate daemon configuration parameters.

        Returns:
            The validated model.

        Raises:
            MissingParametersError: If required parameters are missing.
        """

        # Output configuration validation
        if self.output.output_path is None:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS,
                ["output_path"],
            )
        return self

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
            self.orchestrator.list_processors = [
                processor
                for processor in self.orchestrator.list_processors
                if processor in self.orchestrator.list_supported_processors
            ]
        return self

    @property
    def input_path(self) -> str | None:
        """Backward compatibility for input_path."""
        return self.source.input_path

    @property
    def output_path(self) -> str | None:
        """Backward compatibility for output_path."""
        return self.output.output_path


class AppConfig(BaseSettings):
    """Root configuration class containing all Carbon Engine settings."""

    carmen_api: ApiConfig | None = None
    carmen_daemon: DaemonConfig | None = None
    provider_configs: dict[str, AbstractProviderConfig] = {}
    carbon_values_config: CarbonValuesConfig | None = None

    @cached_property
    def zone_aliases(self) -> dict[str, str]:
        """Merged zone-alias map from all provider configs. Built once on first access."""
        result: dict[str, str] = {}
        for provider_config in self.provider_configs.values():
            aliases = provider_config.get_zone_aliases()
            if aliases:
                result.update(aliases)
        return result


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


def load_yaml(path: Path) -> dict:
    """
    Load a YAML configuration file with environment variable substitution.

    Args:
        path (Path): The path to the YAML configuration file.

    Returns:
        The loaded configuration as a dictionary.

    Raises:
        ConfigFileError: If the configuration file is not found or invalid.
        ConfigValidationError: If configuration validation fails.
        MissingParametersError: If required parameters are missing.
    """
    if not path.exists():
        logger.error("Configuration file not found: %s", path)
        raise ConfigFileError(ErrorCode.CONFIG_FILE_MISSING, file_path=path)

    loader = yaml.SafeLoader
    loader.add_constructor("!env", env_constructor)

    try:
        with path.open("r", encoding="utf-8") as file:
            raw_config = yaml.load(file, Loader=loader)  # type: ignore[misc]

        if not raw_config or not isinstance(raw_config, dict):
            logger.error("Configuration file is empty or invalid: %s", path)
            raise ConfigFileError(ErrorCode.CONFIG_INVALID_FILE, file_path=path)

    except yaml.YAMLError as e:
        logger.error("YAML parsing error in %s: %s", path, str(e))
        raise ConfigFileError(ErrorCode.CONFIG_INVALID_YAML, file_path=path) from e
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
        raise ConfigFileError(ErrorCode.CONFIG_INVALID_FILE, file_path=path) from e

    return raw_config


def load_main_config() -> tuple[ApiConfig | None, DaemonConfig | None]:
    """
    Load the main configuration file and validate required sections.

    Returns:
        Tuple containing the API configuration and Daemon configuration objects.

    Raises:
        ConfigFileError: If the configuration file is not found or invalid.
        ConfigValidationError: If configuration validation fails.
        MissingParametersError: If required parameters are missing in the configuration.
    """
    main_config_file = settings.CARMEN_MAIN_CONFIG_FILEPATH
    logger.info(f"main_config_file: {main_config_file}")
    main_config_file_path = Path(main_config_file)

    main_config_raw = load_yaml(main_config_file_path)

    if "carmen_api" not in main_config_raw and "carmen_daemon" not in main_config_raw:
        logger.error(
            "Required configuration sections missing in: %s", main_config_file_path
        )
        raise MissingParametersError(
            ErrorCode.CONFIG_MISSING_PARAMETERS, ["carmen_api", "carmen_daemon"]
        )

    # Fill in APIConfig and DaemonConfig based on data retrieved from config.yaml
    carmen_api = (
        ApiConfig.model_validate(main_config_raw["carmen_api"])
        if "carmen_api" in main_config_raw
        else None
    )
    carmen_daemon = (
        DaemonConfig.model_validate(main_config_raw["carmen_daemon"])
        if "carmen_daemon" in main_config_raw
        else None
    )
    return carmen_api, carmen_daemon


def load_carbon_values_config() -> CarbonValuesConfig:
    """
    Load the carbon values configuration from its YAML file.

    Returns:
        CarbonValuesConfig: The loaded carbon values configuration.
    Raises:
        ConfigFileError: If the configuration file is not found or invalid.
    """
    path = Path(settings.CARMEN_CARBON_VALUES_FILEPATH)
    raw = load_yaml(path)
    return CarbonValuesConfig.model_validate(raw)


def _instantiate_provider_config(name: str, raw: dict) -> AbstractProviderConfig | None:
    """
    Factory function to instantiate a provider configuration from raw YAML data.

    Fully data-driven: any directory under config/cloud_providers/<name>/ with a
    valid YAML file is automatically treated as a supported provider. No code
    change is needed to add a new CSP or on-premises setup.

    Args:
        name (str): The name of the provider (used only for logging).
        raw (dict): The raw configuration data from the provider YAML file.

    Returns:
        AbstractProviderConfig | None: The validated provider configuration, or
        None if the YAML does not conform to the expected schema.
    """
    try:
        return AbstractProviderConfig.model_validate(raw)
    except ValidationError as e:
        logger.warning("Provider '%s' config invalid, skipping: %s", name, e)
        return None


def load_provider_configs() -> dict[str, AbstractProviderConfig]:
    """
    Load provider-specific configuration files.
    Part of multi-provider support implementation, allows to easily add new providers,
    by adding a new yaml file and provider config class,
    and updating _instantiate_provider_config factory.

    Returns:
        dict[str, AbstractProviderConfig]: A dictionary mapping provider names to their configuration objects.
    Raises:
        ConfigFileError: If any provider configuration file is missing or invalid.
        ConfigValidationError: If any provider configuration fails validation.
        MissingParametersError: If required parameters are missing in any provider configuration.
    """
    provider_configs = {}
    provider_config_dir = Path(settings.CARMEN_PROVIDER_CONFIG_FILEPATH)
    for provider_dir in provider_config_dir.iterdir():
        if provider_dir.is_dir():
            yaml_file = provider_dir / f"{provider_dir.name}.yaml"
            raw = load_yaml(yaml_file)
            provider_name = provider_dir.name  # "azure", "aws", "gcp"
            provider_config = _instantiate_provider_config(provider_name, raw)
            # Guard against None in case of unknown provider or not-yet-implemented provider
            if provider_config is not None:
                provider_configs[provider_name] = provider_config

    return provider_configs


@lru_cache()
def load_and_validate_config() -> AppConfig:
    """
    Load and validate the configuration files.

    Returns:
        The validated configuration object.

    """
    carmen_api, carmen_daemon = load_main_config()
    provider_configs = load_provider_configs()
    carbon_values_config = load_carbon_values_config()

    return AppConfig(
        carmen_api=carmen_api,
        carmen_daemon=carmen_daemon,
        provider_configs=provider_configs,
        carbon_values_config=carbon_values_config,
    )


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
        "configuration loaded successfully from: %s",
        settings.CARMEN_MAIN_CONFIG_FILEPATH,
    )
except (ConfigFileError, ConfigValidationError, MissingParametersError) as e:
    logger.error("Failed to load configuration: %s", e.formatted_string)
    sys.exit(1)
except Exception as e:
    logger.error("Unexpected error during configuration loading: %s", str(e))
    sys.exit(1)
