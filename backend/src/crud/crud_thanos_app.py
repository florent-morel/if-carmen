"""
This module provides a CRUD application class for interacting with Thanos, a time-series database for handling
prometheus queries.
It handles auth_strategies, token refreshing, and executing queries to Thanos endpoints.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any
import httpx

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    ThanosError,
    TokenError,
)
from backend.src.common.enums import SamplingRate
from backend.src.utils.helpers import get_result_from_response
from backend.src.crud.auth_strategies.auth_strategy import AuthStrategy

logger = logging.getLogger(__name__)


class CrudThanosApp:
    """
    CRUD Application Class for executing prometheus queries to Thanos.

    Attributes:
       app: A ConfidentialClientApplication instance for acquiring tokens.
       headers: Dictionary containing authorization headers.
    """

    def __init__(
        self,
        thanos_url: str,
        auth_strategy: AuthStrategy,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initializes the CrudApp instance with an authorized token

        Args:
            thanos_url: The Thanos endpoint URL
            auth_strategy: Authentication strategy to use
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.thanos_url = thanos_url
        self.auth_strategy = auth_strategy
        self.headers = self.auth_strategy.get_headers()
        self.verify_ssl = verify_ssl

        if not verify_ssl:
            logger.warning(
                "SSL verification is disabled for Thanos connections. "
                "This is insecure and should only be used in development environments."
            )

    # FIX: Pylint #R0913
    async def exec_query(
        self,
        query: str,
        start: datetime | None = None,
        end: datetime | None = None,
        sampling_rate: SamplingRate | None = None,
        time_series: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Execute a prometheus query to Thanos and return the response.

        Args:
            query (str): The query to execute (PromQL).
            start (str, optional): The start time for the query. Defaults to None.
            end (str, optional): The end time for the query. Defaults to None.
            sampling_rate (str, optional): The time sampling_rate for the query. Defaults to None.
            applications (List(str), optional): The applications for which the query is executed. Defaults to None.
            clusters (List(str), optional): The clusters for which the query is executed. Defaults to None.
            namespaces (List(str), optional): The namespaces for which the query is executed. Defaults to None.
            time_series (bool, optional): Flag to indicate whether the query is a time-series query. Defaults to True.

        Returns:
            dict: The response from Thanos API.

        Raises:
            ThanosError: If the query execution fails.
            TokenError: If authentication token refresh fails.
            DataFetchError: If connection to Thanos fails.
        """

        if time_series:
            endpoint = self.thanos_url + "/api/v1/query_range"
        else:
            endpoint = self.thanos_url + "/api/v1/query"
        params = {"query": query}
        debug_msg = (
            "Executing the query to Thanos with the following parameters: query: %s"
        )
        if start is not None and end is not None:
            params["start"] = start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            params["end"] = end.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            params["step"] = sampling_rate
            logger.debug(
                "%s, start: %s, end: %s, sampling_rate: %s",
                debug_msg,
                start,
                end,
                sampling_rate,
            )
        else:
            logger.debug(debug_msg, query)

        start_time = time.time()

        async def make_request() -> httpx.Response:
            try:
                async with httpx.AsyncClient(
                    verify=self.verify_ssl, timeout=200.0
                ) as client:
                    return await client.get(
                        endpoint,
                        headers=self.headers,
                        params=params,
                    )
            except httpx.TimeoutException as e:
                logger.error("Thanos query timed out: %s", str(e))
                raise ThanosError(
                    ErrorCode.THANOS_TIMEOUT,
                    query=query,
                    details="Request timed out after 200 seconds",
                ) from e
            except httpx.ConnectError as e:
                logger.error("Failed to connect to Thanos: %s", str(e))
                raise ThanosError(
                    ErrorCode.THANOS_CONNECTION_ERROR,
                    query=query,
                    details=f"Could not establish connection to {endpoint}",
                ) from e
            except httpx.HTTPError as e:
                logger.error("Request to Thanos failed: %s", str(e))
                raise ThanosError(
                    ErrorCode.THANOS_QUERY_FAILED,
                    query=query,
                    details=str(e),
                ) from e

        response = await make_request()

        retry_attempts = 3

        for attempt in range(retry_attempts):
            if "text/html" in response.headers.get("Content-Type", ""):
                logger.warning(
                    "Thanos query execution timeout (%.0f seconds) - refreshing authentication token (attempt %d/%d).",
                    time.time() - start_time,
                    attempt + 1,
                    retry_attempts,
                )
                try:
                    self.headers = self.auth_strategy.get_headers()
                    response = await make_request()
                except Exception as e:
                    logger.error("Failed to refresh token: %s", str(e))
                    if attempt == retry_attempts - 1:
                        raise TokenError(
                            ErrorCode.AUTH_TOKEN_REFRESH_FAILED,
                            f"Failed after {retry_attempts} attempts",
                        ) from e
            else:
                logger.debug("Valid JSON response received from Thanos")
                break
        else:
            logger.error(
                "Authentication failed after %d token refresh attempts", retry_attempts
            )
            raise TokenError(
                ErrorCode.AUTH_TOKEN_REFRESH_FAILED,
                f"Token is not valid after {retry_attempts} refresh attempts - check credentials",
            )

        logger.info(
            "Thanos query executed successfully in %.1f seconds.",
            time.time() - start_time,
        )

        try:
            return get_result_from_response(response)
        except Exception as e:
            logger.error("Failed to parse Thanos response: %s", str(e))
            raise ThanosError(
                ErrorCode.THANOS_INVALID_RESPONSE,
                query=query,
                details=f"Response parsing failed: {str(e)}",
            ) from e
