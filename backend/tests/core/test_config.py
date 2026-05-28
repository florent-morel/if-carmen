"""
Module containing unit tests for the settings configuration of the Carbon Engine.
"""

import logging
from unittest.mock import MagicMock, patch
import pytest
from backend.src.core.settings import configure_logger, get_settings, Settings
from backend.src.common.enums import LogLevel
from backend.src.common.carmen_exception import ConfigValidationError

logger = logging.getLogger(__name__)


def test_configure_logger() -> None:
    """
    Test configuring the logger based on the provided settings.
    """
    mock_settings = MagicMock()
    mock_settings.LOG_LEVEL = LogLevel.WARNING
    mock_settings.TEST_ENV = False
    configure_logger(mock_settings)
    assert logging.getLogger().getEffectiveLevel() == logging.WARNING


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """
    Fixture that automatically clears the cache for get_settings before each test.
    """
    get_settings.cache_clear()


@patch("backend.src.core.settings.read_file")
@patch("backend.src.core.settings.Settings.model_validate")
@patch("backend.src.core.settings.configure_logger")
def test_get_settings_success(
    mock_configure_logger: MagicMock,
    mock_model_validate: MagicMock,
    mock_read_file: MagicMock,
) -> None:
    """
    Unit test for get_settings function when settings are successfully loaded and validated.
    """
    mock_json_data = {
        "UVICORN": {
            "HOST": "1.1.1.1",
            "PORT": 8080,
            "RELOAD": True,
            "TIME_OUT": 180,
        },
        "LOG_LEVEL": "INFO",
        "THANOS": {"CLUSTER_GROUPING_LEVEL": 3},
    }
    validated_settings = MagicMock(spec=Settings)  # type: ignore[misc]
    mock_read_file.return_value = mock_json_data
    mock_model_validate.return_value = validated_settings

    settings = get_settings()

    mock_read_file.assert_called_once()  # type: ignore[misc]
    mock_model_validate.assert_called_once_with(mock_json_data)  # type: ignore[misc]
    mock_configure_logger.assert_called_once_with(mock_model_validate.return_value)  # type: ignore[misc]
    assert settings == validated_settings


@patch("backend.src.core.settings.read_file")
@patch("backend.src.core.settings.Settings.model_validate")
@patch("backend.src.core.settings.configure_logger")
def test_get_settings_error(
    mock_configure_logger: MagicMock,
    mock_model_validate: MagicMock,
    mock_read_file: MagicMock,
) -> None:
    """
    Unit test for get_settings when a validation error occurs.

    Verifies that a CarmenException is raised if Settings.model_validate fails.
    """
    mock_json_data = {
        "INVALID": {
            "A": "1.1.1.1",
            "B": 8080,
            "C": True,
            "D": 180,
        }
    }
    mock_read_file.return_value = mock_json_data
    mock_model_validate.side_effect = ValueError("Invalid settings")
    with pytest.raises(ConfigValidationError):
        _ = get_settings()

    mock_read_file.assert_called_once()  # type: ignore[misc]
    mock_model_validate.assert_called_once_with(mock_json_data)  # type: ignore[misc]
    mock_configure_logger.assert_not_called()  # type: ignore[misc]
