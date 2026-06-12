"""
Unit tests for the Storage Reader class in the daemon.readers module.
"""

import unittest
from collections import Counter
from unittest.mock import MagicMock

from backend.src.common.constants import (
    SOURCE_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_PROVIDER,
    SOURCE_REGION,
    SOURCE_RESOURCE_ID,
    SOURCE_RESOURCE_TYPE,
    SOURCE_RESOURCE_TYPE_STORAGE,
    SOURCE_STORAGE_DURATION_SECONDS,
    SOURCE_STORAGE_SIZE_GB,
)
from backend.src.daemon.readers.reader_storage import Reader_Storage


_HEADERS = ",".join(
    [
        SOURCE_RESOURCE_ID,
        SOURCE_PROVIDER,
        SOURCE_REGION,
        SOURCE_RESOURCE_TYPE,
        SOURCE_COST,
        SOURCE_PRODUCT_NAME,
        SOURCE_STORAGE_SIZE_GB,
        SOURCE_STORAGE_DURATION_SECONDS,
    ]
)


def _make_row(
    resource_id: str,
    resource_type: str,
    cost: str,
    product_name: str,
    storage_size_gb: str,
    storage_duration_seconds: str,
    provider: str = "azure",
    region: str = "centralus",
) -> str:
    return (
        f"{resource_id},{provider},{region},{resource_type},{cost},"
        f"{product_name},{storage_size_gb},{storage_duration_seconds}"
    )


class TestReaderStorage(unittest.TestCase):
    """Unit tests for Reader_Storage."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()
        self.mock_config.source.input_path = "."

    def _make_reader(self) -> Reader_Storage:
        reader_storage = Reader_Storage(self.mock_config)
        reader_storage.known_regions = {
            "australiaeast",
            "centralindia",
            "centralus",
            "eastasia",
            "eastus",
            "francecentral",
        }
        reader_storage.unknown_regions = Counter()
        reader_storage.unknown_providers = Counter()
        reader_storage.dict_log_info = {}
        return reader_storage

    def test_reader_storage_success(self):
        """Reader_Storage should build storage resources from normalized inputs."""
        reader_storage = self._make_reader()

        mock_csv_data = "\n".join(
            [
                _HEADERS,
                _make_row("disk-1", SOURCE_RESOURCE_TYPE_STORAGE, "100.0", "Premium SSD P4 LRS", "32", "86400"),
                _make_row("disk-2", SOURCE_RESOURCE_TYPE_STORAGE, "50.0", "Standard HDD S4 LRS", "64", "172800"),
                _make_row("vm-1", "Compute", "80.0", "VM", "", ""),
            ]
        )

        list_processed_resources = reader_storage.read(mock_csv_data)

        self.assertEqual(len(list_processed_resources), 2)

        first_resource = list_processed_resources[0]
        second_resource = list_processed_resources[1]

        self.assertEqual(first_resource.id, "disk-1")
        self.assertEqual(first_resource.size_gb, 32.0)
        self.assertEqual(first_resource.storage_type, "SSD")
        self.assertEqual(first_resource.replication_type, "LRS")
        self.assertEqual(first_resource.duration_seconds, 86400)

        self.assertEqual(second_resource.id, "disk-2")
        self.assertEqual(second_resource.size_gb, 64.0)
        self.assertEqual(second_resource.storage_type, "HDD")
        self.assertEqual(second_resource.duration_seconds, 172800)

    def test_reader_storage_dict_log_info(self):
        """Verify dict_log_info counters on a small, controlled CSV."""
        reader_storage = self._make_reader()

        mock_csv_data = "\n".join(
            [
                _HEADERS,
                _make_row("disk-1", SOURCE_RESOURCE_TYPE_STORAGE, "100.0", "Premium SSD P4 LRS", "32", "86400"),
                _make_row("disk-2", SOURCE_RESOURCE_TYPE_STORAGE, "50.0", "Standard HDD S4 LRS", "64", "172800"),
                _make_row("disk-invalid", SOURCE_RESOURCE_TYPE_STORAGE, "10.0", "Snapshot", "64", ""),
                _make_row("vm-1", "Compute", "80.0", "VM", "", ""),
                _make_row("net-1", "Network", "20.0", "Network", "", ""),
            ]
        )

        reader_storage.read(mock_csv_data)

        info = reader_storage.dict_log_info
        self.assertEqual(info["total_rows"], 5)
        self.assertEqual(info["total_storage_rows"], 3)
        self.assertEqual(info["not_storage_rows"], 2)
        self.assertEqual(info["excluded_rows"], 1)
        self.assertEqual(info["disk_rows"], 2)


if __name__ == "__main__":
    unittest.main()
