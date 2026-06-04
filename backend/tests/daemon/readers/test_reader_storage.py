"""
Unit tests for the Storage Reader class in the daemon.readers module.

"""

import os
import unittest
from unittest.mock import MagicMock
from collections import Counter

from unittest.mock import patch

from backend.src.common.constants import (
    CSV_PATH,
    CSV_FILE_TEST,
    CSV_FILE_ENCODING,
    SOURCE_PROVIDER,
    HOURLY_INTERVAL_SECONDS,
    SOURCE_RESOURCE_ID,
    SOURCE_RESOURCE_GROUP,
    SOURCE_SUBSCRIPTION_ID,
    SOURCE_REGION,
    SOURCE_METER_CATEGORY,
    SOURCE_BILLING_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_METER_NAME,
    SOURCE_QUANTITY,
    SOURCE_UNIT_OF_MEASURE,
    SOURCE_DATE,
    DATE_FORMAT,
    UNKNOWN,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.readers.reader_storage import Reader_Storage

import logging

logger = logging.getLogger(__name__)


_HEADERS = ",".join([
    SOURCE_RESOURCE_ID,
    SOURCE_PROVIDER,
    SOURCE_REGION,
    SOURCE_METER_CATEGORY,
    SOURCE_BILLING_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_METER_NAME,
    SOURCE_QUANTITY,
    SOURCE_UNIT_OF_MEASURE,
    "BillingPeriodStartDate",
    "BillingPeriodEndDate",
])


def _make_row(
    resource_id: str,
    meter_category: str,
    billing_cost: str,
    product_name: str,
    meter_name: str,
    quantity: str,
    unit_of_measure: str,
    provider: str = "azure",
    region: str = "centralus",
) -> str:
    return (
        f"{resource_id},{provider},{region},{meter_category},{billing_cost},"
        f"{product_name},{meter_name},{quantity},{unit_of_measure},"
        "05/01/2024,05/31/2024"
    )


class TestReaderStorage(unittest.TestCase):
    """
    Unit test class for the CarbonDaemon class and related to storage
    calculation functionality.
    """

    def create_sample_storage(
        self,
        storage_id,
        product_name,
        storage_type,
        replication_type,
        size_gb,
        region,
        subscription,
        resource_group,
        carbon_intensity,
        time_points,
        duration_seconds,
    ) -> StorageResource:
        """
        Returns a sample storage resource dictionary.
        """
        storageResource = StorageResource(
            id=storage_id,
            name=product_name,
            storage_type=storage_type,
            replication_type=replication_type,
            size_gb=size_gb,
            region=region,
            subscription=subscription,
            resource_group=resource_group,
            carbon_intensity=carbon_intensity,
            time_points=[],
            duration_seconds=duration_seconds,
        )
        return storageResource

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()
        self.list_input_file = []
        self.list_input_file.append(os.getenv(CSV_PATH, CSV_FILE_TEST))

    @patch("backend.src.utils.ioc_util.resolve")
    def test_reader_storage_success(self, mock_ioc_util_resolve):
        """
        Test successful Storage Reader execution.
        """
        processed_storage = [
            self.create_sample_storage(
                storage_id="id",
                product_name=None,
                storage_type="SSD",
                replication_type="LRS",
                size_gb=32.0,
                region=None,
                subscription=None,
                resource_group=None,
                carbon_intensity=253.0,
                time_points=[],
                duration_seconds=HOURLY_INTERVAL_SECONDS,
            )
        ]

        reader_storage = Reader_Storage(self.mock_config)
        reader_storage.known_regions = ["australiaeast", "centralus", "eastasia", "eastus", "francecentral", "centralindia"]
        reader_storage.unknown_regions = Counter()
        reader_storage.unknown_providers = Counter()
        reader_storage.dict_log_info = {}

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.STORAGE
        mock_processor.reader = reader_storage

        logger.debug(f"Inside test reader Storage: {self}")
        for input_file in self.list_input_file:
            if os.path.exists(input_file):
                with open(
                    input_file, "r", encoding=CSV_FILE_ENCODING
                ) as file:
                    logger.info(f"Data source reading from {input_file}")
                    csv_data = file.read()

        list_processed_resources = reader_storage.read(csv_data)

        self.assertEqual(len(list_processed_resources), 6)

        resultStorageResource = list_processed_resources[0]

        # Ensure input data is not altered.
        self.assertEqual(resultStorageResource.size_gb, 32.0)
        self.assertEqual(resultStorageResource.storage_type, "SSD")
        self.assertEqual(resultStorageResource.replication_type, "LRS")
        #TODO: need to implement missing regions UTs

    @patch("backend.src.utils.ioc_util.resolve")
    def test_reader_storage_dict_log_info(self, mock_ioc_util_resolve):
        """
        Verify dict_log_info counters on a small, controlled CSV.
        """
        reader_storage = Reader_Storage(self.mock_config)
        reader_storage.known_regions = ["australiaeast", "centralus", "eastasia", "eastus", "francecentral", "centralindia"]
        reader_storage.unknown_regions = Counter()
        reader_storage.unknown_providers = Counter()

        mock_csv_data = "\n".join(
            [
                _HEADERS,
                _make_row("disk-1", "Storage", "100.0", "Premium SSD P4 LRS", "P4", "1", "1/Month"),
                _make_row("disk-2", "Storage", "50.0", "Standard HDD S4 LRS", "S4", "1", "1/Month"),
                _make_row("snapshot-1", "Storage", "10.0", "Snapshot", "Snapshot", "1", "1 GB/Month"),
                _make_row("vm-1", "Compute", "80.0", "VM", "VM", "1", "1/Hour"),
                _make_row("net-1", "Network", "20.0", "Network", "Bandwidth", "1", "1"),
            ]
        )

        reader_storage.read(mock_csv_data)

        info = reader_storage.dict_log_info
        self.assertEqual(info["total_rows"], 5)
        self.assertEqual(info["total_storage_rows"], 3)
        self.assertEqual(info["not_storage_rows"], 2)
        self.assertEqual(info["excluded_rows"], 1)
        self.assertEqual(info["disk_rows"], 2)
        self.assertEqual(info["period_days"], 31)
