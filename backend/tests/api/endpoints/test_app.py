"""
This module contains unit tests for API endpoints related to retrieving resources and running the carbon engine.
"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.src.common.carmen_exception import DataFetchError
from backend.src.core.settings import settings
from backend.src.schemas.application import Application
from backend.src.schemas.pod import Pod
from backend.src.services.carbon_service.carbon_service import CarbonService


@patch("backend.src.services.argos_service.ArgosService.get_available_resources")
def test_get_available_resources(mock_get_available_resources, api_client: TestClient):
    """
    Unit test for the get_available_resources endpoint.

    Tests that the API returns the expected resource dictionary and handles successful requests.
    """
    mock_response = {
        "paas": ["PaaS1", "PaaS2"],
        "namespaces": ["namespace1", "namespace2"],
    }
    mock_get_available_resources.return_value = mock_response

    response = api_client.get(f"{settings.FASTAPI.API_STR}/apps/?app=App1&app=App2")

    assert response.status_code == 200
    assert response.json() == mock_response
    mock_get_available_resources.assert_called_once_with(["App1", "App2"], None)


@patch("backend.src.services.argos_service.ArgosService.get_available_resources")
def test_get_available_resources_no_params(
    mock_get_available_resources, api_client: TestClient
):
    """
    Unit test for the get_available_resources endpoint when no query parameters are passed.
    """
    # Arrange
    mock_response = {"paas": [], "app": []}
    mock_get_available_resources.return_value = mock_response

    # Act
    response = api_client.get(f"{settings.FASTAPI.API_STR}/apps/")

    # Assert
    assert response.status_code == 200
    assert response.json() == mock_response
    mock_get_available_resources.assert_called_once_with(None, None)


@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_app_service.IFAppService.run_engine"
)
@patch("backend.src.services.argos_service.ArgosService.retrieve_telemetry_data")
@patch("backend.src.utils.ioc_util.resolve")
def test_run_engine_for_selected_resources_success_at_app_level(
    mock_resolve, mock_retrieve_telemetry_data, mock_run_engine, api_client: TestClient
):
    """
    Unit test for the run_engine_for_selected_resources endpoint at application level.

    Verifies that:
    - Pod data is retrieved correctly.
    - The run_engine method is called with the correct pods.
    - The API responds with status 200.
    """

    mock_pods = [
        Pod(id="0", app="app1", paas="PaaS1", namespace="namespace1"),
        Pod(id="1", app="app1", paas="PaaS1", namespace="namespace2"),
    ]
    mock_app = [Application(id="app1", name="app1", pods=mock_pods)]

    mock_carbon_service = MagicMock()
    mock_carbon_service.run_engine = mock_run_engine
    mock_retrieve_telemetry_data.return_value = mock_app
    mock_resolve.return_value = mock_carbon_service

    response = api_client.get(
        f"{settings.FASTAPI.API_STR}/apps/run-engine/?app=App1&paas=PaaS1"
    )

    assert response.status_code == 200
    mock_retrieve_telemetry_data.assert_called_once()
    mock_resolve.assert_called_once_with(CarbonService, "IFApp", 1800)
    mock_run_engine.assert_awaited_once_with(mock_app, False)


@patch("backend.src.services.argos_service.ArgosService.retrieve_telemetry_data")
def test_run_engine_for_selected_resources_data_fetch_error(
    mock_retrieve_telemetry_data, api_client: TestClient
):
    """
    Unit test for the run_engine_for_selected_resources endpoint when data fetch fails.
    """
    from backend.src.common.errors import ErrorCode

    mock_retrieve_telemetry_data.side_effect = DataFetchError(
        ErrorCode.DATA_FETCH_FAILED, source="Thanos", details="Connection timeout"
    )

    response = api_client.get(f"{settings.FASTAPI.API_STR}/apps/run-engine/?paas=PaaS1")

    # Should return error response with proper status code
    assert response.status_code == 502  # Bad Gateway for data fetch errors
    error_response = response.json()
    assert "error" in error_response
    assert error_response["error"]["code"] == "3001"
    assert error_response["error"]["category"] == "data fetch"


def test_run_engine_for_selected_resources_invalid_query_params(api_client: TestClient):
    """
    Unit test for the run_engine_for_selected_resources endpoint with invalid query parameters.
    """
    # Unprocessable entity error due to invalid 'code' parameter
    response = api_client.get(
        f"{settings.FASTAPI.API_STR}/apps/run-engine/?paas=erd6&code=422"
    )
    assert response.status_code == 422
    error_response = response.json()
    assert "error" in error_response


@patch(
    "backend.src.services.carbon_service.impact_framework.service.if_app_service.IFAppService.run_engine"
)
@patch("backend.src.services.argos_service.ArgosService.retrieve_telemetry_data")
@patch("backend.src.utils.ioc_util.resolve")
def test_run_engine_for_selected_resources_success_with_emission_breakdown(
    mock_resolve, mock_retrieve_telemetry_data, mock_run_engine, api_client: TestClient
):
    """
    Unit test for the run_engine_for_selected_resources endpoint at pod level.
    """
    mock_pods = [
        Pod(id="0", app="app1", paas="PaaS1", namespace="namespace1"),
        Pod(id="1", app="app1", paas="PaaS1", namespace="namespace2"),
    ]

    mock_carbon_service = MagicMock()
    mock_carbon_service.run_engine = mock_run_engine
    mock_retrieve_telemetry_data.return_value = mock_pods
    mock_resolve.return_value = mock_carbon_service

    """response = api_client.get(f"{settings.FASTAPI.API_STR}"
                              f"/apps/run-engine/?app=App1&paas=PaaS1&emission_breakdown=True")

    assert response.status_code == 200
    mock_retrieve_telemetry_data.assert_called_once()
    mock_resolve.assert_called_once_with(CarbonService, "IFApp", 1800)
    mock_run_engine.assert_awaited_once_with(mock_pods, True)"""
    # TODO: Fix. There should be another schema class called namespace.py that has List of pods just like Cluster schema
    #   Having a Dict of Dict of Dict of List of Pod is not a good design if we want to have scalable code:
    #   Dict[str, Dict[str, Dict[str, List[Pod]]]]
    #   If we choose to describe these objects in complex datastructures starting from app level,
    #   it would've got really complex. So please keep that design..
