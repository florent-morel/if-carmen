"""
Unit tests for the CarbonDaemonOrchestrator class.

These tests cover the orchestrator-based daemon architecture including
processor patterns, YAML configuration, and the CarbonDaemonOrchestrator execution.
"""

import logging
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from backend.src.common.carmen_exception import CarmenException

from backend.src.common.constants import (
    DAILY_SECONDS,
    SAMPLING_RATE_IN_SECONDS,
)
from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import ConfigurationError
from backend.src.daemon.carbon_daemon_orchestrator import (
    CarbonDaemonOrchestrator,
    CarbonDaemonResult,
)
from backend.src.daemon.runners.runner_compute import Runner_Compute
from backend.src.schemas.resource import ResourceType
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.services.carbon_service.impact_framework.service.if_vm_service import (
    IFVMService,
)

logger = logging.getLogger(__name__)


class TestCarbonDaemonOrchestratorComponents(unittest.TestCase):
    """
    Unit test class for the CarbonDaemonOrchestrator and related components.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.mock_config.output.output_path = tmp.name
        self.mock_config.source = MagicMock()
        self.mock_config.source.input_path = "etc/sample_data/test_data"
        logger.info(f"input_path: {self.mock_config.source.input_path}")
        self.sample_vms = [
            VirtualMachine(id="vm1", name="test-vm-1"),
            VirtualMachine(id="vm2", name="test-vm-2"),
        ]

    @patch("backend.src.daemon.carbon_daemon_orchestrator.register_models")
    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_runner_compute_success(
        self, mock_ioc_util_resolve, mock_register_models
    ):
        """
        Test successful Orchestrator execution with mocked reader, writer, and carbon service.
        """
        # Mock carbon service to return a successful result
        mock_ioc_util_resolve.return_value = IFVMService(
            SAMPLING_RATE_IN_SECONDS)

        # Execute runner on sample VMs
        runner_compute = Runner_Compute()
        resource_type_result = runner_compute.run(self.sample_vms.copy())

        # Mock processor to return the generated resource daemon result
        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = self.sample_vms.copy()
        mock_processor.run.return_value = resource_type_result

        # Orchestrate the daemon with the mocked processor
        orchestrator = CarbonDaemonOrchestrator(
            self.mock_config, [mock_processor])
        result = orchestrator.orchestrate_carbon_daemon()

        # Validate the results
        resultResource = result.dict_resource_result[ResourceType.VIRTUAL_MACHINE]
        self.assertIsNotNone(resultResource)

        listResourceResult = resultResource.list_processed_resources
        self.assertEqual(len(listResourceResult), 2)

        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertTrue(result.success)
        self.assertGreater(result.execution_time, 0)
        self.assertEqual(len(result.list_exceptions), 0)

        # Validate that the mocks were called as expected by the Orchestrator
        mock_register_models.assert_called_once()
        # TODO: There are 26 files in test folder, check with single file to
        # uncomment this
        # mock_processor.read.assert_called_once()
        mock_ioc_util_resolve.assert_called_once_with(
            CarbonService, "IFVm", 3600)

    @patch("backend.src.daemon.carbon_daemon_orchestrator.register_models")
    def test_orchestrator_no_vms_found(self, _mock_register_models):
        """
        Test orchestrator execution when no VMs are found in data source.
        """
        message = "No resources found."
        self.mock_config.source.input_path = "etc/sample_data/test_data/empty_csv"
        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = []

        runner_compute = Runner_Compute()
        mock_processor.runner = runner_compute
        # mock_processor.run = runner_compute.run([])

        orchestrator = CarbonDaemonOrchestrator(
            self.mock_config, [mock_processor])
        result = orchestrator.orchestrate_carbon_daemon()

        # read() was called; run() was never reached because the orchestrator short-circuits
        logger.info("mock reader")
        mock_processor.read.assert_called_once()

        # Orchestrator fails at the read stage
        self.assertIsInstance(result, CarbonDaemonResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.list_exceptions)
        logger.info(f"list_exceptions: {result.list_exceptions}")

        for exception in result.list_exceptions:
            logger.info(f"Exception: {exception.error_code}, \n details: {
                        exception.details}")
            self.assertEqual(exception.error_code,
                             ErrorCode.DATA_FETCH_NO_RESULTS)
            self.assertIn(
                message, exception.details
            )

    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_reader_compute_exception(self, mock_ioc_util_resolve):
        """
        Test daemon execution when reader raises an exception.
        """
        mock_ioc_util_resolve.return_value = IFVMService(DAILY_SECONDS)

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.side_effect = CarmenException(
            ErrorCode.UNKNOWN_ERROR, details="Test Reader failed")

        orchestrator = CarbonDaemonOrchestrator(
            self.mock_config, [mock_processor])

        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        self.assertFalse(carbonDaemonResult.success)
        logger.info(f"list_exceptions: {carbonDaemonResult.list_exceptions}")

        for exception in carbonDaemonResult.list_exceptions:
            logger.info(f"Exception: {exception.error_code}, \n details: {
                        exception.formatted_string}")
            if exception.error_code == ErrorCode.UNKNOWN_ERROR:
                self.assertIn(
                    "Unexpected error reading file", exception.details
                )
                self.assertIn("Test Reader failed", exception.details)

    @patch("backend.src.daemon.carbon_daemon_orchestrator.CarbonDaemonOrchestrator.write_report")
    @patch("backend.src.utils.ioc_util.resolve")
    def test_carbon_orchestrator_exception_at_orchestration_level(self, mock_ioc_util_resolve, mock_write_report):
        """
        Test daemon execution when carbon service raises an exception.
        """
        runner_error_msg = "Mock run side_effect"
        orchestrator_error_msg_1 = f"Failed to run engine for the given processors: {
            runner_error_msg}"
        orchestrator_error_msg_2 = "Unexpected error during daemon execution"

        mock_carbon_service = MagicMock()
        mock_carbon_service.run_engine.side_effect = Exception(
            "Carbon service failed")

        mock_ioc_util_resolve.return_value = mock_carbon_service

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = self.sample_vms.copy()
        mock_processor.run.side_effect = Exception(runner_error_msg)

        orchestrator = CarbonDaemonOrchestrator(
            self.mock_config, [mock_processor])
        mock_write_report.return_value = None

        # Call Main orchestrator process
        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        logger.info(carbonDaemonResult.list_exceptions)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIn(
            orchestrator_error_msg_1, carbonDaemonResult.list_exceptions[0].args[1]
        )
        self.assertIn(
            orchestrator_error_msg_2, carbonDaemonResult.list_exceptions[1].args[1]
        )

    @patch("backend.src.daemon.carbon_daemon_orchestrator.CarbonDaemonOrchestrator.write_report")
    @patch("backend.src.utils.ioc_util.resolve")
    def test_carbon_orchestrator_exception_at_resource_level(self, mock_ioc_util_resolve, mock_write_report):
        """
        Test daemon execution when carbon service raises an exception.
        """
        runner_error_msg = "Mock run side_effect"
        orchestrator_error_msg_1 = f"Failed to run engine for the given processors: {
            runner_error_msg}"
        orchestrator_error_msg_2 = "Unexpected error during daemon execution"

        mock_carbon_service = MagicMock()
        # mock_carbon_service.run_engine.side_effect = Exception("Carbon service failed")

        mock_ioc_util_resolve.return_value = mock_carbon_service

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        mock_processor.read.return_value = self.sample_vms.copy()
        mock_processor.run.side_effect = Exception(runner_error_msg)

        orchestrator = CarbonDaemonOrchestrator(
            self.mock_config, [mock_processor])
        mock_write_report.return_value = None
        # Call Main orchestrator process
        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        logger.info(carbonDaemonResult.list_exceptions)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIn(
            orchestrator_error_msg_1, carbonDaemonResult.list_exceptions[0].args[1]
        )
        self.assertIn(
            orchestrator_error_msg_2, carbonDaemonResult.list_exceptions[1].args[1]
        )
        logger.info(carbonDaemonResult.get_resource_type_list_exception(
            ResourceType.VIRTUAL_MACHINE))
        self.assertIn(runner_error_msg, carbonDaemonResult.get_resource_type_list_exception(
            ResourceType.VIRTUAL_MACHINE)[0].args[1])

    @patch("backend.src.utils.ioc_util.resolve")
    def test_daemon_run_carmen_exception(self, mock_ioc_util_resolve):
        """
        Test daemon execution when a ConfigurationError is raised.
        """

        mock_ioc_util_resolve.return_value = IFVMService(DAILY_SECONDS)

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.VIRTUAL_MACHINE
        error_details = "Test known error occurred"
        mock_processor.read.side_effect = ConfigurationError(
            ErrorCode.UNKNOWN_ERROR, details=error_details
        )

        logger.info(f"Mock processor: {mock_processor}")

        orchestrator = CarbonDaemonOrchestrator(
            self.mock_config, [mock_processor])

        carbonDaemonResult = orchestrator.orchestrate_carbon_daemon()

        self.assertIsInstance(carbonDaemonResult, CarbonDaemonResult)
        self.assertFalse(carbonDaemonResult.success)
        self.assertIsNotNone(carbonDaemonResult.list_exceptions)
        logger.info(f"list_exceptions: {carbonDaemonResult.list_exceptions}")

        for exception in carbonDaemonResult.list_exceptions:
            logger.info(f"Exception: {exception.error_code}, \n details: {
                        exception.details}")
            if exception.error_code == ErrorCode.UNKNOWN_ERROR:
                self.assertIn(
                    error_details, exception.details
                )

    def test_carmen_daemon_exception_no_processor(self):
        error_details = "no processor found"
        mock_config = MagicMock()
        daemon = CarbonDaemonOrchestrator(mock_config)
        result = daemon.orchestrate_carbon_daemon()

        assert result.success is False
        self.assertIsNotNone(result.list_exceptions)
        logger.info(f"list_exceptions: {result.list_exceptions}")

        for exception in result.list_exceptions:
            logger.info(f"Exception: {exception.error_code}, \n details: {
                        exception.formatted_string}")
            self.assertEqual(exception.error_code,
                             ErrorCode.CONFIG_NO_PROCESSOR)
            self.assertIn(
                error_details, exception.details
            )


if __name__ == "__main__":
    unittest.main()
