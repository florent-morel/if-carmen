"""
Unit tests for the CarbonDaemonOrchestrator class - Storage resources.

These tests cover the orchestrator-based daemon architecture for storage
resources, including processor patterns and CarbonDaemonOrchestrator execution.
"""

import unittest
from unittest.mock import MagicMock

from unittest.mock import patch, AsyncMock
from backend.src.daemon.carbon_daemon_orchestrator import CarbonDaemonOrchestrator
from backend.src.daemon.processors.processor_storage import Processor_Storage
from backend.src.common.carmen_exception import CarmenException, DataFetchError
from backend.src.common.errors import ERRORS, ErrorCode

from backend.src.common.constants import (
    HOURLY_INTERVAL_SECONDS,
    DAILY_SECONDS,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.daemon.runners.runner_storage import Runner_Storage
from backend.src.services.carbon_service.impact_framework.service.if_storage_service import (
    IFStorageService,
)

from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
import logging
from backend.src.core.yaml_config_loader import config

logger = logging.getLogger(__name__)


class TestCarbonDaemonOrchestratorStorage(unittest.TestCase):
    """
    Unit test class for the CarbonDaemonOrchestrator storage resource functionality.
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
            provider="azure",
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
        self.mock_config.source.input_path = "etc/sample_data/test_data/storage_test.csv"
        logger.warning(f"input_path: {self.mock_config.source.input_path}")

    @patch("backend.src.utils.ioc_util.resolve")
    # @patch("backend.src.daemon.carbon_daemon.register_models")
    # def test_daemon_run_compute_storage_success(self,
    # mock_ioc_util_resolve, mock_register_models):
    def test_daemon_runner_storage_success(self, mock_ioc_util_resolve):
        """
        Test successful daemon execution with mocked reader, writer, and
        carbon service.
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

        mock_ioc_util_resolve.return_value = IFStorageService(DAILY_SECONDS)

        runner_storage = Runner_Storage()
        resource_type_result = runner_storage.run(processed_storage.copy())

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.STORAGE
        mock_processor.read.return_value = processed_storage.copy()
        mock_processor.run.return_value = resource_type_result

        logger.info(f"Mock processor: {mock_processor}")
        logger.info(f"Mock config: {self.mock_config}")
        logger.warning(f"config input path: {config.carmen_daemon.input_path}")
        logger.warning(f"config output path: {config.carmen_daemon.output_path}")

        self.mock_config.output.output_path = config.carmen_daemon.output_path

        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])

        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()
        logger.info(f"Result: {carbonDaemonResult.dict_resource_result}")

        resultStorage = carbonDaemonResult.dict_resource_result[ResourceType.STORAGE]
        self.assertIsNotNone(resultStorage)

        listStorageResourceResult = resultStorage.list_processed_resources
        self.assertEqual(len(listStorageResourceResult), 1)

        resultStorageResource = listStorageResourceResult[0]

        # Ensure input data is not altered.
        self.assertEqual(resultStorageResource.size_gb, 32.0)
        self.assertEqual(resultStorageResource.storage_type, "SSD")
        self.assertEqual(resultStorageResource.replication_type, "LRS")

        # Validate computation calculation on single resource
        self.assertEqual(resultStorage.total_energy_consumed, 0.0001)
        self.assertEqual(resultStorage.total_carbon_operational, 0.0291)
        self.assertEqual(resultStorage.total_carbon_embodied, 0.4381)
        self.assertEqual(resultStorage.total_carbon_emitted, 0.4672)

        # Validate computation calculation on overall result
        self.assertEqual(carbonDaemonResult.total_energy_consumed, 0.0001)
        self.assertEqual(carbonDaemonResult.total_carbon_operational, 0.0291)
        self.assertEqual(carbonDaemonResult.total_carbon_embodied, 0.4381)
        self.assertEqual(carbonDaemonResult.total_carbon_emitted, 0.4672)
        # mock_register_models.assert_called_once()
        # mock_reader_factory.create_reader.assert_called_once_with(self.mock_config)
        # mock_reader.read.assert_called_once()
        # mock_ioc_util_resolve.assert_called_once_with(CarbonService, "IFStorage", HOURLY_INTERVAL_SECONDS)
        # mock_carbon_service.run_engine.assert_called_once_with(self.sample_vms)
        # mock_writer_factory.create_writer.assert_called_once_with(
        #     self.mock_config, processed_storage
        # )

    #     @patch("backend.src.daemon.carbon_daemon.register_models")
    #     def test_daemon_run_no_vms_found(self, mock_register_models):
    #         """
    #         Test daemon execution when no VMs are found in data source.
    #         """
    #         mock_reader = MagicMock()
    #         mock_reader.read.return_value = []
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

    #     @patch("backend.src.daemon.carbon_daemon.register_models")

    @patch("backend.src.daemon.readers.reader_storage.Reader_Storage.read")
    @patch("backend.src.daemon.carbon_daemon_orchestrator.CarbonDaemonOrchestrator.write_report")
    @patch("backend.src.utils.ioc_util.resolve")
    # def test_daemon_run_reader_exception(self, mock_register_models):
    def test_daemon_reader_storage_exception(self, mock_reader, mock_write_report, mock_ioc_util_resolve):
        """
        Test daemon execution when reader raises an exception.
        """
        mock_reader = MagicMock()
        mock_reader.read.side_effect = CarmenException(ErrorCode.UNKNOWN_ERROR, "Reader failed")

        mock_ioc_util_resolve.return_value = IFStorageService(DAILY_SECONDS)

        mock_carbon_service = MagicMock()
        mock_ioc_util_resolve.return_value = mock_carbon_service

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.STORAGE
        mock_processor.read.side_effect = CarmenException(ErrorCode.UNKNOWN_ERROR, "Reader failed")
        mock_processor.run.return_value = None

        logger.info(f"Mock processor: {mock_processor}")

        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])
        mock_write_report.return_value = None

        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        logger.info(f"Carbon Daemon Result: {carbonDaemonResult}")

        # resultStorage = carbonDaemonResult.dict_resource_result[ResourceType.STORAGE]
        # self.assertIsNone(carbonDaemonResult.dict_resource_result[ResourceType.STORAGE])

        # self.assertIsInstance(resultStorage, ResourceTypeResult)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIsNotNone(carbonDaemonResult.list_exceptions)
        logger.info(f"list_exceptions: {carbonDaemonResult.list_exceptions}")

        for exception in carbonDaemonResult.list_exceptions:
            logger.info(f"Exception: {exception.error_code}, \n details: {exception.formatted_string}")
            self.assertIn(
                "Unexpected error reading file", exception.details
            )
            self.assertIn("Reader failed", exception.details)


#     @patch("backend.src.daemon.carbon_daemon.register_models")
#     @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
#     def test_daemon_run_carbon_service_exception(
#         self, mock_ioc_util_resolve, mock_register_models
#     ):
#         """
#         Test daemon execution when carbon service raises an exception.
#         """
#         mock_reader = MagicMock()
#         mock_reader.read.return_value = self.sample_vms.copy()
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
#         self.assertIn("Unexpected error during daemon execution", result.error_message)
#         self.assertIn("Carbon service failed", result.error_message)
#
#     @patch("backend.src.daemon.carbon_daemon.register_models")
#     @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
#     def test_daemon_run_carmen_exception(
#         self, mock_ioc_util_resolve, mock_register_models
#     ):
#         """
#         Test daemon execution when a ConfigurationError is raised.
#         """
#         mock_reader = MagicMock()
#         mock_reader.read.side_effect = ConfigurationError(
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
#


if __name__ == "__main__":
    unittest.main()
