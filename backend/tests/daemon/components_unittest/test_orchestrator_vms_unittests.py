"""
Unit tests for the CarbonDaemonOrchestrator class.

These tests cover the orchestrator-based daemon architecture including
processor patterns, YAML configuration, and the CarbonDaemonOrchestrator execution.
"""

import unittest
from unittest.mock import patch, MagicMock

from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import ConfigurationError, ComputationError
from backend.src.schemas.virtual_machine import VirtualMachine

from backend.src.services.carbon_service.carbon_service import CarbonService

from backend.src.daemon.carbon_daemon_orchestrator import (
    CarbonDaemonOrchestrator,
    CarbonDaemonResult,
)
from backend.src.daemon.carbon_daemon_result import ResourceTypeResult
from backend.src.daemon.processors.processor_compute import Processor_Compute
from backend.src.daemon.runners.runner_compute import Runner_Compute
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.services.carbon_service.impact_framework.service.if_vm_service import (
    IFVMService,
)
from backend.src.common.constants import (
    SAMPLING_RATE_IN_SECONDS,
    DAILY_SECONDS,
)

import logging

logger = logging.getLogger(__name__)


class TestCarbonDaemonOrchestratorComponents(unittest.TestCase):
    """
    Unit test class for the CarbonDaemonOrchestrator and related components.
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

    @patch("backend.src.daemon.carbon_daemon_orchestrator.register_models")
    # @patch("backend.src.daemon.readers.helpers.carbon_daemon.ioc_util.resolve")
    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_runner_compute_success(
        self, mock_ioc_util_resolve, mock_register_models
    ):
        """
        Test successful Orchestrator execution with mocked reader, writer, and carbon service.
        """
        # Mock carbon service to return a successful result
        mock_ioc_util_resolve.return_value = IFVMService(SAMPLING_RATE_IN_SECONDS)

        # Execute runner on sample VMs
        runner_compute = Runner_Compute()
        resource_type_result = runner_compute.run(self.sample_vms.copy())

        # Mock processor to return the generated resource daemon result
        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = self.sample_vms.copy()
        mock_processor.run.return_value = resource_type_result

        # Orchestrate the daemon with the mocked processor
        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])
        result = orchestrator.orchestrate_carbon_daemon()

        # Validate the results
        resultResource = result.dict_resource_result[ResourceType.VIRTUAL_MACHINE]
        self.assertIsNotNone(resultResource)

        listResourceResult = resultResource.list_processed_resources
        self.assertEqual(len(listResourceResult), 2)

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertTrue(result.success)
        self.assertGreater(result.execution_time, 0)
        self.assertEqual(result.error_message, "")

        # Validate that the mocks were called as expected by the Orchestrator
        mock_register_models.assert_called_once()
        mock_processor.read.assert_called_once()
        mock_ioc_util_resolve.assert_called_once_with(CarbonService, "IFVm", 3600)

    @patch("backend.src.daemon.carbon_daemon_orchestrator.register_models")
    def test_orchestrator_no_vms_found(self, _mock_register_models):
        """
        Test orchestrator execution when no VMs are found in data source.
        """
        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = []

        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])
        result = orchestrator.orchestrate_carbon_daemon()

        # read() was called; run() was never reached because the orchestrator short-circuits
        mock_processor.read.assert_called_once()
        mock_processor.run.assert_not_called()

        # Orchestrator fails at the read stage
        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertFalse(result.success)
        self.assertIn("No resources found for VirtualMachine", result.error_message)

    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_reader_compute_exception(self, mock_ioc_util_resolve):
        """
        Test daemon execution when reader raises an exception.
        """
        mock_reader = MagicMock()
        mock_reader.read.side_effect = Exception("Reader failed")

        mock_ioc_util_resolve.return_value = IFVMService(DAILY_SECONDS)

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.side_effect = Exception("Reader failed")

        logger.info(f"Mock processor: {mock_processor}")

        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])

        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIn(
            "unexpected error during daemon execution", carbonDaemonResult.error_message
        )
        self.assertIn("Reader failed", carbonDaemonResult.error_message)

    # @patch("backend.src.daemon.readers.helpers.carbon_daemon.register_models")
    # @patch("backend.src.daemon.readers.helpers.carbon_daemon.ioc_util.resolve")
    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_run_carbon_service_exception(self, mock_ioc_util_resolve):
        """
        Test daemon execution when carbon service raises an exception.
        """
        # mock_reader = MagicMock()
        # mock_reader.read.return_value = self.sample_vms.copy()

        mock_carbon_service = MagicMock()
        mock_carbon_service.run_engine.side_effect = Exception("Carbon service failed")

        # mock_reader_factory = MagicMock()
        # mock_reader_factory.create_reader.return_value = mock_reader

        mock_ioc_util_resolve.return_value = mock_carbon_service

        # daemon = CarbonDaemon(
        #     self.mock_config,
        #     reader_factory=mock_reader_factory,
        #     writer_factory=mock_writer_factory,
        # )

        # result = daemon.run()

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = self.sample_vms.copy()
        mock_processor.run.side_effect = Exception("Carbon service failed")

        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])
        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIn(
            "unexpected error during daemon execution", carbonDaemonResult.error_message
        )
        self.assertIn("Carbon service failed", carbonDaemonResult.error_message)

    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_run_known_exception(self, mock_ioc_util_resolve):
        """
        Test daemon execution when a ConfigurationError is raised.
        """

        mock_ioc_util_resolve.return_value = IFVMService(DAILY_SECONDS)

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.side_effect = ConfigurationError(
            ErrorCode.CONFIG_INVALID_FILE, details="Known error occurred"
        )

        logger.info(f"Mock processor: {mock_processor}")

        orchestrator = CarbonDaemonOrchestrator(self.mock_config, [mock_processor])

        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIn(
            "known error during daemon execution",
            carbonDaemonResult.error_message.lower(),
        )

    @patch(
        "backend.src.daemon.readers.compute.reader_compute_azure.initialize_azure_client"
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


if __name__ == "__main__":
    unittest.main()
