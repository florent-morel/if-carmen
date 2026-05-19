# pylint: disable=redefined-outer-name
"""
Unit tests for IFMiscServicesService in impact framework.
"""
from unittest.mock import patch, MagicMock

import pytest

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
        subscription="sub1",
        carbon_intensity=100.0,
        misc_services_cost=50.0,
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


@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_misc_services_service.MiscServicesModel.fill_inputs"
)
@patch.object(IFMiscServicesService, "__init__", lambda self, duration: None)
def test_get_resource_inputs(
    mock_misc_services_model_fill_inputs, mock_misc_services_resource
):
    """
    Test get_resource_inputs for IFMiscServicesService with MiscServicesModel.
    """
    mock_misc_services_model_fill_inputs.side_effect = (
        lambda misc_services_resource, time_index: {
            "compute-energy": misc_services_resource.compute_energy,
            "storage-energy": misc_services_resource.storage_energy,
            "compute-embodied": misc_services_resource.compute_embodied,
            "storage-embodied": misc_services_resource.storage_embodied,
            "compute-cost": misc_services_resource.compute_cost,
            "storage-cost": misc_services_resource.storage_cost,
            "misc-services-cost": misc_services_resource.misc_services_cost,
            "carbon-intensity": misc_services_resource.carbon_intensity,
            "timestamp": misc_services_resource.time_points[time_index],
        }
    )

    mock_misc_services_resource.compute_energy = 50.0
    mock_misc_services_resource.storage_energy = 60.0
    mock_misc_services_resource.compute_embodied = 10.0
    mock_misc_services_resource.storage_embodied = 20.0
    mock_misc_services_resource.compute_cost = 30.0
    mock_misc_services_resource.storage_cost = 40.0
    mock_misc_services_resource.time_points = [0]

    resource_inputs = IFMiscServicesService.get_resource_inputs(
        mock_misc_services_resource
    )

    expected_inputs = [
        {
            "carbon-intensity": 100.0,
            "compute-cost": 30.0,
            "compute-embodied": 10.0,
            "compute-energy": 50.0,
            "misc-services-cost": 50.0,
            "storage-cost": 40.0,
            "storage-embodied": 20.0,
            "storage-energy": 60.0,
            "timestamp": 0,
        }
    ]

    assert resource_inputs == expected_inputs
    mock_misc_services_model_fill_inputs.assert_called_once_with(
        mock_misc_services_resource, 0
    )
