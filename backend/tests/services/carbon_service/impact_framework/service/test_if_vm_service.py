# pylint: disable=redefined-outer-name
"""
Unit tests for IF_VM_service in impact framework.
"""
from unittest.mock import patch, MagicMock
import pytest
# from robot.utils.asserts import assert_true

from backend.src.services.carbon_service.impact_framework.service.if_vm_service import (
    IFVMService,
)
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)


@pytest.fixture
def mock_vm_1():
    """
    Fixture to create a mock virtual machine object for test_vm_1 with actual values for time_points and cpu_util.
    """
    vm = MagicMock(spec=VirtualMachine)
    vm.time_points = [1, 2, 3]
    vm.cpu_util = [0.5, 0.7, 0.9]
    vm.carbon_intensity = 100
    vm.vm_size = "Standard_D2_v2"
    return vm


@patch.object(IFVMService, "__init__", lambda self, duration: None)
@patch.object(IFVMService, "run_if", autospec=True)
@patch.object(IFVMService, "parse_if_output", autospec=True)
def test_run_engine_success(mock_parse_if_output, mock_run_if, mock_vm_1):
    """
    Test the run_engine method of IFVMService with mock VM data.
    """
    # Creating a new instance of IFVMService
    mock_if_service = MagicMock(spec=IFService)
    service = IFVMService(mock_if_service)

    result = service.run_engine([mock_vm_1])

    mock_run_if.assert_called_once_with(service, [mock_vm_1], 0)
    mock_parse_if_output.assert_called_once_with(service, [mock_vm_1], file_id=0)
    assert result == [mock_vm_1]


@patch.object(IFVMService, "__init__", lambda self, duration: None)
@patch.object(IFService, "get_models_info", autospec=True)
def test_get_models_info(mock_super_get_models_info):
    """
    Test the get_models_info method of IFVMService.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFVMService(mock_if_service)
    mock_data = {"hardware_models": {"cloud-metadata": {}}}

    service.get_models_info(mock_data)

    mock_super_get_models_info.assert_called_once()
    assert "cloud-metadata" in mock_data["hardware_models"]
    assert mock_data["hardware_models"]["cloud-metadata"]


@patch.object(IFVMService, "__init__", lambda self, duration: None)
@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.get_resource_inputs"
)
def test_get_resource_inputs(mock_get_resource_inputs, mock_vm_1):
    """
    Test the get_resource_inputs static method of IFVMService.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFVMService(mock_if_service)

    mock_get_resource_inputs.return_value = ["mock_value"]
    mock_models = (MagicMock(),)

    result = service.get_resource_inputs(mock_vm_1, mock_models)

    mock_get_resource_inputs.assert_called_once_with(mock_vm_1, mock_models)
    assert result == ["mock_value"]
