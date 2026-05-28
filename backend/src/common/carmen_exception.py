"""
Exception management classes for the Carbon Engine.

This module provides a comprehensive set of exception classes that map to
specific error codes and categories, enabling consistent error handling
throughout the application.
"""

from __future__ import annotations

from backend.src.common.errors import ERRORS, ErrorCode


class CarmenException(Exception):
    """
    Base custom exception class for handling known exceptions.

    All custom exceptions in the application should inherit from this class.
    """

    def __init__(self, error_code: ErrorCode, details: str | None = None):
        """
        Initialize a CarmenException.

        Args:
            error_code: The error code from the ErrorCode enum.
            details: Optional additional details about the error.
        """
        self.error_code = error_code
        self.template = ERRORS[error_code]
        self.details = details
        self._formatted_string = self._build_message()
        super().__init__(self.template.message)

    def _build_message(self) -> str:
        """Build the formatted error message."""
        base_message = self.template.to_string()
        if self.details:
            return f"{base_message}: {self.details}"
        return base_message

    @property
    def formatted_string(self) -> str:
        """Get the formatted error string."""
        return self._formatted_string

    @property
    def category(self) -> str:
        """Get the error category."""
        return self.template.category.value


# Configuration Exceptions


class ConfigurationError(CarmenException):
    """Base class for configuration-related errors."""


class MissingParametersError(ConfigurationError):
    """Exception raised when required parameters are missing."""

    def __init__(self, error_code: ErrorCode, missing: list[str]):
        """
        Initialize a MissingParametersError.

        Args:
            error_code: The error code (usually CONFIG_MISSING_PARAMETERS).
            missing: List of missing parameter names.
        """
        self.missing = missing
        super().__init__(error_code)

    def _build_message(self) -> str:
        """Build the formatted error message with missing parameters."""
        base_message = self.template.to_string()
        return f"{base_message}{', '.join(self.missing)}"


class ConfigFileError(ConfigurationError):
    """Exception raised for configuration file errors."""

    def __init__(self, error_code: ErrorCode, file_path: Optional[str] = None):
        """
        Initialize a ConfigFileError.

        Args:
            error_code: The error code.
            file_path: Optional path to the configuration file.
        """
        self.file_path = file_path
        details = f"file: {file_path}" if file_path else None
        super().__init__(error_code, details)


class ConfigValidationError(ConfigurationError):
    """Exception raised when configuration validation fails."""

    def __init__(
        self, error_code: ErrorCode, validation_errors: Optional[list[str]] = None
    ):
        """
        Initialize a ConfigValidationError.

        Args:
            error_code: The error code.
            validation_errors: Optional list of validation error messages.
        """
        self.validation_errors = validation_errors or []
        details = "; ".join(validation_errors) if validation_errors else None
        super().__init__(error_code, details)


# Authentication Exceptions


class AuthenticationError(CarmenException):
    """Base class for authentication-related errors."""


class TokenError(AuthenticationError):
    """Exception raised for token-related errors."""

    def __init__(self, error_code: ErrorCode, token_info: Optional[str] = None):
        """
        Initialize a TokenError.

        Args:
            error_code: The error code.
            token_info: Optional additional information about the token error.
        """
        super().__init__(error_code, token_info)


class CredentialsError(AuthenticationError):
    """Exception raised for credential-related errors."""

    def __init__(self, error_code: ErrorCode, credential_type: Optional[str] = None):
        """
        Initialize a CredentialsError.

        Args:
            error_code: The error code.
            credential_type: Optional type of credential that failed (e.g., 'Azure', 'API Key').
        """
        super().__init__(error_code, credential_type)


# Data Fetch Exceptions


class DataFetchError(CarmenException):
    """Base class for data fetching errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        source: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a DataFetchError.

        Args:
            error_code: The error code.
            source: Optional name of the data source.
            details: Optional additional details.
        """
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
        query: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a ThanosError.

        Args:
            error_code: The error code.
            query: Optional PromQL query that failed.
            details: Optional additional details.
        """
        self.query = query
        source_details = "Thanos"
        if query:
            source_details = (
                f"{source_details}, query: {query[:100]}..."  # Truncate long queries
            )
        super().__init__(error_code, source_details, details)


class PrometheusQueryError(DataFetchError):
    """Exception raised for Prometheus query errors."""

    def __init__(
        self, error_code: ErrorCode, query: str, details: Optional[str] = None
    ):
        """
        Initialize a PrometheusQueryError.

        Args:
            error_code: The error code.
            query: The PromQL query that failed.
            details: Optional additional details.
        """
        self.query = query
        super().__init__(error_code, "Prometheus", f"query: {query}, {details or ''}")


# Validation Exceptions


class ValidationError(CarmenException):
    """Base class for validation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        field_name: Optional[str] = None,
        invalid_value: Optional[str] = None,
    ):
        """
        Initialize a ValidationError.

        Args:
            error_code: The error code.
            field_name: Optional name of the field that failed validation.
            invalid_value: Optional value that failed validation.
        """
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
        provided_value: Optional[str] = None,
    ):
        """
        Initialize a DateValidationError.

        Args:
            error_code: The error code.
            date_field: Name of the date field.
            provided_value: Optional value that was provided.
        """
        super().__init__(error_code, date_field, provided_value)


class QueryParameterError(ValidationError):
    """Exception raised for query parameter validation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        invalid_params: Optional[list[str]] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a QueryParameterError.

        Args:
            error_code: The error code.
            invalid_params: Optional list of invalid parameter names.
            details: Optional additional details.
        """
        self.invalid_params = invalid_params or []
        param_details = ", ".join(invalid_params) if invalid_params else details
        super().__init__(error_code, param_details)


# File System Exceptions


class FileSystemError(CarmenException):
    """Base class for file system errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        path: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a FileSystemError.

        Args:
            error_code: The error code.
            path: Optional file or directory path.
            details: Optional additional details.
        """
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
        """
        Initialize a FileNotFoundError.

        Args:
            path: Path to the file that was not found.
        """
        super().__init__(ErrorCode.FILE_NOT_FOUND, path)


class FileReadError(FileSystemError):
    """Exception raised when a file cannot be read."""

    def __init__(self, path: str, details: Optional[str] = None):
        """
        Initialize a FileReadError.

        Args:
            path: Path to the file that could not be read.
            details: Optional additional details about the error.
        """
        super().__init__(ErrorCode.FILE_READ_ERROR, path, details)


class FileWriteError(FileSystemError):
    """Exception raised when a file cannot be written."""

    def __init__(self, path: str, details: Optional[str] = None):
        """
        Initialize a FileWriteError.

        Args:
            path: Path to the file that could not be written.
            details: Optional additional details about the error.
        """
        super().__init__(ErrorCode.FILE_WRITE_ERROR, path, details)


class DirectoryError(FileSystemError):
    """Exception raised for directory-related errors."""


# Computation Exceptions


class ComputationError(CarmenException):
    """Base class for computation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        operation: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a ComputationError.

        Args:
            error_code: The error code.
            operation: Optional description of the operation that failed.
            details: Optional additional details.
        """
        self.operation = operation
        message_details = f"operation: {operation}" if operation else None
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)


class DivisionByZeroError(ComputationError):
    """Exception raised when division by zero is encountered."""

    def __init__(self, operation: Optional[str] = None):
        """
        Initialize a DivisionByZeroError.

        Args:
            operation: Optional description of the operation.
        """
        super().__init__(ErrorCode.COMPUTATION_DIVISION_BY_ZERO, operation)


class MissingDataError(ComputationError):
    """Exception raised when required data is missing for computation."""

    def __init__(self, missing_data: str, operation: Optional[str] = None):
        """
        Initialize a MissingDataError.

        Args:
            missing_data: Description of the missing data.
            operation: Optional description of the operation.
        """
        super().__init__(
            ErrorCode.COMPUTATION_MISSING_DATA, operation, f"missing: {missing_data}"
        )


# Impact Framework Exceptions


class ImpactFrameworkError(CarmenException):
    """Base class for Impact Framework errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        manifest_path: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize an ImpactFrameworkError.

        Args:
            error_code: The error code.
            manifest_path: Optional path to the manifest file.
            details: Optional additional details.
        """
        self.manifest_path = manifest_path
        message_details = f"manifest: {manifest_path}" if manifest_path else None
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)


class ImpactFrameworkPluginError(ImpactFrameworkError):
    """Exception raised for Impact Framework plugin errors."""

    def __init__(
        self, plugin_name: str, error_message: str, manifest_path: Optional[str] = None
    ):
        """
        Initialize an ImpactFrameworkPluginError.

        Args:
            plugin_name: Name of the plugin that failed.
            error_message: Error message from the plugin.
            manifest_path: Optional path to the manifest file.
        """
        self.plugin_name = plugin_name
        self.error_message = error_message
        details = f"plugin: {plugin_name}, error: {error_message}"
        super().__init__(ErrorCode.IF_PLUGIN_ERROR, manifest_path, details)


# Database Exceptions


class DatabaseError(CarmenException):
    """Base class for database errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        query: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a DatabaseError.

        Args:
            error_code: The error code.
            query: Optional database query that failed.
            details: Optional additional details.
        """
        self.query = query
        message_details = (
            f"query: {query[:100]}..." if query else None
        )  # Truncate long queries
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)


# External API Exceptions


class ExternalAPIError(CarmenException):
    """Base class for external API errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize an ExternalAPIError.

        Args:
            error_code: The error code.
            api_name: Optional name of the external API.
            endpoint: Optional API endpoint that failed.
            details: Optional additional details.
        """
        self.api_name = api_name
        self.endpoint = endpoint
        message_parts = []
        if api_name:
            message_parts.append(f"API: {api_name}")
        if endpoint:
            message_parts.append(f"endpoint: {endpoint}")
        if details:
            message_parts.append(details)
        message_details = ", ".join(message_parts) if message_parts else None
        super().__init__(error_code, message_details)


# Report Generation Exceptions


class ReportGenerationError(CarmenException):
    """Base class for report generation errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        report_type: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """
        Initialize a ReportGenerationError.

        Args:
            error_code: The error code.
            report_type: Optional type of report being generated.
            details: Optional additional details.
        """
        self.report_type = report_type
        message_details = f"report type: {report_type}" if report_type else None
        if message_details and details:
            message_details = f"{message_details}, {details}"
        elif details:
            message_details = details
        super().__init__(error_code, message_details)
