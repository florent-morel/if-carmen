
"""
Unit tests for the CarbonDaemon class in the carbon_daemon module.

These tests cover the new factory-based daemon architecture including
reader/writer patterns, YAML configuration, and the CarbonDaemon orchestration.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import ConfigurationError, ComputationError
from backend.src.schemas.virtual_machine import VirtualMachine

from backend.src.daemon.carbon_daemon import (
    CarbonDaemon,
    CarbonDaemonResult,
    DefaultReaderFactory,
    DefaultWriterFactory,
    main,
)
from backend.src.common.constants import (
    CARMEN_LOGO,
    HOURLY_INTERVAL_SECONDS,
    UploadType,
)
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.schemas.storage_resource import StorageResource


class TestCarbonDaemonStorage(unittest.TestCase):
    """
    Unit test class for the CarbonDaemon class and related to storage calculation functionality.
    """

    def storage(self, storage_id, product_name, storage_type, replication_type, 
                size_gb, region, subscription, resource_group, carbon_intensity, time_points, duration_seconds) -> StorageResource:
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

        self.sample_storage = self.storage("id", None, "SSD", "LRS", 32.0,
                                           None, None, None, 253.0, [],
                                           HOURLY_INTERVAL_SECONDS)

    @patch("backend.src.daemon.carbon_daemon.register_models")
    @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
    def test_daemon_run_compute_storage_success(self, mock_ioc_util_resolve, mock_register_models):
        """
        Test successful daemon execution with mocked reader, writer, and carbon service.
        """
        mock_reader = MagicMock()
        mock_reader.read_files.return_value = self.sample_storage.copy()

        mock_writer = MagicMock()

        mock_carbon_service = MagicMock()
        processed_storage = [
            self.storage("id", None, "SSD", "LRS", 32.0,
                        None, None, None, 253.0, [],
                        HOURLY_INTERVAL_SECONDS)
        ]
        mock_carbon_service.run_engine.return_value = processed_storage

        mock_reader_factory = MagicMock()
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()
        mock_writer_factory.create_writer.return_value = mock_writer

        mock_ioc_util_resolve.return_value = mock_carbon_service

        daemon = CarbonDaemon(
            self.mock_config,
            reader_factory=mock_reader_factory,
            writer_factory=mock_writer_factory,
        )

        carbonDaemonResult = daemon._process_carbon_calculations_storage(processed_storage)

        # self.assertIsInstance(result, list[StorageResource])
        # self.assertTrue(result.success)
        # self.assertEqual(result.vm_count, 0)  # No vm provided
        # self.assertGreater(result.execution_time, 0)
        # self.assertEqual(result.error_message, "")

        listStorageResourceResult = carbonDaemonResult.list_processed_resources
        self.assertEqual(len(listStorageResourceResult), 1)

        resultStorageResource = listStorageResourceResult[0]
        # Ensure input data is not altered.
        self.assertEqual(resultStorageResource.size_gb, 32.0)
        self.assertEqual(resultStorageResource.storage_type, "SSD")
        self.assertEqual(resultStorageResource.replication_type, "LRS")

        # Validate computation calculation on single resource
        self.assertEqual(resultStorageResource.storage_energy, 32.0)
        self.assertEqual(resultStorageResource.storage_embodied, 32.0)
        self.assertEqual(resultStorageResource.carbon_emitted, 32.0)

        # Validate computation calculation on overall result
        self.assertEqual(carbonDaemonResult.total_storage_energy, 32.0)
        self.assertEqual(carbonDaemonResult.total_storage_embodied, 32.0)
        self.assertEqual(carbonDaemonResult.total_carbon_emitted, 32.0)
        # mock_register_models.assert_called_once()
        # mock_reader_factory.create_reader.assert_called_once_with(self.mock_config)
        # mock_reader.read_files.assert_called_once()
        # mock_ioc_util_resolve.assert_called_once_with(CarbonService, "IFStorage", HOURLY_INTERVAL_SECONDS)
        # mock_carbon_service.run_engine.assert_called_once_with(self.sample_vms)
        # mock_writer_factory.create_writer.assert_called_once_with(
        #     self.mock_config, processed_storage
        # )
        # mock_writer.upload_compute_report.assert_called_once()

#     @patch("backend.src.daemon.carbon_daemon.register_models")
#     def test_daemon_run_no_vms_found(self, mock_register_models):
#         """
#         Test daemon execution when no VMs are found in data source.
#         """
#         mock_reader = MagicMock()
#         mock_reader.read_files.return_value = []
# 
#         mock_reader_factory = MagicMock()
#         mock_reader_factory.create_reader.return_value = mock_reader
# 
#         mock_writer_factory = MagicMock()
# 
#         daemon = CarbonDaemon(
#             self.mock_config,
#             reader_factory=mock_reader_factory,
#             writer_factory=mock_writer_factory,
#         )
# 
#         result = daemon.run()
# 
#         self.assertIsInstance(result, CarbonDaemonResult)
#         self.assertFalse(result.success)
#         self.assertEqual(result.vm_count, 0)
#         self.assertIn("No virtual machines found", result.error_message)
# 
#     @patch("backend.src.daemon.carbon_daemon.register_models")
#     def test_daemon_run_reader_exception(self, mock_register_models):
#         """
#         Test daemon execution when reader raises an exception.
#         """
#         mock_reader = MagicMock()
#         mock_reader.read_files.side_effect = Exception("Reader failed")
# 
#         mock_reader_factory = MagicMock()
#         mock_reader_factory.create_reader.return_value = mock_reader
# 
#         mock_writer_factory = MagicMock()
# 
#         daemon = CarbonDaemon(
#             self.mock_config,
#             reader_factory=mock_reader_factory,
#             writer_factory=mock_writer_factory,
#         )
# 
#         result = daemon.run()
# 
#         self.assertIsInstance(result, CarbonDaemonResult)
#         self.assertFalse(result.success)
#         self.assertIn("unexpected error during daemon execution", result.error_message)
#         self.assertIn("Reader failed", result.error_message)
# 
#     @patch("backend.src.daemon.carbon_daemon.register_models")
#     @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
#     def test_daemon_run_carbon_service_exception(
#         self, mock_ioc_util_resolve, mock_register_models
#     ):
#         """
#         Test daemon execution when carbon service raises an exception.
#         """
#         mock_reader = MagicMock()
#         mock_reader.read_files.return_value = self.sample_vms.copy()
# 
#         mock_carbon_service = MagicMock()
#         mock_carbon_service.run_engine.side_effect = Exception("Carbon service failed")
# 
#         mock_reader_factory = MagicMock()
#         mock_reader_factory.create_reader.return_value = mock_reader
# 
#         mock_writer_factory = MagicMock()
# 
#         mock_ioc_util_resolve.return_value = mock_carbon_service
# 
#         daemon = CarbonDaemon(
#             self.mock_config,
#             reader_factory=mock_reader_factory,
#             writer_factory=mock_writer_factory,
#         )
# 
#         result = daemon.run()
# 
#         self.assertIsInstance(result, CarbonDaemonResult)
#         self.assertFalse(result.success)
#         self.assertIn("unexpected error during daemon execution", result.error_message)
#         self.assertIn("Carbon service failed", result.error_message)
# 
#     @patch("backend.src.daemon.carbon_daemon.register_models")
#     @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
#     def test_daemon_run_known_exception(
#         self, mock_ioc_util_resolve, mock_register_models
#     ):
#         """
#         Test daemon execution when a ConfigurationError is raised.
#         """
#         mock_reader = MagicMock()
#         mock_reader.read_files.side_effect = ConfigurationError(
#             ErrorCode.CONFIG_INVALID_FILE, details="Known error occurred"
#         )
# 
#         mock_reader_factory = MagicMock()
#         mock_reader_factory.create_reader.return_value = mock_reader
# 
#         mock_writer_factory = MagicMock()
# 
#         daemon = CarbonDaemon(
#             self.mock_config,
#             reader_factory=mock_reader_factory,
#             writer_factory=mock_writer_factory,
#         )
# 
#         result = daemon.run()
# 
#         self.assertIsInstance(result, CarbonDaemonResult)
#         self.assertFalse(result.success)
#         self.assertIn(
#             "known error during daemon execution", result.error_message.lower()
#         )
# 
#     @patch(
#         "backend.src.daemon.readers.compute.azure_compute_reader.initialize_azure_client"
#     )
#     def test_default_reader_factory_azure(self, mock_azure_client):
#         """
#         Test DefaultReaderFactory creates Azure reader for azure source type.
#         """
#         mock_azure_client.return_value = MagicMock()
# 
#         factory = DefaultReaderFactory()
#         config = MagicMock()
#         config.source = MagicMock()
#         config.source.type = "azure"
# 
#         reader = factory.create_reader(config)
# 
#         self.assertIsNotNone(reader)
# 
#     def test_default_reader_factory_unsupported(self):
#         """
#         Test DefaultReaderFactory raises ValueError for unsupported source type.
#         """
#         factory = DefaultReaderFactory()
#         config = MagicMock()
#         config.source = MagicMock()
#         config.source.type = "unsupported"
# 
#         with self.assertRaises(ValueError) as context:
#             factory.create_reader(config)
# 
#         self.assertIn("unsupported source type", str(context.exception))
# 
#     @patch(
#         "backend.src.daemon.writers.compute.azure_compute_writer.initialize_azure_client"
#     )
#     def test_default_writer_factory_azure(self, mock_azure_client):
#         """
#         Test DefaultWriterFactory creates Azure writer for azure upload type.
#         """
#         mock_azure_client.return_value = MagicMock()
# 
#         factory = DefaultWriterFactory()
#         config = MagicMock()
#         config.upload = MagicMock()
#         config.upload.type = "azure"
# 
#         writer = factory.create_writer(config, self.sample_vms)
# 
#         self.assertIsNotNone(writer)
# 
#     def test_default_writer_factory_local(self):
#         """
#         Test DefaultWriterFactory creates Local writer for local upload type.
#         """
#         factory = DefaultWriterFactory()
#         config = MagicMock()
#         config.upload = MagicMock()
#         config.upload.type = "local"
# 
#         writer = factory.create_writer(config, self.sample_vms)
# 
#         self.assertIsNotNone(writer)
# 
#     def test_default_writer_factory_unsupported(self):
#         """
#         Test DefaultWriterFactory raises ValueError for unsupported upload type.
#         """
#         factory = DefaultWriterFactory()
#         config = MagicMock()
#         config.upload = MagicMock()
#         config.upload.type = "unsupported"
# 
#         with self.assertRaises(ValueError) as context:
#             factory.create_writer(config, self.sample_vms)
# 
#         self.assertIn("unsupported upload type", str(context.exception))


if __name__ == "__main__":
    unittest.main()
