"""
Exception handler for FastAPI application.

This module provides centralized exception handling for the Carbon Engine API,
mapping custom exceptions to appropriate HTTP responses with consistent error formatting.
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.src.common.known_exception import (
    KnownException,
)
from backend.src.common.errors import ErrorCode, ErrorCategory

logger = logging.getLogger(__name__)


def get_status_code_for_error(error_code: ErrorCode) -> int:
    """
    Map error codes to appropriate HTTP status codes.

    Args:
        error_code: The error code to map.

    Returns:
        The appropriate HTTP status code.
    """
    # Configuration errors (usually 500 or 503)
    if error_code.value.startswith("1"):
        return status.HTTP_503_SERVICE_UNAVAILABLE

    # Authentication errors (401 or 403)
    if error_code.value.startswith("2"):
        if error_code in [ErrorCode.AUTH_UNAUTHORIZED]:
            return status.HTTP_403_FORBIDDEN
        return status.HTTP_401_UNAUTHORIZED

    # Data fetch errors (usually 502 or 503)
    if error_code.value.startswith("3"):
        if error_code in [
            ErrorCode.DATA_FETCH_TIMEOUT,
            ErrorCode.THANOS_TIMEOUT,
        ]:
            return status.HTTP_504_GATEWAY_TIMEOUT
        if error_code in [
            ErrorCode.DATA_FETCH_NO_RESULTS,
        ]:
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_502_BAD_GATEWAY

    # Validation errors (400 or 422)
    if error_code.value.startswith("4"):
        return status.HTTP_422_UNPROCESSABLE_ENTITY

    # File system errors (usually 404 or 500)
    if error_code.value.startswith("5"):
        if error_code in [
            ErrorCode.FILE_NOT_FOUND,
            ErrorCode.DIRECTORY_NOT_FOUND,
            ErrorCode.AZURE_STORAGE_BLOB_NOT_FOUND,
            ErrorCode.AZURE_STORAGE_CONTAINER_NOT_FOUND,
        ]:
            return status.HTTP_404_NOT_FOUND
        if error_code in [
            ErrorCode.FILE_PERMISSION_DENIED,
        ]:
            return status.HTTP_403_FORBIDDEN
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    # Computation errors (usually 500)
    if error_code.value.startswith("6"):
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    # Impact Framework errors (usually 500 or 502)
    if error_code.value.startswith("7"):
        return status.HTTP_502_BAD_GATEWAY

    # Database errors (usually 500 or 503)
    if error_code.value.startswith("8"):
        return status.HTTP_503_SERVICE_UNAVAILABLE

    # External API errors (usually 502 or 503)
    if error_code.value.startswith("9"):
        if error_code == ErrorCode.EXTERNAL_API_RATE_LIMIT:
            return status.HTTP_429_TOO_MANY_REQUESTS
        if error_code == ErrorCode.EXTERNAL_API_TIMEOUT:
            return status.HTTP_504_GATEWAY_TIMEOUT
        return status.HTTP_502_BAD_GATEWAY

    # Report generation errors (usually 500)
    if error_code.value.startswith("10"):
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    # Default to internal server error
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def create_error_response(
    error_code: str,
    category: str,
    message: str,
    details: dict[str, Any] = None,
) -> dict[str, Any]:
    """
    Create a standardized error response structure.

    Args:
        error_code: The error code.
        category: The error category.
        message: The error message.
        details: Optional additional details about the error.

    Returns:
        A dictionary containing the error response.
    """
    response = {
        "error": {
            "code": error_code,
            "category": category,
            "message": message,
        }
    }

    if details:
        response["error"]["details"] = details

    return response


async def known_exception_handler(
    request: Request, exc: KnownException
) -> JSONResponse:
    """
    Handle KnownException and its subclasses.

    Args:
        request: The incoming request.
        exc: The exception that was raised.

    Returns:
        A JSON response with appropriate status code and error details.
    """
    status_code = get_status_code_for_error(exc.error_code)

    # Log the error with appropriate level based on status code
    if status_code >= 500:
        logger.error(
            "Known exception occurred: [%s] %s",
            exc.error_code.value,
            exc.formatted_string,
            exc_info=True,
        )
    else:
        logger.warning(
            "Known exception occurred: [%s] %s",
            exc.error_code.value,
            exc.formatted_string,
        )

    # Build details dictionary
    details: dict[str, Any] = {}

    # Add exception-specific details
    if hasattr(exc, "missing") and exc.missing:
        details["missing_parameters"] = exc.missing
    if hasattr(exc, "file_path") and exc.file_path:
        details["file_path"] = exc.file_path
    if hasattr(exc, "path") and exc.path:
        details["path"] = exc.path
    if hasattr(exc, "query") and exc.query:
        details["query"] = exc.query[:200]  # Truncate long queries
    if hasattr(exc, "field_name") and exc.field_name:
        details["field"] = exc.field_name
    if hasattr(exc, "invalid_value") and exc.invalid_value:
        details["invalid_value"] = str(exc.invalid_value)
    if hasattr(exc, "source") and exc.source:
        details["source"] = exc.source
    if hasattr(exc, "operation") and exc.operation:
        details["operation"] = exc.operation
    if hasattr(exc, "api_name") and exc.api_name:
        details["api"] = exc.api_name
    if hasattr(exc, "endpoint") and exc.endpoint:
        details["endpoint"] = exc.endpoint
    if hasattr(exc, "container") and exc.container:
        details["container"] = exc.container
    if hasattr(exc, "blob_name") and exc.blob_name:
        details["blob"] = exc.blob_name

    response = create_error_response(
        error_code=exc.error_code.value,
        category=exc.category,
        message=exc.formatted_string,
        details=details if details else None,
    )

    return JSONResponse(status_code=status_code, content=response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI/Pydantic validation errors.

    Args:
        request: The incoming request.
        exc: The validation exception.

    Returns:
        A JSON response with validation error details.
    """
    logger.warning("Validation error occurred: %s", exc.errors())

    # Extract field names and error messages
    validation_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        validation_errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    response = create_error_response(
        error_code=ErrorCode.VALIDATION_INVALID_PARAMETER.value,
        category=ErrorCategory.VALIDATION.value,
        message="Request validation failed",
        details={"validation_errors": validation_errors},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException from FastAPI.

    Args:
        request: The incoming request.
        exc: The HTTP exception.

    Returns:
        A JSON response with the exception details.
    """
    logger.warning("HTTP exception occurred: %s - %s", exc.status_code, exc.detail)

    # Map status codes to categories
    if exc.status_code >= 500:
        category = "server error"
    elif exc.status_code >= 400:
        category = "client error"
    else:
        category = "http error"

    response = create_error_response(
        error_code=str(exc.status_code),
        category=category,
        message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
    )

    return JSONResponse(status_code=exc.status_code, content=response)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: The incoming request.
        exc: The exception that was raised.

    Returns:
        A JSON response with error details.
    """
    logger.exception("Unexpected exception occurred: %s", str(exc))

    # Don't expose internal error details in production
    response = create_error_response(
        error_code="INTERNAL_ERROR",
        category="server error",
        message="An unexpected error occurred. Please contact support if the issue persists.",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    # Register custom exception handlers
    app.add_exception_handler(KnownException, known_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")


def raise_http_error(
    status_code: int,
    error_code: str,
    category: str,
    message: str,
    details: dict[str, Any] = None,
) -> None:
    """
    Raise an HTTPException with standardized error format.

    Args:
        status_code: HTTP status code.
        error_code: Application error code.
        category: Error category.
        message: Error message.
        details: Optional additional details.
    """
    error_response = create_error_response(error_code, category, message, details)
    raise HTTPException(status_code=status_code, detail=error_response)
