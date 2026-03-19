# pylint: disable=redefined-outer-name
"""
Unit tests for IFCostService in impact framework.
"""
from unittest.mock import patch, MagicMock

import pytest

from backend.src.schemas.costResource import CostResource
from backend.src.services.carbon_service.impact_framework.service.if_cost_service import IFCostService
from backend.src.services.carbon_service.impact_framework.service.if_service import IFService


@pytest.fixture
def mock_cost_resource():
    """
    Fixture to create a mock cost resource object for testing.
    """
    return CostResource(
        id="cost1",
        name="Test Cost Resource",
        region="eastus",
        subscription="sub1",
        carbon_intensity=100.0,
        services_cost=50.0
    )


@patch.object(IFCostService, "__init__", lambda self, duration: None)
@patch.object(IFCostService, "run_if", autospec=True)
@patch.object(IFCostService, "parse_if_output", autospec=True)
def test_run_engine_success(mock_parse_if_output, mock_run_if, mock_cost_resource):
    """
    Test the run_engine method of IFCostService with mock cost resource data.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFCostService(mock_if_service)

    result = service.run_engine([mock_cost_resource])

    mock_run_if.assert_called_once_with(service, [mock_cost_resource], file_id=0)
    mock_parse_if_output.assert_called_once_with(service, [mock_cost_resource], file_id=0)
    assert result == [mock_cost_resource]


@patch.object(IFCostService, "__init__", lambda self, duration: None)
@patch.object(IFService, "get_models_info", autospec=True)
def test_get_models_info(mock_super_get_models_info):
    """
    Test the get_models_info method of IFCostService.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFCostService(mock_if_service)
    mock_data = {"hardware_models": {"cost-model": {}}}

    service.get_models_info(mock_data)

    mock_super_get_models_info.assert_called_once()
    assert "cost-model" in mock_data["hardware_models"]
    assert mock_data["hardware_models"]["cost-model"]


@patch("backend.src.services.carbon_service.impact_framework.service.if_cost_service.CostModel.fill_inputs")
@patch.object(IFCostService, "__init__", lambda self, duration: None)
def test_get_resource_inputs(mock_cost_model_fill_inputs, mock_cost_resource):
    """
    Test get_resource_inputs for IFCostService with CostModel.
    """
    mock_cost_model_fill_inputs.side_effect = lambda cost_resource, time_index: {
        "compute-energy": cost_resource.compute_energy,
        "storage-energy": cost_resource.storage_energy,
        "compute-embodied": cost_resource.compute_embodied,
        "storage-embodied": cost_resource.storage_embodied,
        "compute-cost": cost_resource.compute_cost,
        "storage-cost": cost_resource.storage_cost,
        "services-cost": cost_resource.services_cost,
        "carbon-intensity": cost_resource.carbon_intensity,
        "timestamp": cost_resource.time_points[time_index]
    }

    mock_cost_resource.compute_energy = 50.0
    mock_cost_resource.storage_energy = 60.0
    mock_cost_resource.compute_embodied = 10.0
    mock_cost_resource.storage_embodied = 20.0
    mock_cost_resource.compute_cost = 30.0
    mock_cost_resource.storage_cost = 40.0
    mock_cost_resource.time_points = [0]

    resource_inputs = IFCostService.get_resource_inputs(mock_cost_resource)

    expected_inputs = [
        {'carbon-intensity': 100.0,
         'compute-cost': 30.0,
         'compute-embodied': 10.0,
         'compute-energy': 50.0,
         'services-cost': 50.0,
         'storage-cost': 40.0,
         'storage-embodied': 20.0,
         'storage-energy': 60.0,
         'timestamp': 0}
    ]

    assert resource_inputs == expected_inputs
    mock_cost_model_fill_inputs.assert_called_once_with(mock_cost_resource, 0)
