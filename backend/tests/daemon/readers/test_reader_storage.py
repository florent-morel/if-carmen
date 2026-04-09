
"""
Unit tests for the Storage Reader class in the daemon.readers module.

"""

import unittest
from unittest.mock import MagicMock

from unittest.mock import patch, AsyncMock
from backend.src.daemon.carbon_daemon_orchestrator import CarbonDaemonOrchestrator
from backend.src.daemon.processors.processor_storage import Processor_Storage

from backend.src.common.constants import (
    HOURLY_INTERVAL_SECONDS,
    DAILY_SECONDS,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.resource import Resource, ResourceType
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
        self.mock_config.source = MagicMock()
        self.mock_config.upload = MagicMock()

    @patch("backend.src.utils.ioc_util.resolve")
    # @patch("backend.src.daemon.carbon_daemon.register_models")
    # def test_daemon_run_compute_storage_success(self,
    # mock_ioc_util_resolve, mock_register_models):
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

        reader_storage = Reader_Storage()

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.STORAGE
        mock_processor.reader = reader_storage
        # reader_storage.local_storage_file = 

        # self.assertIsNotNone(resultStorage)
        mock_processor.read()

        listStorageResourceResult = resultStorage.list_processed_resources

        self.assertEqual(len(listStorageResourceResult), 1)

        resultStorageResource = listStorageResourceResult[0]

        # Ensure input data is not altered.
        self.assertEqual(resultStorageResource.size_gb, 32.0)
        self.assertEqual(resultStorageResource.storage_type, "SSD")
        self.assertEqual(resultStorageResource.replication_type, "LRS")
