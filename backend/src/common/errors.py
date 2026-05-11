"""
Error codes and templates for structured error handling across the application.
"""

from __future__ import annotations

from enum import Enum


class ErrorCategory(str, Enum):
    """
    High level error categories
    """

    CONFIGURATION = "configuration"
    DATA_FETCH = "data fetch"
    IMPACT_FRAMEWORK = "impact framework"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external api"
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
    - 8xxx: Database errors
    - 9xxx: External API errors
    - 10xxx: Report generation errors
    """

    # Unknown errors (0xxx)
    UNKNOWN_ERROR = "0001"

    # Configuration errors (1xxx)
    CONFIG_FILE_MISSING = "1001"
    CONFIG_MISSING_PARAMETERS = "1002"
    CONFIG_INVALID_FILE = "1003"
    CONFIG_INVALID_YAML = "1004"
    CONFIG_INVALID_JSON = "1005"
    CONFIG_INVALID_VALUE = "1006"
    CONFIG_VALIDATION_FAILED = "1007"

    # Authentication errors (2xxx)
    AUTH_TOKEN_EXPIRED = "2001"
    AUTH_TOKEN_INVALID = "2002"
    AUTH_CREDENTIALS_MISSING = "2003"
    AUTH_CREDENTIALS_INVALID = "2004"
    AUTH_TOKEN_REFRESH_FAILED = "2005"
    AUTH_UNAUTHORIZED = "2006"

    # Data fetch errors (3xxx)
    DATA_FETCH_FAILED = "3001"
    DATA_FETCH_TIMEOUT = "3002"
    DATA_FETCH_NO_RESULTS = "3003"
    DATA_FETCH_INVALID_RESPONSE = "3004"
    DATA_FETCH_CONNECTION_ERROR = "3005"
    DATA_FETCH_QUERY_INVALID = "3006"

    # Thanos/Prometheus errors (3.1xx)
    THANOS_QUERY_FAILED = "3101"
    THANOS_TIMEOUT = "3102"
    THANOS_INVALID_RESPONSE = "3103"
    THANOS_CONNECTION_ERROR = "3104"
    PROMETHEUS_QUERY_INVALID = "3105"

    # Validation errors (4xxx)
    VALIDATION_INVALID_PARAMETER = "4001"
    VALIDATION_MISSING_PARAMETER = "4002"
    VALIDATION_INVALID_DATE_FORMAT = "4003"
    VALIDATION_INVALID_DATE_RANGE = "4004"
    VALIDATION_INVALID_QUERY_PARAMS = "4005"
    VALIDATION_INVALID_SAMPLING_RATE = "4006"

    # File system errors (5xxx)
    FILE_NOT_FOUND = "5001"
    FILE_READ_ERROR = "5002"
    FILE_WRITE_ERROR = "5003"
    FILE_PERMISSION_DENIED = "5004"
    FILE_INVALID_FORMAT = "5005"
    DIRECTORY_NOT_FOUND = "5006"
    DIRECTORY_CREATE_ERROR = "5007"
    CSV_FILE_NOT_FOUND = "5008"

    # Computation errors (6xxx)
    COMPUTATION_FAILED = "6001"
    COMPUTATION_INVALID_INPUT = "6002"
    COMPUTATION_DIVISION_BY_ZERO = "6003"
    COMPUTATION_OVERFLOW = "6004"
    COMPUTATION_MISSING_DATA = "6005"

    # Impact Framework errors (7xxx)
    IF_EXECUTION_FAILED = "7001"
    IF_INVALID_MANIFEST = "7002"
    IF_PLUGIN_ERROR = "7003"
    IF_OUTPUT_INVALID = "7004"
    IF_METADATA_MISSING = "7005"
    IF_CLOUD_METADATA_FETCH_FAILED = "7006"

    # Database errors (8xxx)
    DB_CONNECTION_ERROR = "8001"
    DB_QUERY_FAILED = "8002"
    DB_INSERT_FAILED = "8003"
    DB_UPDATE_FAILED = "8004"
    DB_DELETE_FAILED = "8005"

    # External API errors (9xxx)
    EXTERNAL_API_ERROR = "9001"
    EXTERNAL_API_TIMEOUT = "9002"
    EXTERNAL_API_INVALID_RESPONSE = "9003"
    EXTERNAL_API_RATE_LIMIT = "9004"

    # Report generation errors (10xxx)
    REPORT_GENERATION_FAILED = "10001"
    REPORT_INVALID_DATA = "10002"
    REPORT_WRITE_FAILED = "10003"
    REPORT_TEMPLATE_ERROR = "10004"


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
    ErrorCode.CONFIG_INVALID_JSON: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration file contains invalid JSON syntax",
    ),
    ErrorCode.CONFIG_INVALID_VALUE: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration contains an invalid value",
    ),
    ErrorCode.CONFIG_VALIDATION_FAILED: ErrorTemplate(
        category=ErrorCategory.CONFIGURATION,
        user_message="configuration validation failed",
    ),
    # Authentication errors
    ErrorCode.AUTH_TOKEN_EXPIRED: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="authentication token has expired",
    ),
    ErrorCode.AUTH_TOKEN_INVALID: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="authentication token is invalid",
    ),
    ErrorCode.AUTH_CREDENTIALS_MISSING: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="authentication credentials are missing",
    ),
    ErrorCode.AUTH_CREDENTIALS_INVALID: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="authentication credentials are invalid",
    ),
    ErrorCode.AUTH_TOKEN_REFRESH_FAILED: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="failed to refresh authentication token after multiple attempts",
    ),
    ErrorCode.AUTH_UNAUTHORIZED: ErrorTemplate(
        category=ErrorCategory.AUTHENTICATION,
        user_message="unauthorized access - authentication required",
    ),
    # Data fetch errors
    ErrorCode.DATA_FETCH_FAILED: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="failed to fetch data from the remote source",
    ),
    ErrorCode.DATA_FETCH_TIMEOUT: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="data fetch operation timed out",
    ),
    ErrorCode.DATA_FETCH_NO_RESULTS: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="no results returned from data source",
    ),
    ErrorCode.DATA_FETCH_INVALID_RESPONSE: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="received invalid response from data source",
    ),
    ErrorCode.DATA_FETCH_CONNECTION_ERROR: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="failed to establish connection to data source",
    ),
    ErrorCode.DATA_FETCH_QUERY_INVALID: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="query syntax is invalid",
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
    ErrorCode.PROMETHEUS_QUERY_INVALID: ErrorTemplate(
        category=ErrorCategory.DATA_FETCH,
        user_message="prometheus query syntax is invalid",
    ),
    # Validation errors
    ErrorCode.VALIDATION_INVALID_PARAMETER: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="provided parameter value is invalid",
    ),
    ErrorCode.VALIDATION_MISSING_PARAMETER: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="required parameter is missing",
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
    ErrorCode.VALIDATION_INVALID_SAMPLING_RATE: ErrorTemplate(
        category=ErrorCategory.VALIDATION,
        user_message="sampling rate is invalid",
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
    ErrorCode.FILE_WRITE_ERROR: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="failed to write to file",
    ),
    ErrorCode.FILE_PERMISSION_DENIED: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="permission denied for file operation",
    ),
    ErrorCode.FILE_INVALID_FORMAT: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="file format is invalid or not supported",
    ),
    ErrorCode.DIRECTORY_NOT_FOUND: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="specified directory was not found",
    ),
    ErrorCode.DIRECTORY_CREATE_ERROR: ErrorTemplate(
        category=ErrorCategory.FILE_SYSTEM,
        user_message="failed to create directory",
    ),
    # Computation errors
    ErrorCode.COMPUTATION_FAILED: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="computation failed",
    ),
    ErrorCode.COMPUTATION_INVALID_INPUT: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="invalid input provided for computation",
    ),
    ErrorCode.COMPUTATION_DIVISION_BY_ZERO: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="division by zero encountered in computation",
    ),
    ErrorCode.COMPUTATION_OVERFLOW: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="numeric overflow encountered in computation",
    ),
    ErrorCode.COMPUTATION_MISSING_DATA: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="required data missing for computation",
    ),
    # Impact Framework errors
    ErrorCode.IF_EXECUTION_FAILED: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="impact framework execution failed",
    ),
    ErrorCode.IF_INVALID_MANIFEST: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="impact framework manifest is invalid",
    ),
    ErrorCode.IF_PLUGIN_ERROR: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="impact framework plugin encountered an error",
    ),
    ErrorCode.IF_OUTPUT_INVALID: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="impact framework output is invalid",
    ),
    ErrorCode.IF_METADATA_MISSING: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="impact framework metadata is missing",
    ),
    ErrorCode.IF_CLOUD_METADATA_FETCH_FAILED: ErrorTemplate(
        category=ErrorCategory.IMPACT_FRAMEWORK,
        user_message="failed to fetch cloud metadata for impact framework",
    ),
    # Database errors
    ErrorCode.DB_CONNECTION_ERROR: ErrorTemplate(
        category=ErrorCategory.DATABASE,
        user_message="failed to connect to database",
    ),
    ErrorCode.DB_QUERY_FAILED: ErrorTemplate(
        category=ErrorCategory.DATABASE,
        user_message="database query failed",
    ),
    ErrorCode.DB_INSERT_FAILED: ErrorTemplate(
        category=ErrorCategory.DATABASE,
        user_message="failed to insert data into database",
    ),
    ErrorCode.DB_UPDATE_FAILED: ErrorTemplate(
        category=ErrorCategory.DATABASE,
        user_message="failed to update data in database",
    ),
    ErrorCode.DB_DELETE_FAILED: ErrorTemplate(
        category=ErrorCategory.DATABASE,
        user_message="failed to delete data from database",
    ),
    # External API errors
    ErrorCode.EXTERNAL_API_ERROR: ErrorTemplate(
        category=ErrorCategory.EXTERNAL_API,
        user_message="external API request failed",
    ),
    ErrorCode.EXTERNAL_API_TIMEOUT: ErrorTemplate(
        category=ErrorCategory.EXTERNAL_API,
        user_message="external API request timed out",
    ),
    ErrorCode.EXTERNAL_API_INVALID_RESPONSE: ErrorTemplate(
        category=ErrorCategory.EXTERNAL_API,
        user_message="received invalid response from external API",
    ),
    ErrorCode.EXTERNAL_API_RATE_LIMIT: ErrorTemplate(
        category=ErrorCategory.EXTERNAL_API,
        user_message="external API rate limit exceeded",
    ),
    # Report generation errors
    ErrorCode.REPORT_GENERATION_FAILED: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="report generation failed",
    ),
    ErrorCode.REPORT_INVALID_DATA: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="invalid data provided for report generation",
    ),
    ErrorCode.REPORT_WRITE_FAILED: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="failed to write report to destination",
    ),
    ErrorCode.REPORT_TEMPLATE_ERROR: ErrorTemplate(
        category=ErrorCategory.COMPUTATION,
        user_message="report template processing failed",
    ),
}
