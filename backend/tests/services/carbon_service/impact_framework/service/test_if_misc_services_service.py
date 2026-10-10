# pylint: disable=redefined-outer-name
"""
Unit tests for IFMiscServicesService in impact framework.
"""
from unittest.mock import patch, MagicMock

import pytest

from backend.src.common.constants import DAILY_SECONDS
from backend.src.services.carbon_service.impact_framework.service.if_misc_services_service import (
    IFMiscServicesService,
)
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)
from backend.src.schemas.misc_services_resource import MiscServicesResource


@pytest.fixture
def mock_misc_services_resource():
    """
    Fixture to create a mock misc services resource object for testing.
    """
    return MiscServicesResource(
        id="misc_service1",
        name="Test Misc Services Resource",
        region="eastus",
        carbon_intensity=100.0,
        cost=50.0,
    )


@patch.object(IFMiscServicesService, "__init__", lambda self, duration: None)
@patch.object(IFMiscServicesService, "run_if", autospec=True)
@patch.object(IFMiscServicesService, "parse_if_output", autospec=True)
def test_run_engine_success(
    mock_parse_if_output, mock_run_if, mock_misc_services_resource
):
    """
    Test the run_engine method of IFMiscServicesService with mock misc services resource data.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFMiscServicesService(mock_if_service)

    result = service.run_engine([mock_misc_services_resource])

    mock_run_if.assert_called_once_with(
        service, [mock_misc_services_resource], file_id=0
    )
    mock_parse_if_output.assert_called_once_with(
        service, [mock_misc_services_resource], file_id=0
    )
    assert result == [mock_misc_services_resource]


@patch.object(IFMiscServicesService, "__init__", lambda self, duration: None)
@patch.object(IFService, "get_models_info", autospec=True)
def test_get_models_info(mock_super_get_models_info):
    """
    Test the get_models_info method of IFMiscServicesService.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFMiscServicesService(mock_if_service)
    mock_data = {"hardware_models": {"misc_services-model": {}}}

    service.get_models_info(mock_data)

    mock_super_get_models_info.assert_called_once()
    assert "misc_services-model" in mock_data["hardware_models"]
    assert mock_data["hardware_models"]["misc_services-model"]


def test_get_resource_inputs(mock_misc_services_resource):
    """
    Test get_resource_inputs for IFMiscServicesService with MiscServicesModel.
    """
    mock_misc_services_resource.energy_cost_ratio = 0.125
    mock_misc_services_resource.embodied_cost_ratio = 0.75
    mock_misc_services_resource.time_points = [0]
    mock_misc_services_resource.duration_seconds = [DAILY_SECONDS]

    resource_inputs = IFMiscServicesService.get_resource_inputs(
        mock_misc_services_resource
    )

    expected_inputs = [
        {
            "carbon-intensity": 100.0,
            "energy-cost-ratio": 0.125,
            "embodied-cost-ratio": 0.75,
            "cost": 50.0,
            "timestamp": 0,
            "duration": DAILY_SECONDS,
            "duration/seconds": DAILY_SECONDS,
        }
    ]

    assert resource_inputs == expected_inputs
