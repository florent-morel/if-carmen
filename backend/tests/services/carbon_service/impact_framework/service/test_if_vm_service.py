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
    vm.provider = None
    return vm


@patch.object(IFVMService, "__init__", lambda self, duration: None)
@patch.object(IFVMService, "run_if", autospec=True)
@patch.object(IFVMService, "parse_if_output", autospec=True)
def test_run_engine_success(mock_parse_if_output, mock_run_if, mock_vm_1):
    """
    Test the run_engine method of IFVMService with mock VM data.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFVMService(mock_if_service)

    result = service.run_engine([mock_vm_1])

    mock_run_if.assert_called_once_with(service, [mock_vm_1], file_id=0)
    mock_parse_if_output.assert_called_once_with(service, [mock_vm_1], file_id=0)
    assert result == [mock_vm_1]


@patch.object(IFVMService, "__init__", lambda self, duration: None)
@patch.object(IFService, "get_models_info", autospec=True)
def test_get_models_info(mock_super_get_models_info):
    """
    Test the get_models_info method of IFVMService.
    p-cpu and p-vm-storage are filled with their Python model configurations.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFVMService(mock_if_service)
    mock_data = {"hardware_models": {"p-cpu": {}, "p-vm-storage": {}}}

    service.get_models_info(mock_data)

    mock_super_get_models_info.assert_called_once()
    assert mock_data["hardware_models"]["p-cpu"] != {}
    assert "cloud-metadata" not in mock_data["hardware_models"]


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


@patch.object(IFVMService, "__init__", lambda self, duration: None)
@patch.object(IFVMService, "run_if", autospec=True)
@patch.object(IFVMService, "parse_if_output", autospec=True)
def test_run_engine_groups_vms_by_provider(mock_parse_if_output, mock_run_if):
    """
    Test that run_engine groups VMs by provider so each IF run only contains
    a single provider's VMs, enabling correct CSV/config selection.
    """
    service = IFVMService(None)

    vm_azure_1 = MagicMock(spec=VirtualMachine)
    vm_azure_1.provider = "azure"
    vm_azure_1.time_points = [1, 2]

    vm_azure_2 = MagicMock(spec=VirtualMachine)
    vm_azure_2.provider = "azure"
    vm_azure_2.time_points = [1, 2]

    vm_aws = MagicMock(spec=VirtualMachine)
    vm_aws.provider = "aws"
    vm_aws.time_points = [1, 2]

    all_vms = [vm_azure_1, vm_aws, vm_azure_2]
    result = service.run_engine(all_vms)

    # Should be called twice — once per provider
    assert mock_run_if.call_count == 2
    assert mock_parse_if_output.call_count == 2

    # Each call receives only one provider's VMs
    chunks_passed = [call_args[0][1] for call_args in mock_run_if.call_args_list]
    provider_sets = [{vm.provider for vm in chunk} for chunk in chunks_passed]
    assert {"azure"} in provider_sets
    assert {"aws"} in provider_sets

    # The azure chunk has both azure VMs
    azure_chunk = next(
        c for c in chunks_passed if {vm.provider for vm in c} == {"azure"}
    )
    assert len(azure_chunk) == 2

    # Original list is returned unchanged
    assert result == all_vms
