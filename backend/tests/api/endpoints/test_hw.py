"""
Test cases for hardware endpoints in the API.
"""

from unittest.mock import patch, MagicMock
import pytest

from backend.src.core.settings import settings
from backend.src.core.yaml_config_loader import config
from backend.src.services.carbon_service.impact_framework.models.cloud_metadata import CloudMetadata


@pytest.mark.asyncio
@patch("backend.src.api.endpoints.hw.ioc_util.resolve")
async def test_run_engine_success(mock_resolve, api_client):
    """
    Test case for successful run engine hardware endpoint.
    """
    # Arrange
    mock_service = MagicMock()
    mock_resolve.return_value = mock_service

    params = {
        "virtual_machine-type": "Standard_E16as_v4",
        "cpu-load": [10, 20, 30],
        "storage-size": [100, 200, 300],
        "duration": 60,
    }

    # Act
    response = api_client.get(
        f"{settings.FASTAPI.API_STR}/hardware/run-engine-hardware/", params=params
    )

    # Assert
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    virtual_machine = mock_service.run_engine.call_args.args[0][0]
    assert virtual_machine.provider == config.carmen_api.provider
    assert "cpu/thermal-design-power" in CloudMetadata.fill_inputs(virtual_machine, 0)


@pytest.mark.asyncio
@patch("backend.src.api.endpoints.hw.ioc_util.resolve")
async def test_run_engine_requires_provider(mock_resolve, api_client, monkeypatch):
    monkeypatch.setattr(config.carmen_api, "provider", None)

    response = api_client.get(
        f"{settings.FASTAPI.API_STR}/hardware/run-engine-hardware/",
        params={
            "virtual_machine-type": "Standard_E16as_v4",
            "cpu-load": 10,
            "storage-size": 100,
            "duration": 60,
        },
    )

    assert response.status_code == 400
    assert "carmen_api.provider must be configured" in response.text
    mock_resolve.assert_not_called()


@pytest.mark.asyncio
@patch("backend.src.api.endpoints.hw.ioc_util.resolve")
async def test_run_engine_mismatched_array_lengths(mock_resolve, api_client):
    """
    Test case for mismatched array lengths in CPU load and storage size.
    """
    params = {
        "virtual_machine-type": "Standard_E16as_v4",
        "cpu-load": [10, 20],
        "storage-size": [100],  # Mismatch
        "duration": 60,
    }

    response = api_client.get(
        f"{settings.FASTAPI.API_STR}/hardware/run-engine-hardware/", params=params
    )

    assert response.status_code == 400
    assert "CPU load and storage size arrays must have the same length" in response.text
