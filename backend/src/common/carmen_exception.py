"""
Custom exception classes mapped to ErrorCode values.
"""

from __future__ import annotations

from backend.src.common.errors import ERRORS, ErrorCode


class CarmenException(Exception):
    """Base custom exception for known application errors."""

    def __init__(self, error_code: ErrorCode, details: str | None = None):
        self.error_code = error_code
        self.template = ERRORS[error_code]
        self.details = details
        self._formatted_string = self._build_message()
        super().__init__(self.template.message)

    def _build_message(self) -> str:
        base_message = self.template.to_string()
        if self.details:
            return f"{base_message}: {self.details}"
        return base_message

    @property
    def formatted_string(self) -> str:
        return self._formatted_string

    @property
    def category(self) -> str:
        return self.template.category.value


# Configuration Exceptions


class ConfigurationError(CarmenException):
    """Base class for configuration-related errors."""


class MissingParametersError(ConfigurationError):
    """Exception raised when required parameters are missing."""

    def __init__(self, error_code: ErrorCode, missing: list[str]):
        self.missing = missing
        super().__init__(error_code)

    def _build_message(self) -> str:
        base_message = self.template.to_string()
        return f"{base_message}{', '.join(self.missing)}"


class ConfigFileError(ConfigurationError):
    """Exception raised for configuration file errors."""

    def __init__(self, error_code: ErrorCode, file_path: str | None = None):
        self.file_path = file_path
        details = f"file: {file_path}" if file_path else None
        super().__init__(error_code, details)


class ConfigValidationError(ConfigurationError):
    """Exception raised when configuration validation fails."""

    def __init__(
        self, error_code: ErrorCode, validation_errors: list[str] | None = None
    ):
        self.validation_errors = validation_errors or []
        details = "; ".join(validation_errors) if validation_errors else None
        super().__init__(error_code, details)


# Authentication Exceptions


class AuthenticationError(CarmenException):
    """Base class for authentication-related errors."""


class TokenError(AuthenticationError):
    """Exception raised for token-related errors."""

    def __init__(self, error_code: ErrorCode, token_info: str | None = None):
        super().__init__(error_code, token_info)


# Data Fetch Exceptions


class DataFetchError(CarmenException):
    """Base class for data fetching errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        source: str | None = None,
        details: str | None = None,
    ):
        self.source = source
        message_details = f"source: {source}" if source else None
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)


class ThanosError(DataFetchError):
    """Exception raised for Thanos-specific errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        query: str | None = None,
        details: str | None = None,
    ):
        self.query = query
        source_details = "Thanos"
        if query:
            source_details = (
                f"{source_details}, query: {query[:100]}..."  # Truncate long queries
            )
        super().__init__(error_code, source_details, details)


# Validation Exceptions


class ValidationError(CarmenException):
    """Base class for validation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        field_name: str | None = None,
        invalid_value: str | None = None,
    ):
        self.field_name = field_name
        self.invalid_value = invalid_value
        details = None
        if field_name:
            details = f"field: {field_name}"
            if invalid_value:
                details = f"{details}, value: {invalid_value}"
        super().__init__(error_code, details)


class DateValidationError(ValidationError):
    """Exception raised for date-related validation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        date_field: str,
        provided_value: str | None = None,
    ):
        super().__init__(error_code, date_field, provided_value)


class QueryParameterError(ValidationError):
    """Exception raised for query parameter validation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        invalid_params: list[str] | None = None,
        details: str | None = None,
    ):
        self.invalid_params = invalid_params or []
        param_details = ", ".join(invalid_params) if invalid_params else details
        super().__init__(error_code, param_details)


# File System Exceptions


class FileSystemError(CarmenException):
    """Base class for file system errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        path: str | None = None,
        details: str | None = None,
    ):
        self.path = path
        message_details = f"path: {path}" if path else None
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)


class FileNotFoundError(FileSystemError):  # pylint: disable=redefined-builtin
    """Exception raised when a file is not found."""

    def __init__(self, path: str):
        super().__init__(ErrorCode.FILE_NOT_FOUND, path)


class FileReadError(FileSystemError):
    """Exception raised when a file cannot be read."""

    def __init__(self, path: str, details: str | None = None):
        super().__init__(ErrorCode.FILE_READ_ERROR, path, details)


# Computation Exceptions


class ComputationError(CarmenException):
    """Base class for computation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        operation: str | None = None,
        details: str | None = None,
    ):
        self.operation = operation
        message_details = f"operation: {operation}" if operation else None
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)
