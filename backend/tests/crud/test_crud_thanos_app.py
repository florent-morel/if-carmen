# pylint: disable=redefined-outer-name
"""
This module contains tests for the CrudThanosApp class.

Tests cover:
- Query execution for time series and instant queries
- Token refresh mechanism
- Time range queries
- Error handling
"""

from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import pytest
import httpx

from backend.src.crud.crud_thanos_app import CrudThanosApp
from backend.src.common.carmen_exception import ThanosError, TokenError


@pytest.fixture
def mock_auth_strategy() -> MagicMock:
    """Create a mock authentication strategy with a dummy token."""
    strategy = MagicMock()
    strategy.get_headers.return_value = {"Authorization": "Bearer dummy-token"}
    return strategy


@pytest.fixture
def crud_app(mock_auth_strategy: MagicMock) -> CrudThanosApp:
    """Create a CrudThanosApp instance with mock authentication"""
    return CrudThanosApp("http://thano:ws.example.com", mock_auth_strategy)


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
@patch("backend.src.crud.crud_thanos_app.get_result_from_response")
async def test_exec_query_time_series_success(
    mock_get_result: MagicMock, mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Create a CrudThanosApp instance with mock authentication"""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": "mocked_result"}'

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client.return_value = mock_client_instance

    mock_get_result.return_value = {"data": "mocked_result"}

    result = await crud_app.exec_query("up", time_series=True)

    assert result == {"data": "mocked_result"}
    mock_client_instance.get.assert_called_once()
    mock_get_result.assert_called_once_with(mock_response)


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
@patch("backend.src.crud.crud_thanos_app.get_result_from_response")
async def test_exec_query_instant_success(
    mock_get_result: MagicMock, mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Test executing an instant query (no time range)"""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": "instant_result"}'

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client.return_value = mock_client_instance

    mock_get_result.return_value = {"data": "instant_result"}

    result = await crud_app.exec_query("up", time_series=False)

    assert result == {"data": "instant_result"}


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
async def test_exec_query_token_refresh_success(
    mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Test refresh token mechanism"""
    invalid_response = MagicMock()
    invalid_response.headers = {"Content-Type": "text/html"}
    valid_response = MagicMock()
    valid_response.headers = {"Content-Type": "application/json"}
    valid_response.content = b'{"data": "refreshed_result"}'

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(
        side_effect=[invalid_response, invalid_response, valid_response]
    )
    mock_client.return_value = mock_client_instance

    with patch(
        "backend.src.crud.crud_thanos_app.get_result_from_response"
    ) as mock_result:
        mock_result.return_value = {"data": "refreshed_result"}

        result = await crud_app.exec_query("up")

        assert result == {"data": "refreshed_result"}
        assert mock_client_instance.get.call_count == 3


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
@patch("backend.src.crud.crud_thanos_app.get_result_from_response")
async def test_exec_query_with_time_range(
    mock_get_result: MagicMock, mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Text query execution with time range"""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": "ok"}'

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client.return_value = mock_client_instance

    mock_get_result.return_value = {"data": "ok"}

    start = datetime(2024, 1, 1, 0, 0, 0)
    end = datetime(2024, 1, 1, 1, 0, 0)

    result = await crud_app.exec_query("up", start=start, end=end, sampling_rate="60s")

    assert result == {"data": "ok"}

    params = mock_client_instance.get.call_args[1]["params"]
    assert "start" in params
    assert "end" in params
    assert "step" in params
    assert params["step"] == "60s"


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
async def test_exec_query_timeout_error(
    mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Test that timeout errors are properly raised as ThanosError"""
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(
        side_effect=httpx.TimeoutException("Request timed out")
    )
    mock_client.return_value = mock_client_instance

    with pytest.raises(ThanosError) as exc_info:
        await crud_app.exec_query("up")

    assert exc_info.value.error_code.value == "3102"  # THANOS_TIMEOUT
    assert "timed out" in exc_info.value.formatted_string.lower()


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
async def test_exec_query_connection_error(
    mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Test that connection errors are properly raised as ThanosError"""
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(
        side_effect=httpx.ConnectError("Failed to connect")
    )
    mock_client.return_value = mock_client_instance

    with pytest.raises(ThanosError) as exc_info:
        await crud_app.exec_query("up")

    assert exc_info.value.error_code.value == "3104"  # THANOS_CONNECTION_ERROR
    assert "connection" in exc_info.value.formatted_string.lower()


@pytest.mark.asyncio
@patch("backend.src.crud.crud_thanos_app.httpx.AsyncClient")
async def test_exec_query_token_refresh_failure(
    mock_client: MagicMock, crud_app: CrudThanosApp
) -> None:
    """Test that token refresh failures are properly raised"""
    invalid_response = MagicMock()
    invalid_response.headers = {"Content-Type": "text/html"}

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(return_value=invalid_response)
    mock_client.return_value = mock_client_instance

    with pytest.raises(TokenError) as exc_info:
        await crud_app.exec_query("up")

    assert exc_info.value.error_code.value == "2005"  # AUTH_TOKEN_REFRESH_FAILED
    assert "refresh" in exc_info.value.formatted_string.lower()
