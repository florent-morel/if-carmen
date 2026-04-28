"""
Unit tests for the daemon_helpers module.

Missing-region/provider tracking is now done via collections.Counter inside
Reader_Compute; daemon_helpers is only responsible for logging and VM creation.
"""

import unittest
from backend.src.daemon.readers.helpers.daemon_helpers import (
    log_missing_regions,
    log_missing_providers,
    get_row_data,
)


class TestLogMissingRegions(unittest.TestCase):
    def test_logs_warning_per_region(self):
        with self.assertLogs(level="WARNING") as log:
            log_missing_regions({"eastus2": 3, "unknown_region": 1})
        messages = "\n".join(log.output)
        self.assertIn("unknown region 'eastus2': 3 VMs", messages)
        self.assertIn("unknown region 'unknown_region': 1 VMs", messages)

    def test_empty_dict_produces_no_logs(self):
        # assertLogs would fail if nothing is logged — use assertRaises to confirm
        with self.assertRaises(AssertionError):
            with self.assertLogs(level="WARNING"):
                log_missing_regions({})


class TestLogMissingProviders(unittest.TestCase):
    def test_logs_warning_per_provider(self):
        with self.assertLogs(level="WARNING") as log:
            log_missing_providers({"gcp": 7, "unknown_csp": 2})
        messages = "\n".join(log.output)
        self.assertIn("unknown provider 'gcp': 7 VMs", messages)
        self.assertIn("unknown provider 'unknown_csp': 2 VMs", messages)

    def test_empty_dict_produces_no_logs(self):
        with self.assertRaises(AssertionError):
            with self.assertLogs(level="WARNING"):
                log_missing_providers({})


class TestGetRowData(unittest.TestCase):
    def test_returns_value_when_present(self):
        self.assertEqual(get_row_data("eastus"), "eastus")

    def test_returns_empty_string_for_dash(self):
        self.assertEqual(get_row_data("-"), "")

    def test_returns_empty_string_for_empty_string(self):
        self.assertEqual(get_row_data(""), "")

    def test_returns_empty_string_for_none(self):
        self.assertEqual(get_row_data(None), "")
