"""
Error codes and templates for structured error handling across the application.
"""

from __future__ import annotations

from enum import Enum


class ErrorCategory(str, Enum):
    """
    High level error categories
    """

    UNKNOWN = "unknown"
    CONFIGURATION = "configuration"
    DATA_FETCH = "data fetch"
    IMPACT_FRAMEWORK = "impact framework"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    FILE_SYSTEM = "file system"
    COMPUTATION = "computation"


class ErrorCode(str, Enum):
    """
    Enumeration of error codes used throughout the application.

    Error codes are organized by category:
    - 0xxx: Unknown errors
    - 1xxx: Configuration errors
    - 2xxx: Authentication errors
    - 3xxx: Data fetch errors
    - 4xxx: Validation errors
    - 5xxx: File system errors
    - 6xxx: Computation errors
    - 7xxx: Impact Framework errors
    """

    # Unknown errors (0xxx)
    UNKNOWN_ERROR = "0001"

    # Configuration errors (1xxx)
    CONFIG_FILE_MISSING = "1001"
    CONFIG_MISSING_PARAMETERS = "1002"
    CONFIG_INVALID_FILE = "1003"
    CONFIG_INVALID_YAML = "1004"
    CONFIG_INVALID_VALUE = "1006"
    CONFIG_VALIDATION_FAILED = "1007"
    CONFIG_NO_PROCESSOR = "1008"

    # Authentication errors (2xxx)
    AUTH_TOKEN_REFRESH_FAILED = "2005"

    # Data fetch errors (3xxx)
    DATA_FETCH_FAILED = "3001"
    DATA_FETCH_NO_RESULTS = "3003"
    DATA_FETCH_INVALID_RESPONSE = "3004"

    # Thanos/Prometheus errors (3.1xx)
    THANOS_QUERY_FAILED = "3101"
    THANOS_TIMEOUT = "3102"
    THANOS_INVALID_RESPONSE = "3103"
    THANOS_CONNECTION_ERROR = "3104"

    # Validation errors (4xxx)
    VALIDATION_INVALID_PARAMETER = "4001"
    VALIDATION_INVALID_DATE_FORMAT = "4003"
    VALIDATION_INVALID_DATE_RANGE = "4004"
    VALIDATION_INVALID_QUERY_PARAMS = "4005"

    # File system errors (5xxx)
    FILE_NOT_FOUND = "5001"
    FILE_READ_ERROR = "5002"
    FILE_PERMISSION_DENIED = "5004"
    FILE_INVALID_FORMAT = "5005"
    CSV_FILE_NOT_FOUND = "5008"

    # Computation errors (6xxx)
    COMPUTATION_FAILED = "6001"

    # Impact Framework errors (7xxx)
    IF_EXECUTION_FAILED = "7001"
    UNKNOWN_VM_INSTANCE_TYPE = "7007"  # VM type not in instances CSV and vcpu_count not resolvable


class ErrorTemplate:
    """
    Template for creating structured error messages.
    """

    def __init__(
        self,
        category: ErrorCategory,
        user_message: str,
    ) -> None:
        self.category = category
        self.message = user_message

    def to_string(self) -> str:
        """
        Converts the error template to its string representation.
        """
        return self.message


ERRORS: dict[str, ErrorTemplate] = {
    # Unknown error
    ErrorCode.UNKNOWN_ERROR: ErrorTemplate(
        category=ErrorCategory.UNKNOWN,
        user_message="unknown error raised",
    ),
    # Configuration errors
    ErrorCode.CONFIG_MISSING_PARAMETERS: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="required parameters are missing: ",
    ),
    ErrorCode.CONFIG_FILE_MISSING: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="path provided for configuration was not found",
    ),
    ErrorCode.CONFIG_INVALID_FILE: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration file is empty, invalid, or contains only comments",
    ),
    ErrorCode.CONFIG_INVALID_YAML: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration file contains invalid YAML syntax",
    ),
    ErrorCode.CONFIG_INVALID_VALUE: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration contains an invalid value",
    ),
    ErrorCode.CONFIG_VALIDATION_FAILED: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration validation failed",
    ),
    ErrorCode.CONFIG_NO_PROCESSOR: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="No processor found for Carmen Daemon execution.",
    ),
    # Authentication errors
    ErrorCode.AUTH_TOKEN_REFRESH_FAILED: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="failed to refresh authentication token after multiple attempts",
    ),
    # Data fetch errors
    ErrorCode.DATA_FETCH_FAILED: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="failed to fetch data from the remote source",
    ),
    ErrorCode.DATA_FETCH_NO_RESULTS: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="no results returned from data source",
    ),
    ErrorCode.DATA_FETCH_INVALID_RESPONSE: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="received invalid response from data source",
    ),
    # Thanos/Prometheus errors
    ErrorCode.THANOS_QUERY_FAILED: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="failed to execute thanos query",
    ),
    ErrorCode.THANOS_TIMEOUT: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="Thanos query execution timed out",
    ),
    ErrorCode.THANOS_INVALID_RESPONSE: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="received invalid response from thanos",
    ),
    ErrorCode.THANOS_CONNECTION_ERROR: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="failed to connect to thanos endpoint",
    ),
    # Validation errors
    ErrorCode.VALIDATION_INVALID_PARAMETER: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="provided parameter value is invalid",
    ),
    ErrorCode.VALIDATION_INVALID_DATE_FORMAT: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="date format is invalid, expected format: yyyy-mm-dd hh:mm:ss",
    ),
    ErrorCode.VALIDATION_INVALID_DATE_RANGE: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="date range is invalid, start date must be before end date",
    ),
    ErrorCode.VALIDATION_INVALID_QUERY_PARAMS: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="invalid query parameters provided",
    ),
    # File system errors
    ErrorCode.FILE_NOT_FOUND: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="specified file was not found",
    ),
    ErrorCode.CSV_FILE_NOT_FOUND: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="CSV data is empty",
    ),
    ErrorCode.FILE_READ_ERROR: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="failed to read file",
    ),
    ErrorCode.FILE_PERMISSION_DENIED: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="permission denied for file operation",
    ),
    ErrorCode.FILE_INVALID_FORMAT: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="file format is invalid or not supported",
    ),
    # Computation errors
    ErrorCode.COMPUTATION_FAILED: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="computation failed",
    ),
    # Impact Framework errors
    ErrorCode.IF_EXECUTION_FAILED: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="impact framework execution failed",
    ),
    ErrorCode.UNKNOWN_VM_INSTANCE_TYPE: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="VM instance type is unknown and vCPU count could not be resolved; cannot compute CPU energy",
    ),
}
