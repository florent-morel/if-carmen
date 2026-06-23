# pylint: disable=redefined-outer-name
"""
Unit tests for the IFAppService class in the carbon service impact framework.
"""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from backend.src.common.constants import DAILY_SECONDS
from backend.src.schemas.application import Application
from backend.src.schemas.pod import Pod
from backend.src.services.carbon_service.impact_framework.service.if_app_service import (
    IFAppService,
)
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)


@pytest.fixture
def app_service():
    """
    Mock IFAppService class.
    """
    with patch.object(IFAppService, "__init__", lambda self, *args, **kwargs: None):
        mock_service = IFAppService(duration=10)
        mock_service.data = {"applications": {}}
        return mock_service


@pytest.fixture
def mock_pod_fixture():
    """
    Mock Pod object.
    """
    return Pod(
        id="pod1",
        app="app1",
        paas="paas1",
        namespace="namespace1",
        time_points=[1, 2, 3],
        cpu_util=[0.5, 0.6, 0.7],
        requested_cpu=[0.5, 0.6, 0.7],
        memory_used=[500, 600, 700],
        requested_memory=[0.5, 0.6, 0.7],
        storage_capacity=[50, 100],
        network_io=[10, 20],
        carbon_intensity=0.1,
    )


@pytest.fixture
def mock_application(mock_pod_fixture):
    """
    Mock Application object.
    """
    app = Application(id="app1", name="app1", pods=[mock_pod_fixture])
    return app


@pytest.mark.asyncio
@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_app_service.IFAppService.run_if",
    new_callable=AsyncMock,
)
@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.parse_if_output"
)
async def test_run_engine(
    mock_parse_if_output, mock_run_if, app_service, mock_application
):
    """
    Test the run_engine method for IFAppService with mock Application data at application level.
    """
    mock_parse_if_output.return_value = [mock_application]
    mock_application.id = "0"

    result = await app_service.run_engine(compute_resources=[mock_application])

    assert isinstance(result, list)
    assert isinstance(result[0], Application)
    mock_run_if.assert_called_once_with([mock_application])
    mock_parse_if_output.assert_called_once_with([mock_application], False)


@pytest.mark.asyncio
@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_app_service.IFAppService.run_if",
    new_callable=AsyncMock,
)
@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.parse_if_output"
)
async def test_run_engine_at_pod_level(
    mock_parse_if_output, mock_run_if, app_service, mock_application
):
    """
    Test the run_engine method for IFAppService with mock Application data at application level.
    """
    mock_parse_if_output.return_value = {
        "paas": {"app": {"namespace": mock_application.pods}}
    }
    mock_application.id = "0"

    result = await app_service.run_engine(
        compute_resources=[mock_application], emission_breakdown_at_pod_level=True
    )

    assert isinstance(result, dict)
    mock_run_if.assert_called_once_with([mock_application])
    mock_parse_if_output.assert_called_once_with([mock_application], True)


def test_get_resource_data(app_service, mock_application, mock_pod_fixture):
    """
    Test the get_resource_data method for IFAppService with mock Application data.
    """
    apps = [mock_application]
    data = {}
    expected_result = {
        "app1": {
            "pod1": [
                {
                    "cpu/utilization": 50.0,
                    "grid/carbon-intensity": 0.1,
                    "memory/requested": 5e-10,
                    "pue": 1.0,
                    "resources-reserved": 0.5,
                    "resources-total": 66,
                    "timestamp": 1,
                    "duration": DAILY_SECONDS,
                    "duration/seconds": DAILY_SECONDS,
                },
                {
                    "cpu/utilization": 60.0,
                    "grid/carbon-intensity": 0.1,
                    "memory/requested": 6e-10,
                    "pue": 1.0,
                    "resources-reserved": 0.6,
                    "resources-total": 66,
                    "timestamp": 2,
                    "duration": DAILY_SECONDS,
                    "duration/seconds": DAILY_SECONDS,
                },
                {
                    "cpu/utilization": 70.0,
                    "grid/carbon-intensity": 0.1,
                    "memory/requested": 7e-10,
                    "pue": 1.0,
                    "resources-reserved": 0.7,
                    "resources-total": 66,
                    "timestamp": 3,
                    "duration": DAILY_SECONDS,
                    "duration/seconds": DAILY_SECONDS,
                },
            ]
        }
    }
    app_service.get_resource_data(data, apps)
    assert data["resources"] == expected_result


@patch.object(IFAppService, "__init__", lambda self, duration: None)
@patch.object(IFService, "get_models_info", autospec=True)
def test_get_models_info(mock_super_get_models_info):
    """
    Test the get_models_info method of IFVMService.
    """
    mock_if_service = MagicMock(spec=IFService)
    service = IFAppService(mock_if_service)
    data = {"hardware_models": {"p-cores": {}}}

    service.get_models_info(data)

    mock_super_get_models_info.assert_called_once()
    assert "p-cores" in data["hardware_models"]
    assert data["hardware_models"]["p-cores"]


@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.get_resource_inputs"
)
def test_get_resource_inputs(mock_get_resource_inputs, app_service):
    """
    Test the get_resource_inputs method for IFAppService with mock Pod data.
    """
    mock_pod = MagicMock(spec=Pod)
    mock_models = (MagicMock(), MagicMock())
    expected_result = [{"mock_key": "mock_value"}]
    mock_get_resource_inputs.return_value = expected_result

    result = IFAppService.get_resource_inputs(mock_pod, mock_models)

    assert result == expected_result
    mock_get_resource_inputs.assert_called_once_with(mock_pod, mock_models, DAILY_SECONDS)
