"""
FastAPI exception handlers for the Carbon Engine API.
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.src.common.carmen_exception import CarmenException
from backend.src.common.errors import ERRORS, ErrorCategory, ErrorCode

logger = logging.getLogger(__name__)

_ERROR_CODE_STATUS: dict[ErrorCode, int] = {
    ErrorCode.THANOS_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
    ErrorCode.DATA_FETCH_NO_RESULTS: status.HTTP_404_NOT_FOUND,
    ErrorCode.FILE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.FILE_PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
}

_CATEGORY_STATUS: dict[ErrorCategory, int] = {
    ErrorCategory.CONFIGURATION: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCategory.AUTHENTICATION: status.HTTP_401_UNAUTHORIZED,
    ErrorCategory.DATA_FETCH: status.HTTP_502_BAD_GATEWAY,
    ErrorCategory.VALIDATION: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCategory.FILE_SYSTEM: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCategory.COMPUTATION: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCategory.IMPACT_FRAMEWORK: status.HTTP_502_BAD_GATEWAY,
}


def get_status_code_for_error(error_code: ErrorCode) -> int:
    """Map an ErrorCode to its HTTP status code."""
    if error_code in _ERROR_CODE_STATUS:
        return _ERROR_CODE_STATUS[error_code]
    template = ERRORS.get(error_code)
    if template is None:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    return _CATEGORY_STATUS.get(
        template.category, status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def create_error_response(
    error_code: str,
    category: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the JSON error envelope returned by API exception handlers."""
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


async def carmen_exception_handler(
    request: Request, exc: CarmenException
) -> JSONResponse:
    """Convert CarmenException instances into structured JSON responses."""
    status_code = get_status_code_for_error(exc.error_code)

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

    details: dict[str, Any] = {}
    if hasattr(exc, "missing") and exc.missing:
        details["missing_parameters"] = exc.missing
    if hasattr(exc, "file_path") and exc.file_path:
        details["file_path"] = exc.file_path
    if hasattr(exc, "path") and exc.path:
        details["path"] = exc.path
    if hasattr(exc, "query") and exc.query:
        details["query"] = exc.query[:200]
    if hasattr(exc, "field_name") and exc.field_name:
        details["field"] = exc.field_name
    if hasattr(exc, "invalid_value") and exc.invalid_value:
        details["invalid_value"] = str(exc.invalid_value)
    if hasattr(exc, "source") and exc.source:
        details["source"] = exc.source
    if hasattr(exc, "operation") and exc.operation:
        details["operation"] = exc.operation

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
    """Handle FastAPI/Pydantic request validation errors."""
    logger.warning("Validation error occurred: %s", exc.errors())

    validation_errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

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
    """Handle FastAPI HTTPException errors."""
    logger.warning("HTTP exception occurred: %s - %s", exc.status_code, exc.detail)

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
    """Handle unhandled exceptions without leaking internal details."""
    logger.exception("Unexpected exception occurred: %s", str(exc))

    response = create_error_response(
        error_code="INTERNAL_ERROR",
        category="server error",
        message="An internal server error occurred.",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI application."""
    app.add_exception_handler(CarmenException, carmen_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
