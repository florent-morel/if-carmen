"""
This module contains helper functions used in the project
"""

from __future__ import annotations

import pathlib
import subprocess
import logging
import json
import re
from typing import Any
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
import yaml
from fastapi import Request
from jinja2 import Template
import httpx
from backend.src.common.constants import RATE_TO_DURATION
from backend.src.common.enums import SamplingRate
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import (
    DataFetchError,
    QueryParameterError,
    ValidationError,
    FileReadError,
    FileNotFoundError as CustomFileNotFoundError,
)

logger = logging.getLogger(__name__)


def validate_query_parameters(
    request: Request, expected_params: set[str]
) -> None:  # DO: apply RequestValidationError of FastAPI
    """
    Validate query parameters in the request against the expected parameters.

    :param request: The FastAPI request object.
    :param expected_params: The set of expected query parameters.
    :raises QueryParameterError: If unexpected query parameters are found.
    """
    unexpected_params_set = set(request.query_params.keys()) - expected_params
    if unexpected_params_set:
        raise QueryParameterError(
            ErrorCode.VALIDATION_INVALID_QUERY_PARAMS,
            invalid_params=list(unexpected_params_set),
        )


def get_result_from_response(response: httpx.Response) -> list[dict[str, Any]]:
    """
    Get the labels from a Thanos JSON response.

    Args:
        response: The HTTP response containing JSON data.

    Returns:
        The list of labels extracted from the response.

    Raises:
        DataFetchError: If there is an error in parsing the JSON or extracting the data.
    """
    try:
        jsonified_response: dict[str, Any] = json.loads(response.content)
        return jsonified_response["data"]["result"]
    except KeyError as ex:
        logger.exception("Missing 'data' or 'result' in response")
        raise DataFetchError(
            ErrorCode.DATA_FETCH_INVALID_RESPONSE,
            details="Invalid structure in JSON response - missing 'data' or 'result' field",
        ) from ex
    except JSONDecodeError as ex:
        logger.exception("Failed to decode JSON response")
        raise DataFetchError(
            ErrorCode.DATA_FETCH_INVALID_RESPONSE,
            details="Unable to parse JSON from response",
        ) from ex


def str_to_float(string: str | None) -> float:
    """
    Convert the string to a float and returns 0 if the given string is empty or None.
    """
    if string:
        return float(string)
    return 0.0


def return_desired_metric_from_response(
    data: list[dict[str, Any]], key: str
) -> list[Any]:
    """
    Extracts values corresponding to the specified key from dictionaries in a list.

    Args:
        data (list): A list of dictionaries containing metric data.
        key (str): The key whose corresponding value needs to be extracted.

    Returns:
        list: A list containing the values corresponding to the specified key

    """
    return [d["metric"][key] for d in data if d["metric"]]


def run_command_and_parse_json(command: list[str]) -> dict[str, Any] | None:
    """
    Run a command in the shell that produces a JSON and parse the JSON output to a dictionary

    :param command: The shell command to execute.
    :return: The parsed JSON output as a dictionary, or None if an error occurs.
    """
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
        if result.stdout is None:
            logger.error("Command did not produce any output.")
            return None

        json_output: dict[str, Any] = json.loads(result.stdout)
        return json_output

    except subprocess.CalledProcessError as ex:
        logger.exception(
            "Command failed with return code %s. Error output: %s",
            ex.returncode,
            ex.stderr,
        )
        return None

    except json.JSONDecodeError:
        logger.exception("Error decoding JSON")
        return None


def remove_unnecessary(string_with_digits: str) -> str:
    """
    Removes digits from a given string.

    :param string_with_digits: The string from which digits should be removed.
    :return: A new string with the digits removed.
    """
    string_without_digits = re.sub(r"\d", "", string_with_digits)
    return string_without_digits


def create_list_pattern(delimiter: str, *args: list[str] | None) -> str:
    """
    Creates a regex pattern based on the arguments.

    Args:
        delimiter: The char value that separates the list of values
        *args: Argument list containing strings.

    Returns:
        str: A regex pattern created by joining the strings with delimiter value if the first argument is not None,
             otherwise returns the regex pattern ".+" (match any character).

    """
    if args[0]:
        list_pattern = delimiter.join(*args)
    else:
        list_pattern = ".+"  # regex pattern for all
    return list_pattern


def get_formatted_string(format_str: str, **kwargs: Any) -> str | None:
    """
    Format a string using keyword arguments.

    :param format_str: The formatting string containing placeholders.
    :type format_str: str
    :param kwargs: Keyword arguments containing key-value pairs to be substituted into the formatting string.
    :type kwargs: dict
    :return: The formatted string, or None if a KeyError occurs during formatting.
    :rtype: str or None
    """
    try:
        return format_str.format(**kwargs)
    except KeyError:
        logger.exception("Error formatting string")
        return None


def group_clusters_by_level(
    cluster_list: list[str], grouping_level: int
) -> list[list[str]]:
    """
    Groups elements of input_list into sub-lists based on grouping_level.

    Args:
        cluster_list (list): List of clusters to be grouped.
        grouping_level (int): Number of clusters in each subgroup.

    Returns:
        list: List of sublists where each sublist contains clusters according to grouping_level.
    """
    return [
        cluster_list[i : i + grouping_level]
        for i in range(0, len(cluster_list), grouping_level)
    ]


def get_start_time() -> datetime:
    """Function to get the default start date value for /run-engine/ endpoint."""
    return datetime.strptime(
        (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
        "%Y-%m-%d %H:%M:%S",
    )


def get_end_time() -> datetime:
    """Function to get the default end date value for /run-engine/ endpoint."""
    return datetime.strptime(
        (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "%Y-%m-%d %H:%M:%S",
    )


def read_file(path: str) -> Template | dict[str, Any]:
    """
    Reads the .j2, .yaml or .json files and returns jinja2.environment.Template object or a dict
    :param path: input file path
    :return: A Jinja2 template object if the file is a .j2 file, or a dictionary for .yaml or .json files.

    Raises:
        CustomFileNotFoundError: If the file is not found.
        FileReadError: If the file cannot be read or parsed.
    """
    try:
        with open(path, mode="r", encoding="utf-8") as in_file:
            file_extension = pathlib.Path(path).suffix
            if file_extension == ".j2":
                template_text = in_file.read()
                return Template(template_text)
            if file_extension in [".yml", ".yaml"]:
                return yaml.safe_load(in_file)
            if file_extension == ".json":
                return json.loads(in_file.read())

            # Unsupported file extension
            raise FileReadError(
                str(path),
                details="File extension is not supported! Supported: .j2, .yml, .yaml, .json",
            )

    except FileNotFoundError as ex:
        logger.exception("File not found: %s", path)
        raise CustomFileNotFoundError(str(path)) from ex
    except (yaml.YAMLError, JSONDecodeError) as ex:
        logger.exception("Failed to parse file: %s", path)
        raise FileReadError(
            str(path),
            details=f"Failed to parse file content: {str(ex)}",
        ) from ex
    except Exception as ex:
        logger.exception("Error reading file: %s", path)
        raise FileReadError(str(path), details=str(ex)) from ex


def convert_to_seconds(time_str) -> int:
    """
    Convert a time string (e.g., '30m', '1h') to seconds.

    Raises:
        ValidationError: If the time format is invalid.
    """
    multiplier = {"s": 1, "m": 60, "h": 3600}
    if time_str and time_str[-1] in multiplier:
        try:
            return int(time_str[:-1]) * multiplier[time_str[-1]]
        except ValueError as ex:
            raise ValidationError(
                ErrorCode.VALIDATION_INVALID_PARAMETER,
                field_name="time_str",
                invalid_value=time_str,
            ) from ex
    raise ValidationError(
        ErrorCode.VALIDATION_INVALID_PARAMETER,
        field_name="time_str",
        invalid_value=time_str,
    )


def subtract_last_time_point(
    date_time: datetime, sampling_rate: SamplingRate
) -> datetime:
    """
    Subtract the defined sampling rate interval from the given datetime.

    Parameters:
    - date_time (datetime): The datetime to adjust.
    - sampling_rate (SamplingRate): The sampling rate to subtract.

    Returns:
    - datetime: The adjusted datetime.
    """
    delta = RATE_TO_DURATION[sampling_rate]
    adjusted_time = date_time - delta
    return adjusted_time


def get_timestamps(
    interval_start: datetime, interval_end: datetime, sampling_rate: SamplingRate
) -> list[datetime]:
    """
    Generate a list of timestamps from start to end at specified intervals.

    Parameters:
    start (datetime): The starting datetime.
    end (datetime): The ending datetime.
    sampling_rate (str): The interval between timestamps.
                             Valid values are
                             '15s', '30s', '1m', '5m', '30m', '1h', '6h', '1d'.

    Returns:
    List[datetime]: A list of datetime objects
                    at the specified intervals from start to end.

    Raises:
    ValueError: If the sampling_interval is not one of the valid values.
    """
    timestamps = []
    current_timepoint = interval_start
    interval = RATE_TO_DURATION[sampling_rate]

    while current_timepoint <= interval_end:
        timestamps.append(current_timepoint)
        current_timepoint += interval

    return timestamps


def get_row_data(row_data: str) -> str:
    """
    Helper function to get row data, returns empty string if the data is missing or represented as '-'.
    """
    return row_data if row_data != "-" and row_data else ""
