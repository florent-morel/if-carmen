"""
Unit tests for the CarbonDaemon class in the carbon_daemon module.

These tests cover the new factory-based daemon architecture including
reader/writer patterns, YAML configuration, and the CarbonDaemon orchestration.
"""

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
from backend.src.services.carbon_service.carbon_service import CarbonService


class TestCarbonDaemon(unittest.TestCase):
    """
    Unit test class for the CarbonDaemon class and related functionality.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()
        self.mock_config.source = MagicMock()
        self.mock_config.source.type = "azure"
        self.mock_config.upload = MagicMock()
        self.mock_config.upload.type = "local"
        self.sample_vms = [
            VirtualMachine(id="vm1", name="test-vm-1"),
            VirtualMachine(id="vm2", name="test-vm-2"),
        ]

    @patch("backend.src.daemon.carbon_daemon.register_models")
    @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
    def test_daemon_run_compute_vms_success(self, mock_ioc_util_resolve, mock_register_models):
        """
        Test successful daemon execution with mocked reader, writer, and carbon service.
        """
        mock_reader = MagicMock()
        mock_reader.read_files.return_value = self.sample_vms.copy()

        mock_writer = MagicMock()

        mock_carbon_service = MagicMock()
        processed_vms = [
            VirtualMachine(id="vm1", name="test-vm-1", total_carbon_emitted=100.0),
            VirtualMachine(id="vm2", name="test-vm-2", total_carbon_emitted=150.0),
        ]
        mock_carbon_service.run_engine.return_value = processed_vms

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

        result = daemon.run()

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertTrue(result.success)
        self.assertEqual(result.vm_count, 2)
        self.assertGreater(result.execution_time, 0)
        self.assertEqual(result.error_message, "")

        mock_register_models.assert_called_once()
        mock_reader_factory.create_reader.assert_called_once_with(self.mock_config)
        mock_reader.read_files.assert_called_once()
        mock_ioc_util_resolve.assert_called_once_with(CarbonService, "IFVm", 3600)
        mock_carbon_service.run_engine.assert_called_once_with(self.sample_vms)
        mock_writer_factory.create_writer.assert_called_once_with(
            self.mock_config, processed_vms
        )
        mock_writer.upload_compute_report.assert_called_once()

    @patch("backend.src.daemon.carbon_daemon.register_models")
    def test_daemon_run_no_vms_found(self, mock_register_models):
        """
        Test daemon execution when no VMs are found in data source.
        """
        mock_reader = MagicMock()
        mock_reader.read_files.return_value = []

        mock_reader_factory = MagicMock()
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()

        daemon = CarbonDaemon(
            self.mock_config,
            reader_factory=mock_reader_factory,
            writer_factory=mock_writer_factory,
        )

        result = daemon.run()

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertFalse(result.success)
        self.assertEqual(result.vm_count, 0)
        self.assertIn("No virtual machines found", result.error_message)

    @patch("backend.src.daemon.carbon_daemon.register_models")
    def test_daemon_run_reader_exception(self, mock_register_models):
        """
        Test daemon execution when reader raises an exception.
        """
        mock_reader = MagicMock()
        mock_reader.read_files.side_effect = Exception("Reader failed")

        mock_reader_factory = MagicMock()
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()

        daemon = CarbonDaemon(
            self.mock_config,
            reader_factory=mock_reader_factory,
            writer_factory=mock_writer_factory,
        )

        result = daemon.run()

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertFalse(result.success)
        self.assertIn("unexpected error during daemon execution", result.error_message)
        self.assertIn("Reader failed", result.error_message)

    @patch("backend.src.daemon.carbon_daemon.register_models")
    @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
    def test_daemon_run_carbon_service_exception(
        self, mock_ioc_util_resolve, mock_register_models
    ):
        """
        Test daemon execution when carbon service raises an exception.
        """
        mock_reader = MagicMock()
        mock_reader.read_files.return_value = self.sample_vms.copy()

        mock_carbon_service = MagicMock()
        mock_carbon_service.run_engine.side_effect = Exception("Carbon service failed")

        mock_reader_factory = MagicMock()
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()

        mock_ioc_util_resolve.return_value = mock_carbon_service

        daemon = CarbonDaemon(
            self.mock_config,
            reader_factory=mock_reader_factory,
            writer_factory=mock_writer_factory,
        )

        result = daemon.run()

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertFalse(result.success)
        self.assertIn("unexpected error during daemon execution", result.error_message)
        self.assertIn("Carbon service failed", result.error_message)

    @patch("backend.src.daemon.carbon_daemon.register_models")
    @patch("backend.src.daemon.carbon_daemon.ioc_util.resolve")
    def test_daemon_run_known_exception(
        self, mock_ioc_util_resolve, mock_register_models
    ):
        """
        Test daemon execution when a ConfigurationError is raised.
        """
        mock_reader = MagicMock()
        mock_reader.read_files.side_effect = ConfigurationError(
            ErrorCode.CONFIG_INVALID_FILE, details="Known error occurred"
        )

        mock_reader_factory = MagicMock()
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()

        daemon = CarbonDaemon(
            self.mock_config,
            reader_factory=mock_reader_factory,
            writer_factory=mock_writer_factory,
        )

        result = daemon.run()

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertFalse(result.success)
        self.assertIn(
            "known error during daemon execution", result.error_message.lower()
        )

    @patch(
        "backend.src.daemon.readers.compute.azure_compute_reader.initialize_azure_client"
    )
    def test_default_reader_factory_azure(self, mock_azure_client):
        """
        Test DefaultReaderFactory creates Azure reader for azure source type.
        """
        mock_azure_client.return_value = MagicMock()

        factory = DefaultReaderFactory()
        config = MagicMock()
        config.source = MagicMock()
        config.source.type = "azure"

        reader = factory.create_reader(config)

        self.assertIsNotNone(reader)

    def test_default_reader_factory_unsupported(self):
        """
        Test DefaultReaderFactory raises ValueError for unsupported source type.
        """
        factory = DefaultReaderFactory()
        config = MagicMock()
        config.source = MagicMock()
        config.source.type = "unsupported"

        with self.assertRaises(ValueError) as context:
            factory.create_reader(config)

        self.assertIn("unsupported source type", str(context.exception))

    @patch(
        "backend.src.daemon.writers.compute.azure_compute_writer.initialize_azure_client"
    )
    def test_default_writer_factory_azure(self, mock_azure_client):
        """
        Test DefaultWriterFactory creates Azure writer for azure upload type.
        """
        mock_azure_client.return_value = MagicMock()

        factory = DefaultWriterFactory()
        config = MagicMock()
        config.upload = MagicMock()
        config.upload.type = "azure"

        writer = factory.create_writer(config, self.sample_vms)

        self.assertIsNotNone(writer)

    def test_default_writer_factory_local(self):
        """
        Test DefaultWriterFactory creates Local writer for local upload type.
        """
        factory = DefaultWriterFactory()
        config = MagicMock()
        config.upload = MagicMock()
        config.upload.type = "local"

        writer = factory.create_writer(config, self.sample_vms)

        self.assertIsNotNone(writer)

    def test_default_writer_factory_unsupported(self):
        """
        Test DefaultWriterFactory raises ValueError for unsupported upload type.
        """
        factory = DefaultWriterFactory()
        config = MagicMock()
        config.upload = MagicMock()
        config.upload.type = "unsupported"

        with self.assertRaises(ValueError) as context:
            factory.create_writer(config, self.sample_vms)

        self.assertIn("unsupported upload type", str(context.exception))


class TestMainFunction(unittest.TestCase):
    """
    Unit test class for the main function in the carbon_daemon module.
    """

    @patch("backend.src.daemon.carbon_daemon.config")
    @patch("backend.src.daemon.carbon_daemon.CarbonDaemon")
    def test_main_success(self, mock_carbon_daemon_class, mock_config):
        """
        Test successful execution of main function.
        """
        mock_daemon_config = MagicMock()
        mock_config.carmen_daemon = mock_daemon_config

        mock_daemon_instance = MagicMock()
        mock_result = CarbonDaemonResult(success=True, vm_count=5, execution_time=10.5)
        mock_daemon_instance.run.return_value = mock_result
        mock_carbon_daemon_class.return_value = mock_daemon_instance

        with self.assertLogs(level="INFO") as log:
            main()

        mock_carbon_daemon_class.assert_called_once_with(mock_daemon_config)
        mock_daemon_instance.run.assert_called_once()

        self.assertIn("daemon execution completed successfully", log.output[-1])

    @patch("backend.src.daemon.carbon_daemon.config")
    @patch("backend.src.daemon.carbon_daemon.CarbonDaemon")
    def test_main_daemon_failure(self, mock_carbon_daemon_class, mock_config):
        """
        Test main function when daemon execution fails.
        """
        mock_daemon_config = MagicMock()
        mock_config.carmen_daemon = mock_daemon_config

        mock_daemon_instance = MagicMock()
        mock_result = CarbonDaemonResult(
            success=False, execution_time=5.0, error_message="Test failure"
        )
        mock_daemon_instance.run.return_value = mock_result
        mock_carbon_daemon_class.return_value = mock_daemon_instance

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(SystemExit) as context:
                main()

        self.assertEqual(context.exception.code, 1)

        self.assertIn("daemon execution failed: Test failure", log.output[-1])

    @patch("backend.src.daemon.carbon_daemon.config")
    @patch("backend.src.daemon.carbon_daemon.CarbonDaemon")
    def test_main_critical_exception(self, mock_carbon_daemon_class, mock_config):
        """
        Test main function when a critical exception occurs during daemon creation.
        """
        mock_daemon_config = MagicMock()
        mock_config.carmen_daemon = mock_daemon_config

        mock_carbon_daemon_class.side_effect = Exception("Critical error")

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(SystemExit) as context:
                main()

        self.assertEqual(context.exception.code, 1)

        self.assertIn("critical error in daemon main: Critical error", log.output[-1])


if __name__ == "__main__":
    unittest.main()
