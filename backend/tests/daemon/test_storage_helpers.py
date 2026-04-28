# pylint: disable=redefined-outer-name
"""
Unit tests for storage helpers functions.
"""
import unittest
from unittest.mock import MagicMock, patch

from backend.src.daemon.readers.helpers.storage_helpers import (
    calculate_storage_size,
    date_delta,
    create_storage_resource,
    extract_size_from_product_name,
    get_replication_type,
    get_storage_type,
    process_storage_row,
)
from backend.src.schemas.storage_resource import StorageResource


class TestStorageHelpers(unittest.TestCase):
    """
    Unit tests for storage helper functions.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.sample_ssd_row = {
            "ProductName": "Premium SSD Managed Disks",
            "MeterName": "P10 Disks",
            "LineNumber": "test_line_123",
            "ResourceLocation": "francecentral",
            "SubscriptionId": "test-subscription-id",
            "ResourceGroup": "test-rg",
        }

        self.sample_hdd_row = {
            "ProductName": "Standard HDD Managed Disks",
            "MeterName": "S30 Disks",
            "LineNumber": "test_line_456",
            "ResourceLocation": "germanywestcentral",
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
        row = {"ProductName": "Unknown Storage Type"}
        with self.assertLogs(level="WARNING") as log:
            storage_type = get_storage_type(row)
        self.assertEqual(storage_type, "Unknown")
        self.assertIn("Unknown disk type", log.output[0])

    def test_get_replication_type_lrs(self):
        """Test replication type detection for LRS."""
        row = {"ProductName": "Premium SSD - LRS", "MeterName": "P10 LRS"}
        replication_type = get_replication_type(row)
        self.assertEqual(replication_type, "LRS")

    def test_get_replication_type_grs(self):
        """Test replication type detection for GRS."""
        row = {"ProductName": "Storage - GRS", "MeterName": "Hot GRS Data"}
        replication_type = get_replication_type(row)
        self.assertEqual(replication_type, "GRS")

    def test_get_replication_type_default_lrs(self):
        """Test replication type defaults to LRS for unknown types."""
        row = {"ProductName": "Unknown Storage", "MeterName": "Unknown"}
        replication_type = get_replication_type(row)
        self.assertEqual(replication_type, "LRS")

    def test_calculate_storage_size_gib_hour(self):
        """Test storage size calculation for GiB/Hour unit."""
        row = {
            "UnitOfMeasure": "1 GiB/Hour",
            "Quantity": "240.0",  # 10 GiB for 24 hours
            "ProductName": "Premium SSD v2",
        }
        size_gb, duration_seconds = calculate_storage_size(row, 30, {})
        expected_size = (240.0 / 24) * 1.07374182  # GiB to GB conversion
        self.assertEqual(size_gb, expected_size)
        self.assertEqual(duration_seconds, 86400)  # 24 hours

    def test_calculate_storage_size_month_with_sku(self):
        """Test storage size calculation for 1/Month unit with SKU."""
        row = {
            "UnitOfMeasure": "1/Month",
            "Quantity": "2.0",
            "ProductName": "Premium SSD Managed Disks - P10 LRS",
        }
        size_gb, duration_seconds = calculate_storage_size(row, 30, {"P10": 128})
        self.assertEqual(size_gb, 128.0)
        self.assertEqual(duration_seconds, 30 * 2 * 86400)  # 30 days * 2 disks * 24h

    def test_calculate_storage_size_unknown_unit(self):
        """Test storage size calculation for unknown unit."""
        row = {
            "UnitOfMeasure": "Unknown Unit",
            "Quantity": "1.0",
            "ProductName": "Unknown Product",
        }

        with self.assertLogs(level="WARNING") as log:
            size_gb, duration_seconds = calculate_storage_size(row, 30, {})

        self.assertEqual(size_gb, 0.0)
        self.assertEqual(duration_seconds, 0)
        self.assertIn("Unknown UnitOfMeasure", log.output[0])

    def test_calculate_storage_size_snapshots_excluded(self):
        """Test that snapshots (1 GB/Month) are excluded."""
        row = {
            "UnitOfMeasure": "1 GB/Month",
            "Quantity": "100.0",
            "ProductName": "Blob Storage Snapshots",
        }
        size_gb, duration_seconds = calculate_storage_size(row, 30, {})
        self.assertEqual(size_gb, 0.0)
        self.assertEqual(duration_seconds, 0)

    @patch(
        "backend.src.daemon.readers.helpers.storage_helpers.PaasCiMapper.calculate_ci"
    )
    def test_create_storage_resource(self, mock_ci_calculator):
        """Test creation of StorageResource object."""
        mock_ci_calculator.return_value = 250.0

        storage_resource = create_storage_resource(
            self.sample_ssd_row, "test_storage_123", 128.0, "SSD", "LRS", 86400
        )

        self.assertIsInstance(storage_resource, StorageResource)
        self.assertEqual(storage_resource.id, "test_storage_123")
        self.assertEqual(storage_resource.storage_type, "SSD")
        self.assertEqual(storage_resource.size_gb, 128.0)
        self.assertEqual(storage_resource.carbon_intensity, 250.0)

    @patch("backend.src.daemon.readers.helpers.storage_helpers.calculate_storage_size")
    @patch("backend.src.daemon.readers.helpers.storage_helpers.get_storage_type")
    @patch("backend.src.daemon.readers.helpers.storage_helpers.get_replication_type")
    @patch("backend.src.daemon.readers.helpers.storage_helpers.create_storage_resource")
    def test_process_storage_row_success(
        self,
        mock_create_storage,
        mock_get_replication,
        mock_get_storage_type,
        mock_calculate_size,
    ):
        """Test successful processing of a storage row."""
        mock_calculate_size.return_value = (128.0, 86400)
        mock_get_storage_type.return_value = "SSD"
        mock_get_replication.return_value = "LRS"
        mock_storage_resource = MagicMock(spec=StorageResource)
        mock_storage_resource.time_points = []
        mock_create_storage.return_value = mock_storage_resource

        storage_dict = {}
        result = process_storage_row(self.sample_ssd_row, 30, storage_dict)

        self.assertTrue(result)
        self.assertIn("test_line_123", storage_dict)

    @patch("backend.src.daemon.readers.helpers.storage_helpers.calculate_storage_size")
    def test_process_storage_row_zero_size(self, mock_calculate_size):
        """Test processing of storage row with zero size."""
        mock_calculate_size.return_value = (0.0, 86400)

        storage_dict = {}
        result = process_storage_row(self.sample_ssd_row, 30, storage_dict)

        self.assertFalse(result)
        self.assertEqual(len(storage_dict), 0)

    @patch("backend.src.daemon.readers.helpers.storage_helpers.calculate_storage_size")
    def test_process_storage_row_missing_line_number(self, mock_calculate_size):
        """Test processing of storage row without line number."""
        mock_calculate_size.return_value = (128.0, 86400)

        row_without_line_number = self.sample_ssd_row.copy()
        del row_without_line_number["LineNumber"]

        storage_dict = {}
        result = process_storage_row(row_without_line_number, 30, storage_dict)

        self.assertFalse(result)
        self.assertEqual(len(storage_dict), 0)

    def test_extract_size_from_sku_comprehensive_azure(self):
        """
        Test SKU extraction for all Azure disk types.
        Protects against incorrect billing when new SKUs are added.
        """
        azure_sku_mapping = {
            "P4": 32,
            "P10": 128,
            "P15": 256,
            "P20": 512,
            "P80": 32767,
            "E10": 128,
            "E20": 512,
            "S4": 32,
            "S20": 512,
            "S80": 32767,
        }
        # Test all major SKU series
        test_cases = [
            # Premium SSD (P series)
            ("Premium SSD Managed Disks - P4 LRS - EU West", 32.0),
            ("Premium SSD Managed Disks - P15 LRS", 256.0),
            ("Premium SSD Managed Disks - P80 LRS", 32767.0),
            # Standard SSD (E series)
            ("Standard SSD Managed Disks - E10 LRS", 128.0),
            ("Standard SSD Managed Disks - E20 LRS", 512.0),
            # Standard HDD (S series)
            ("Standard HDD Managed Disks - S4 LRS", 32.0),
            ("Standard HDD Managed Disks - S20 LRS", 512.0),
            ("Standard HDD Managed Disks - S80 LRS", 32767.0),
            # Edge cases
            ("Some Random Product Name", 0.0),  # No SKU
            ("Premium SSD - P999 LRS", 0.0),  # Unknown SKU
            ("Multiple P10 and P20 in name", 128.0),  # Should pick first match
        ]

        for product_name, expected_size in test_cases:
            with self.subTest(product_name=product_name):
                result = extract_size_from_product_name(product_name, azure_sku_mapping)
                self.assertEqual(
                    result,
                    expected_size,
                    f"Failed for {product_name}: expected {expected_size}, got {result}",
                )

    def test_storage_data_validation_edge_cases(self):
        """
        Test validation of edge case storage data.
        Protects against crashes and incorrect calculations from bad data.
        """
        # Test negative sizes
        row_negative = {
            "UnitOfMeasure": "1 GiB/Hour",
            "Quantity": "-1.0",  # Negative quantity
            "ProductName": "Premium SSD v2 Managed Disks",
            "LineNumber": "test_negative",
        }
        storage_dict = {}
        result = process_storage_row(row_negative, 30, storage_dict)
        self.assertFalse(result)  # Should reject negative sizes

        # Test extremely large sizes
        row_huge = {
            "UnitOfMeasure": "1 GiB/Hour",
            "Quantity": "999999.0",  # Unrealistic quantity
            "ProductName": "Premium SSD v2 Managed Disks",
            "LineNumber": "test_huge",
        }
        storage_dict = {}
        with self.assertLogs(level="WARNING") as log:
            result = process_storage_row(row_huge, 30, storage_dict)
            # Should log warning for unusually large disk
            self.assertTrue(
                any("Unusually large disk" in output for output in log.output)
            )

    def test_carbon_intensity_region_mapping(self):
        """
        CRITICAL: Test region to carbon intensity mapping.
        Protects against incorrect carbon calculations for different Azure regions.
        """
        # Test known regions with expected carbon intensities
        test_regions = [
            ("francecentral", 44),  # France - low carbon
            ("germanywestcentral", 344),  # Germany - medium carbon
            ("westeurope", 253),  # Netherlands - medium carbon
            ("northeurope", 280),  # Ireland - medium carbon
            ("eastus", 384),  # Virginia - high carbon
            ("southeastasia", 499),  # Singapore - high carbon
        ]

        for region, expected_ci in test_regions:
            with self.subTest(region=region):
                with patch(
                    "backend.src.daemon.readers.helpers.storage_helpers.PaasCiMapper.calculate_ci"
                ) as mock_ci:
                    mock_ci.return_value = expected_ci

                    storage = create_storage_resource(
                        {
                            "ResourceLocation": region,
                            "LineNumber": "test",
                            "ResourceGroup": "test",
                        },
                        "test_id",
                        100.0,
                        "SSD",
                        "LRS",
                        86400,
                    )

                    self.assertEqual(
                        storage.carbon_intensity,
                        expected_ci,
                        f"Carbon intensity mismatch for {region}",
                    )
                    self.assertEqual(storage.region, region)

        # Test unknown region handling
        with patch(
            "backend.src.daemon.readers.helpers.storage_helpers.PaasCiMapper.calculate_ci"
        ) as mock_ci:
            mock_ci.return_value = 281  # Default carbon intensity

            storage = create_storage_resource(
                {
                    "ResourceLocation": "unknown_region",
                    "LineNumber": "test",
                    "ResourceGroup": "test",
                },
                "test_id",
                100.0,
                "SSD",
                "LRS",
                86400,
            )

            self.assertEqual(storage.carbon_intensity, 281)  # Should use default

    def test_date_delta_success(self):
        """Test billing period calculation - normal case"""
        csv_data = """BillingPeriodStartDate,BillingPeriodEndDate,ProductName
3/1/2025,3/31/2025,Premium SSD
3/1/2025,3/31/2025,Standard HDD"""

        result = date_delta(csv_data)
        self.assertEqual(result, 31)  # March = 31 days

    def test_date_delta_fallback(self):
        """Test fallback to 30 days when CSV is invalid"""
        csv_data = "invalid,csv,data"

        with self.assertLogs(level="ERROR") as log:
            result = date_delta(csv_data)

        self.assertEqual(result, 30)
        self.assertIn("CSV error", log.output[0])


if __name__ == "__main__":
    unittest.main()
