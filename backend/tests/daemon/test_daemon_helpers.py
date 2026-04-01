"""
Unit tests for the daemon_helpers class.
"""

import unittest
from backend.src.daemon.readers.helpers.daemon_helpers import (
    calculate_vm_count_for_missing_regions,
    log_missing_regions,
)


class TestDaemonHelpers(unittest.TestCase):
    """
    Unit tests for the DaemonHelpers class.
    """

    def test_calculate_vm_count_for_missing_regions_region_in_constants(self):
        """
        Test that calculate_vm_count_for_missing_regions correctly behaves when the region is in constants dictionary.
        """
        mock_dict = {"example_region": 5}
        calculate_vm_count_for_missing_regions(mock_dict, "eastus")

        self.assertEqual(mock_dict, {"example_region": 5})

    def test_calculate_vm_count_for_missing_regions_missing_region_not_in_dictionary(
        self,
    ):
        """
        Test that calculate_vm_count_for_missing_regions correctly adds missing region to dictionary.
        """
        mock_dict = {"example_region": 5}

        calculate_vm_count_for_missing_regions(mock_dict, "ex_region")

        self.assertEqual(mock_dict, {"example_region": 5, "ex_region": 1})

    def test_calculate_vm_count_for_missing_regions_missing_region_in_dictionary(self):
        """
        Test that calculate_vm_count_for_missing_regions correctly increments vm count when
        missing region is in dictionary.
        """
        mock_dict = {"example_region": 5}

        calculate_vm_count_for_missing_regions(mock_dict, "example_region")

        self.assertEqual(mock_dict, {"example_region": 6})

    def test_log_missing_regions(self):
        """
        Test that log_missing_regions correctly logs warning for missing regions.
        """
        mock_dict = {"example_region": 5}

        with self.assertLogs(level="WARNING") as log:
            log_missing_regions(mock_dict)
            self.assertIn(
                "unknown region 'example_region' detected with 5 VMs", log.output[0]
            )
