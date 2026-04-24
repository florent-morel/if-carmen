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

from backend.src.core.settings.upload.abstract_credentials_config import (
    AbstractCredentialsConfig
)

from backend.src.core.settings.upload.abstract_source_config import (
    AbstractSourceConfig
)

from backend.src.core.settings.source.source_config_local import (
    LocalSourceConfig
)

from backend.src.core.settings.upload.abstract_upload_config import (
    AbstractUploadConfig
)

from backend.src.core.settings.upload.upload_config_local import (
    LocalUploadConfig
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
    credentials: AzureCredentials | None = None
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


class UploadConfig(BaseSettings):
    """Upload destination configuration."""

    type: Literal["azure", "local"] = "local"
    azure: AzureUploadConfig = AzureUploadConfig()
    local: LocalUploadConfig = LocalUploadConfig()


class OrchestratorConfig(BaseSettings):
    """Carbon Daemon Orchestrator configuration."""

    list_supported_processors: list[str] = ("Processor_Compute",
                                             "Processor_Storage")
    list_processors: list[str] | None = None


class DaemonConfig(BaseSettings):
    """
    Configuration for the Carbon Engine daemon.

    Organized into logical sub-configurations:
    - credentials: Azure authentication (shared between source and upload)
    - source: Where to read data from (azure blob storage or local files)
    - upload: Where to write reports to (azure blob storage or local files)
    - orchestrator: What kind of resources need to be processed for this daemon
      instance.
    """

    credentials: AzureCredentials = AzureCredentials()
    # TODO: check how to make this dynamic from conf file
    # TODO: support Azure config
    # TODO: create a list of source configs
    source: AbstractSourceConfig = LocalSourceConfig()
    list_source_configs: list[AbstractSourceConfig] = source
    # TODO: check how to make this dynamic from conf file
    # TODO: support Azure config
    # TODO: create a list of upload configs
    upload: AbstractUploadConfig = LocalUploadConfig()
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
        # Credentials are validated inside the source validation
        for source in self.list_source_configs:
            source.validate_configuration()

        # Upload configuration validation
        # Credentials are validated inside the upload validation
        self.upload.validate_configuration()

        return self

    @model_validator(mode="after")
    def validate_source_configuration(self) -> DaemonConfig:
        """
        Validate source configuration parameters.

        Returns:
            The validated model.

        Raises:
            MissingParametersError: If required parameters are missing.
        """
        # Validate file_names
        if not self.source.file_names:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["file_names"]
            )

        if self.source.type == "azure":
            # Check Azure credentials
            missing_creds: list[str] = []
            if not self.credentials.client_id:
                missing_creds.append("client_id")
            if not self.credentials.client_secret:
                missing_creds.append("client_secret")
            if not self.credentials.tenant_id:
                missing_creds.append("tenant_id")

            missing: list[str] = missing_creds

            # Check Azure source settings
            missing_source: list[str] = []
            if not self.source.azure.storage_account_url:
                missing_source.append("storage_account_url")
            if not self.source.azure.container_name_read:
                missing_source.append("container_name_read")

            missing.append(missing_source)

            if missing:
                raise MissingParametersError(
                    ErrorCode.CONFIG_MISSING_PARAMETERS, missing
                )

            if (
                self.source.azure.storage_account_url
                and not self.source.azure.storage_account_url.startswith("https://")
            ):
                raise ValueError("storage account url must be a valid https url")

        elif self.source.type == "local" and not self.source.local.source_path:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["source_path"]
            )

        return self

    @model_validator(mode="after")
    def validate_upload_configuration(self) -> DaemonConfig:
        """
        Validate upload configuration parameters.

        Returns:
            The validated model.

        Raises:
            ValueError: If required parameters are missing for the specified upload type.
        """
        if self.upload.type == "azure":
            # Check Azure credentials (shared with source)
            missing_creds: list[str] = []
            if not self.credentials.client_id:
                missing_creds.append("client_id")
            if not self.credentials.client_secret:
                missing_creds.append("client_secret")
            if not self.credentials.tenant_id:
                missing_creds.append("tenant_id")

            # Check Azure upload settings
            missing_upload: list[str] = []
            if not self.upload.azure.container_name_upload:
                missing_upload.append("container_name_upload")

            missing: list[str] = missing_creds + missing_upload
            if missing:
                raise MissingParametersError(
                    ErrorCode.CONFIG_MISSING_PARAMETERS, missing
                )

        elif self.upload.type == "local" and not self.upload.local.upload_path:
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["upload_path"]
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
            logger.error("No processor found in configuration."
                         " Providing hard-coded list: Processor_Compute.")
            self.orchestrator.list_processors = ["Processor_Compute"]
        else:
            # Check that provide processors are supported.
            for processor in self.orchestrator.list_processors:
                if not self.orchestrator.list_supported_processors.index(processor):
                    logger.error("Invalid processor found in configuration:"
                        f" {processor}.  Removing it from list.")
                    self.orchestrator.list_processors.remove(processor)

        return self

    @property
    def source_type(self) -> Literal["azure", "local"]:
        """Backward compatibility for source_type."""
        return self.source.type

    @property
    def upload_type(self) -> Literal["azure", "local"]:
        """Backward compatibility for upload_type."""
        return self.upload.type

    @property
    def client_id(self) -> str | None:
        """Backward compatibility for client_id."""
        return self.credentials.client_id

    @property
    def client_secret(self) -> str | None:
        """Backward compatibility for client_secret."""
        return self.credentials.client_secret

    @property
    def tenant_id(self) -> str | None:
        """Backward compatibility for tenant_id."""
        return self.credentials.tenant_id

    @property
    def storage_account_url(self) -> str | None:
        """Backward compatibility for storage_account_url."""
        return self.source.azure.storage_account_url

    @property
    def container_name_read(self) -> str | None:
        """Backward compatibility for container_name_read."""
        return self.source.azure.container_name_read

    @property
    def container_name_upload(self) -> str | None:
        """Backward compatibility for container_name_upload."""
        return self.upload.azure.container_name_upload

    @property
    def source_path(self) -> str | None:
        """Backward compatibility for source_path."""
        return self.source.local.source_path

    @property
    def upload_path(self) -> str | None:
        """Backward compatibility for upload_path."""
        return self.upload.local.upload_path

    @property
    def file_names(self) -> list[str]:
        """Backward compatibility for file_names."""
        return self.source.file_names


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
    config_file = settings.CARMEN_CONFIG_FILEPATH
    path = Path(config_file)

    if not path.exists():
        logger.error("Configuration file not found: %s", config_file)
        raise ConfigFileError(ErrorCode.CONFIG_FILE_MISSING, file_path=config_file)

    loader = yaml.SafeLoader
    loader.add_constructor("!env", env_constructor)

    try:
        with path.open("r", encoding="utf-8") as file:
            raw_config = yaml.load(file, Loader=loader)  # type: ignore[misc]

        if not raw_config or not isinstance(raw_config, dict):
            logger.error("Configuration file is empty or invalid: %s", config_file)
            raise ConfigFileError(ErrorCode.CONFIG_INVALID_FILE, file_path=config_file)

        if "carmen_api" not in raw_config and "carmen_daemon" not in raw_config:
            logger.error("Required configuration sections missing in: %s", config_file)
            raise MissingParametersError(
                ErrorCode.CONFIG_MISSING_PARAMETERS, ["carmen_api", "carmen_daemon"]
            )

        yaml_config = AppConfig(**raw_config)  # type: ignore[arg-type]

    except yaml.YAMLError as e:
        logger.error("YAML parsing error in %s: %s", config_file, str(e))
        raise ConfigFileError(
            ErrorCode.CONFIG_INVALID_YAML, file_path=config_file
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
            ErrorCode.CONFIG_INVALID_FILE, file_path=config_file
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
