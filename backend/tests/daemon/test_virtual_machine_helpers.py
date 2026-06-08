"""
Unit tests for the virtual_machine_helpers module.
"""

import unittest
from backend.src.daemon.readers.helpers.virtual_machine_helpers import (
    get_row_data,
)


class TestGetRowData(unittest.TestCase):
    def test_returns_value_when_present(self):
        self.assertEqual(get_row_data("eastus"), "eastus")

    def test_returns_empty_string_for_dash(self):
        self.assertEqual(get_row_data("-"), "")

    def test_returns_empty_string_for_empty_string(self):
        self.assertEqual(get_row_data(""), "")

    def test_returns_empty_string_for_none(self):
        self.assertEqual(get_row_data(None), "")
