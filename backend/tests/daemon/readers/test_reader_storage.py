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
    HOURLY_INTERVAL_SECONDS,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.readers.reader_storage import Reader_Storage

import logging

logger = logging.getLogger(__name__)


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

        self.assertEqual(len(list_processed_resources), 1)

        resultStorageResource = list_processed_resources[0]

        # Ensure input data is not altered.
        self.assertEqual(resultStorageResource.size_gb, 32.0)
        self.assertEqual(resultStorageResource.storage_type, "SSD")
        self.assertEqual(resultStorageResource.replication_type, "LRS")
        #TODO: need to implement missing regions UTs
