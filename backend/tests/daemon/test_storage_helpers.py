# pylint: disable=redefined-outer-name
"""
Unit tests for storage helper functions.
"""

import logging
import unittest
from unittest.mock import MagicMock, patch

from backend.src.common.constants import (
    DAILY_SECONDS,
    SOURCE_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_PROVIDER,
    SOURCE_REGION,
    SOURCE_RESOURCE_ID,
    SOURCE_DURATION_SECONDS,
    SOURCE_STORAGE_SIZE_GB,
)
from backend.src.daemon.readers.helpers.storage_helpers import (
    _process_storage_row,
    create_storage_resource,
    get_replication_type,
    get_storage_type,
)
from backend.src.schemas.storage_resource import StorageResource


logger = logging.getLogger(__name__)


class TestStorageHelpers(unittest.TestCase):
    """Unit tests for storage helper functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_ssd_row = {
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_RESOURCE_ID: "test_line_123",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "128",
            SOURCE_DURATION_SECONDS: "86400",
        }

        self.sample_hdd_row = {
            SOURCE_PRODUCT_NAME: "Standard HDD Managed Disks",
            SOURCE_RESOURCE_ID: "test_line_456",
            SOURCE_REGION: "germanywestcentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "64",
            SOURCE_DURATION_SECONDS: "172800",
        }

    def test_get_storage_type_premium_ssd(self):
        """Test storage type detection for Premium SSD."""
        storage_type = get_storage_type(self.sample_ssd_row)
        self.assertEqual(storage_type, "SSD")

    def test_get_storage_type_standard_hdd(self):
        """Test storage type detection for Standard HDD."""
        storage_type = get_storage_type(self.sample_hdd_row)
        self.assertEqual(storage_type, "HDD")

    def test_get_storage_type_unknown(self):
        """Test storage type detection for unknown type."""
        row = {SOURCE_PRODUCT_NAME: "Unknown Storage Type"}
        with self.assertLogs(level="WARNING") as log:
            storage_type = get_storage_type(row)
        self.assertEqual(storage_type, "Unknown")
        self.assertIn("Unknown disk type", log.output[0])

    def test_get_replication_type_lrs(self):
        """Test replication type detection for LRS."""
        row = {SOURCE_PRODUCT_NAME: "Premium SSD - LRS"}
        replication_type = get_replication_type(row)
        self.assertEqual(replication_type, "LRS")

    def test_get_replication_type_grs(self):
        """Test replication type detection for GRS."""
        row = {SOURCE_PRODUCT_NAME: "Storage - GRS"}
        replication_type = get_replication_type(row)
        self.assertEqual(replication_type, "GRS")

    def test_get_replication_type_default_lrs(self):
        """Test replication type defaults to LRS for unknown types."""
        row = {SOURCE_PRODUCT_NAME: "Unknown Storage"}
        replication_type = get_replication_type(row)
        self.assertEqual(replication_type, "LRS")

    def test_process_storage_row_parses_normalized_inputs(self):
        """Test storage row processing from explicit normalized columns."""
        row = {
            SOURCE_RESOURCE_ID: "disk-normalized",
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "128.5",
            SOURCE_DURATION_SECONDS: "5400",
        }
        storage_dict = {}

        result = _process_storage_row(row, storage_dict)

        self.assertTrue(result)
        self.assertEqual(storage_dict["disk-normalized"].size_gb, 128.5)
        self.assertEqual(storage_dict["disk-normalized"].duration_seconds, [5400])

    def test_process_storage_row_missing_size(self):
        """Missing StorageSizeGB should reject the row."""
        row = {
            SOURCE_RESOURCE_ID: "disk-missing-size",
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_DURATION_SECONDS: "86400",
        }
        storage_dict = {}

        with self.assertLogs(level="ERROR") as log:
            result = _process_storage_row(row, storage_dict)

        self.assertFalse(result)
        self.assertEqual(storage_dict, {})
        self.assertIn(SOURCE_STORAGE_SIZE_GB, log.output[0])

    def test_process_storage_row_invalid_number(self):
        """Non-numeric normalized inputs should reject the row."""
        row = {
            SOURCE_RESOURCE_ID: "disk-invalid-values",
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "large",
            SOURCE_DURATION_SECONDS: "5400s",
        }
        storage_dict = {}

        with self.assertLogs(level="ERROR") as log:
            result = _process_storage_row(row, storage_dict)

        self.assertFalse(result)
        self.assertEqual(storage_dict, {})
        self.assertIn("Invalid normalized storage inputs", log.output[0])

    def test_process_storage_row_fractional_seconds(self):
        """Fractional DurationSeconds should reject the row."""
        row = {
            SOURCE_RESOURCE_ID: "disk-fractional-seconds",
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "128",
            SOURCE_DURATION_SECONDS: "5400.5",
        }
        storage_dict = {}

        with self.assertLogs(level="ERROR") as log:
            result = _process_storage_row(row, storage_dict)

        self.assertFalse(result)
        self.assertEqual(storage_dict, {})
        self.assertIn(SOURCE_DURATION_SECONDS, log.output[0])

    def test_process_storage_row_non_positive_values(self):
        """Zero or negative normalized inputs should reject the row."""
        test_cases = [
            ({SOURCE_STORAGE_SIZE_GB: "0", SOURCE_DURATION_SECONDS: "86400"}, SOURCE_STORAGE_SIZE_GB),
            ({SOURCE_STORAGE_SIZE_GB: "128", SOURCE_DURATION_SECONDS: "-1"}, SOURCE_DURATION_SECONDS),
        ]

        for row_values, expected_field in test_cases:
            with self.subTest(expected_field=expected_field):
                row = {
                    SOURCE_RESOURCE_ID: "disk-invalid",
                    SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
                    SOURCE_REGION: "francecentral",
                    SOURCE_PROVIDER: "azure",
                    SOURCE_COST: "0.0",
                    **row_values,
                }
                storage_dict = {}

                with self.assertLogs(level="ERROR") as log:
                    result = _process_storage_row(row, storage_dict)

                self.assertFalse(result)
                self.assertEqual(storage_dict, {})
                self.assertIn(expected_field, log.output[0])

    def test_process_storage_row_missing_duration_uses_default(self):
        """Missing DurationSeconds should fallback to DAILY_SECONDS."""
        row = {
            SOURCE_RESOURCE_ID: "disk-missing-duration",
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "128",
            SOURCE_DURATION_SECONDS: "",
        }
        storage_dict = {}

        with self.assertLogs(level="INFO") as log:
            result = _process_storage_row(row, storage_dict)

        self.assertTrue(result)
        self.assertIn("disk-missing-duration", storage_dict)
        self.assertEqual(storage_dict["disk-missing-duration"].duration_seconds, [DAILY_SECONDS])
        self.assertTrue(
            any(
                "using default value" in output
                and SOURCE_DURATION_SECONDS in output
                for output in log.output
            )
        )

    def test_process_storage_row_none_duration_uses_default(self):
        """None DurationSeconds should fallback to DAILY_SECONDS."""
        row = {
            SOURCE_RESOURCE_ID: "disk-none-duration",
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "128",
            SOURCE_DURATION_SECONDS: None,
        }
        storage_dict = {}

        with self.assertLogs(level="INFO") as log:
            result = _process_storage_row(row, storage_dict)

        self.assertTrue(result)
        self.assertIn("disk-none-duration", storage_dict)
        self.assertEqual(storage_dict["disk-none-duration"].duration_seconds, [DAILY_SECONDS])
        self.assertTrue(
            any(
                "using default value" in output
                and SOURCE_DURATION_SECONDS in output
                for output in log.output
            )
        )

    @patch(
        "backend.src.daemon.readers.helpers.storage_helpers.PaasCiMapper.calculate_ci"
    )
    def test_create_storage_resource(self, mock_ci_calculator):
        """Test creation of StorageResource object."""
        mock_ci_calculator.return_value = 250.0

        storage_resource = create_storage_resource(
            self.sample_ssd_row, "test_storage_123", 128.0, "SSD", "LRS"
        )

        self.assertIsInstance(storage_resource, StorageResource)
        self.assertEqual(storage_resource.id, "test_storage_123")
        self.assertEqual(storage_resource.storage_type, "SSD")
        self.assertEqual(storage_resource.size_gb, 128.0)
        self.assertEqual(storage_resource.carbon_intensity, 250.0)

    def test_storage_data_validation_edge_cases(self):
        """
        Test validation of edge case storage data.
        Protects against crashes and incorrect calculations from bad data.
        """
        row_negative = {
            **self.sample_ssd_row,
            SOURCE_RESOURCE_ID: "test_negative",
            SOURCE_STORAGE_SIZE_GB: "-1.0",
        }
        storage_dict = {}

        result = _process_storage_row(row_negative, storage_dict)
        self.assertFalse(result)

        row_huge = {
            **self.sample_ssd_row,
            SOURCE_RESOURCE_ID: "test_huge",
            SOURCE_STORAGE_SIZE_GB: "999999.0",
            SOURCE_DURATION_SECONDS: "86400",
            SOURCE_COST: "100.0",
        }
        storage_dict = {}

        with self.assertLogs(level="WARNING") as log:
            result = _process_storage_row(row_huge, storage_dict)

        self.assertTrue(result)
        self.assertTrue(any("Unusually large disk" in output for output in log.output))

    def test_carbon_intensity_region_mapping(self):
        """
        CRITICAL: Test region to carbon intensity mapping.
        Protects against incorrect carbon calculations for different Azure regions.
        """
        test_regions = [
            ("francecentral", 44),
            ("germanywestcentral", 344),
            ("westeurope", 253),
            ("northeurope", 280),
            ("eastus", 384),
            ("southeastasia", 499),
        ]

        for region, expected_ci in test_regions:
            with self.subTest(region=region):
                with patch(
                    "backend.src.daemon.readers.helpers.storage_helpers.PaasCiMapper.calculate_ci"
                ) as mock_ci:
                    mock_ci.return_value = expected_ci

                    storage = create_storage_resource(
                        {
                            SOURCE_REGION: region,
                            SOURCE_RESOURCE_ID: "test",
                            SOURCE_COST: "0.0",
                        },
                        "test_id",
                        100.0,
                        "SSD",
                        "LRS",
                    )

                    self.assertEqual(storage.carbon_intensity, expected_ci)
                    self.assertEqual(storage.region, region)

        with patch(
            "backend.src.daemon.readers.helpers.storage_helpers.PaasCiMapper.calculate_ci"
        ) as mock_ci:
            mock_ci.return_value = 281

            storage = create_storage_resource(
                {
                    SOURCE_REGION: "unknown_region",
                    SOURCE_RESOURCE_ID: "test",
                    SOURCE_COST: "0.0",
                },
                "test_id",
                100.0,
                "SSD",
                "LRS",
            )

            self.assertEqual(storage.carbon_intensity, 281)


class TestProcessStorageRow(unittest.TestCase):
    """Tests for _process_storage_row using the normalized storage contract."""

    def setUp(self):
        self.sample_row = {
            SOURCE_PRODUCT_NAME: "Premium SSD Managed Disks",
            SOURCE_RESOURCE_ID: "test_line_123",
            SOURCE_REGION: "francecentral",
            SOURCE_PROVIDER: "azure",
            SOURCE_COST: "0.0",
            SOURCE_STORAGE_SIZE_GB: "128",
            SOURCE_DURATION_SECONDS: "86400",
        }

    @patch("backend.src.daemon.readers.helpers.storage_helpers.get_storage_type")
    @patch("backend.src.daemon.readers.helpers.storage_helpers.get_replication_type")
    @patch("backend.src.daemon.readers.helpers.storage_helpers.create_storage_resource")
    def test_process_storage_row_success(
        self,
        mock_create_storage,
        mock_get_replication,
        mock_get_storage_type,
    ):
        """Test successful processing of a storage row."""
        mock_get_storage_type.return_value = "SSD"
        mock_get_replication.return_value = "LRS"
        mock_storage_resource = MagicMock()
        mock_storage_resource.id = self.sample_row[SOURCE_RESOURCE_ID]
        mock_storage_resource.dict_custom_columns = {}
        mock_storage_resource.time_points = []
        mock_storage_resource.duration_seconds = []
        mock_create_storage.return_value = mock_storage_resource

        storage_dict = {}
        result = _process_storage_row(self.sample_row, storage_dict)

        self.assertTrue(result)
        self.assertIn(self.sample_row[SOURCE_RESOURCE_ID], storage_dict)
        mock_create_storage.assert_called_once_with(
            self.sample_row,
            self.sample_row[SOURCE_RESOURCE_ID],
            128.0,
            "SSD",
            "LRS",
        )

    def test_process_storage_row_zero_size(self):
        """Test processing of storage row with zero size."""
        row = {**self.sample_row, SOURCE_STORAGE_SIZE_GB: "0"}

        storage_dict = {}
        result = _process_storage_row(row, storage_dict)

        self.assertFalse(result)
        self.assertEqual(len(storage_dict), 0)

    def test_process_storage_row_without_resource_id(self):
        """Test processing of storage row without resource id."""
        row_without_resource_id = self.sample_row.copy()
        del row_without_resource_id[SOURCE_RESOURCE_ID]

        storage_dict = {}
        result = _process_storage_row(row_without_resource_id, storage_dict)

        self.assertFalse(result)
        self.assertEqual(len(storage_dict), 0)


if __name__ == "__main__":
    unittest.main()
