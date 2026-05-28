"""
unit tests for various helper functions in the project.
"""

import subprocess
import unittest
from datetime import datetime
from json.decoder import JSONDecodeError
from unittest.mock import patch, MagicMock
from backend.src.common.enums import SamplingRate
from backend.src.common.carmen_exception import (
    QueryParameterError,
    DataFetchError,
    ValidationError,
)
from backend.src.utils.helpers import (
    remove_unnecessary,
    run_command_and_parse_json,
    validate_query_parameters,
    get_result_from_response,
    convert_to_seconds,
    get_formatted_string,
    create_list_pattern,
    return_desired_metric_from_response,
    group_clusters_by_level,
    get_timestamps,
)


class TestHelpers(unittest.TestCase):
    """
    Test cases for helper functions.
    """

    def test_validate_query_parameters_unexpected_params(self):
        """
        Test case for validating query parameters with unexpected parameters.
        """
        request = MagicMock()
        request.query_params = {
            "param1": "value1",
            "param2": "value2",
            "param3": "value3",
        }
        expected_params = {"param1", "param2"}

        with self.assertRaises(QueryParameterError) as context:
            validate_query_parameters(request, expected_params)

        self.assertEqual(context.exception.error_code.value, "4005")

    def test_validate_query_parameters_expected_params(self):
        """Test case for validating query parameters with no unexpected parameters."""
        request = MagicMock()
        request.query_params = {
            "param1": "value1",
            "param2": "value2",
        }
        expected_params = {"param1", "param2"}

        # No exception should be raised if the parameters are as expected
        try:
            validate_query_parameters(request, expected_params)
        except QueryParameterError:
            self.fail(
                "validate_query_parameters raised QueryParameterError unexpectedly!"
            )

    def test_get_result_from_response_valid_json(self):
        """
        Test case for getting result from response with valid JSON.
        """
        response = MagicMock()
        response.content = '{"data": {"result": ["label1", "label2"]}}'
        labels = get_result_from_response(response)
        self.assertEqual(labels, ["label1", "label2"])

    @patch("json.loads")
    def test_get_result_from_response_key_error(self, mock_json_loads):
        """
        Test case for key error while getting to result from response
        """
        # Mock json.loads to return a dictionary without the "data" key
        mock_json_loads.return_value = {"error": "missing data"}

        # Call the function and expect it to raise a DataFetchError
        with self.assertRaises(DataFetchError):
            get_result_from_response(MagicMock())

    @patch("json.loads")
    def test_get_result_from_response_json_decode_error(self, mock_json_loads):
        """
        Test case for json decode error while getting to result from response
        """
        # Mock json.loads to raise a JSONDecodeError
        mock_json_loads.side_effect = JSONDecodeError(msg="invalid JSON", doc="", pos=0)

        # Call the function and expect it to raise a DataFetchError
        with self.assertRaises(DataFetchError):
            get_result_from_response(MagicMock())

    def test_run_command_and_parse_json(self):
        """
        Test case for checking if it parsed the json correctly
        """
        with patch("subprocess.run") as mock_subprocess_run:
            # Test successful JSON decoding
            mock_subprocess_run.return_value.stdout = '[{"Rating": 540.6}]'
            result = run_command_and_parse_json("fake_command")
            assert result == [{"Rating": 540.6}]

            # Test empty JSON output
            mock_subprocess_run.return_value.stdout = None
            result = run_command_and_parse_json("fake_command")
            assert result is None

            # Test JSON decoding error
            mock_subprocess_run.return_value.stdout = "invalid_json"
            result = run_command_and_parse_json("fake_command")
            assert result is None

            # Test subprocess.CalledProcessError
            mock_subprocess_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd="fake_command", stderr="Command failed"
            )
            result = run_command_and_parse_json("fake_command")
            assert result is None

    def test_remove_unnecessary(self):
        """
        Ensures that the remove_unnecessary function correctly removes unnecessary characters from a string.
        """
        result = remove_unnecessary("erd8-dd-54d")
        expected = "erd-dd-d"
        assert result == expected

    def test_time_conversion(self):
        """
        Ensures that the time conversion function correctly converts a string to a datetime object.
        """

        # Test case for converting hours
        result = convert_to_seconds("60h")
        expected = 216000
        assert result == expected

        # Test case for converting minutes
        result = convert_to_seconds("30m")
        expected = 1800
        assert result == expected

        # Test case for converting seconds
        result = convert_to_seconds("30s")
        expected = 30
        assert result == expected

        # Test invalid time format
        with self.assertRaises(ValidationError):
            convert_to_seconds("invalid")

    def test_get_formatted_string_success(self):
        """
        Ensures that the function returns the correctly formatted string when no KeyError occurs.
        """
        # Define format string, key and expected result
        format_str = "Test, {value}!"
        kwargs = {"value": "value1"}
        expected_result = "Test, value1!"

        # Call function with correct key
        result = get_formatted_string(format_str, **kwargs)

        # Check if the function returns the correct answer
        self.assertEqual(result, expected_result)

    def test_get_formatted_string_key_error(self):
        """
        Ensure that the function returns None for an invalid key.
        """
        # Define format string and invalid key
        format_str = "Test, {value}!"
        kwargs = {"invalid_key": "value1"}

        # Call function with invalid key
        result = get_formatted_string(format_str, **kwargs)

        # Check if function returns None
        self.assertIsNone(result)

    def test_return_desired_metric_from_response(self):
        """Test return_desired_metric_from_response with valid data."""
        data = [
            {"metric": {"key1": "value1"}, "value": [1714999789, "1"]},
            {"metric": {"key1": "value2"}, "value": [1714999789, "1"]},
            {"metric": {"key1": "value3"}, "value": [1714999789, "1"]},
        ]
        result = return_desired_metric_from_response(data, "key1")
        self.assertEqual(result, ["value1", "value2", "value3"])

    def test_create_list_pattern_with_args(self):
        """Test create_list_pattern with arguments."""
        result = create_list_pattern(
            "|", ["a", "b", "c"]
        )  # Pass a list as the first argument in *args
        self.assertEqual(result, "a|b|c")

    def test_create_list_pattern_with_none(self):
        """Test create_list_pattern with an empty list in *args."""
        result = create_list_pattern("|", [])
        self.assertEqual(result, ".+")

    def test_group_clusters_by_level_valid(self):
        """Tests the function with a valid grouping level."""
        input_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        grouping_level = 3
        expected_output = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        self.assertEqual(
            group_clusters_by_level(input_list, grouping_level), expected_output
        )

    def test_group_clusters_by_level_invalid(self):
        """Tests the function with invalid grouping level."""
        input_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        grouping_level = 15
        expected_output = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
        self.assertEqual(
            group_clusters_by_level(input_list, grouping_level), expected_output
        )

    def test_get_timestamps(self):
        """
        Test that get_timestamps generates the correct list of timestamps
        based on the given interval.
        """
        interval_start = datetime(2024, 12, 20, 0, 0)
        interval_end = datetime(2024, 12, 20, 1, 0)
        sampling_rate = SamplingRate.THIRTY_MINUTES
        expected_timestamps = [
            datetime(2024, 12, 20, 0, 0),
            datetime(2024, 12, 20, 0, 30),
            datetime(2024, 12, 20, 1, 0),
        ]
        timestamps = get_timestamps(interval_start, interval_end, sampling_rate)
        self.assertListEqual(timestamps, expected_timestamps)
