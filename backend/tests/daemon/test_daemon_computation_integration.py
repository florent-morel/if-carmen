# pylint: disable=redefined-outer-name
"""
This file contains tests that validate the entire carbon calculation pipeline for the daemon.
This is the Integration tests for the Carbon Daemon.
Tests both VM and Storage resource processing. Computed values are compared to values
computed by the functions in the module computation_helpers.py
"""

import sys
import os
import csv
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pytest
import unittest
from backend.src.common.constants import PUE_AZURE
from backend.tests.daemon import mock_data
from backend.src.daemon.carbon_daemon_orchestrator import main as CarbonDaemon
from backend.src.daemon.processors.processor_compute import CarbonDaemonProcessorCompute

# from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_cpu_energy,
    compute_embodied_carbon,
    compute_memory_energy,
    compute_storage_energy,
    compute_operational_carbon,
    compute_tdp_ratio,
    compute_storage_energy_helper,
    compute_storage_embodied_helper,
    compute_storage_operational_helper,
)

from backend.src.daemon.carbon_daemon_orchestrator import (
    CarbonDaemonResult,
    CarbonDaemonOrchestrator,
)


# Adjust the Python path
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, project_root)

# Set up report directory for tests
TEST_REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "report"))
os.makedirs(TEST_REPORT_DIR, exist_ok=True)

# constants for computation
DURATION_IN_HOURS = 24


@pytest.fixture
def setup_report_dir():
    """
    Cleans the report directory before each test.
    """
    if os.path.exists(TEST_REPORT_DIR):
        for filename in os.listdir(TEST_REPORT_DIR):
            file_path = os.path.join(TEST_REPORT_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except OSError as ex:
                print(f"Error deleting file {file_path}: {ex}")


def read_co2_report(report_file: str) -> dict[str, dict[str, float | str]]:
    """
    Reads the generated CO2 report CSV file and returns a dictionary keyed by resource ID.
    Handles all resource types (VMs, Storage, etc.) from the unified carbon report.

    Returns:
        dict: Dictionary with resource IDs as keys and carbon metrics as values.
              Each entry includes ResourceType to distinguish VMs from Storage.
    """
    results = {}
    with open(report_file, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            resource_id = row["Id"]
            results[resource_id] = {
                "EnergyKWH": float(row["EnergyKWH"]),
                "OperationalCarbonGramsCO2eq": float(
                    row["OperationalCarbonGramsCO2eq"]
                ),
                "EmbodiedCarbonGramsCO2eq": float(row["EmbodiedCarbonGramsCO2eq"]),
                "ResourceType": row.get("ResourceType", "VM"),
            }
    return results


def compute_expected_metrics(
    tdp: float,
    cpu_util: float,
    memory_requested: float,
    duration: float,
    vcpu_allocated: float,
    vcpu_total: float,
    storage_size: float,
):
    """
    Computes "by hand" using the functions in the compuation_helpers.py module the expected energy,
    operational carbon and embodied carbon for a virtual machine.
    Args:
        tdp (float): the thermal design power of the virtual machine
        cpu_util (float): the cpu utilization of the virtual machine
        memory_requested (float): the memory requested by the virtual machine
        duration (float): the duration of an observation in seconds
        vcpu_allocated (float)
        vcpu_total (float)
        storage_size (float)

    Returns:
        Tuple[float, float, float]: energy, operational carbon, embodied carbon
    """
    tdp_ratio = compute_tdp_ratio(cpu_util)
    cpu_energy = compute_cpu_energy(tdp, tdp_ratio, duration)
    memory_energy = compute_memory_energy(memory_requested, duration)
    storage_energy = compute_storage_energy(storage_size, duration)
    energy = cpu_energy + memory_energy + storage_energy
    energy = energy * PUE_AZURE
    operational_carbon = compute_operational_carbon(energy)
    embodied_carbon = compute_embodied_carbon(
        vcpu_allocated, vcpu_total, storage_size, DURATION_IN_HOURS
    )
    return energy, operational_carbon, embodied_carbon


def compute_expected_storage_metrics(
    storage_type: str,
    replication_type: str,
    size_gb: float,
    duration_seconds: float,
    carbon_intensity: float,
):
    """
    Computes expected storage metrics using computation helpers.

    Args:
        storage_type: Storage type (SSD, HDD, Unknown)
        replication_type: Replication type (LRS, GRS, ZRS, etc.)
        size_gb: Storage size in GB
        duration_seconds: Duration in seconds
        carbon_intensity: Carbon intensity in gCO2/kWh

    Returns:
        tuple: (energy_kwh, operational_gco2, embodied_gco2, total_gco2)
    """
    energy_kwh = compute_storage_energy_helper(
        size_gb, storage_type, replication_type, duration_seconds
    )
    operational_gco2 = compute_storage_operational_helper(energy_kwh, carbon_intensity)
    embodied_gco2 = compute_storage_embodied_helper(
        size_gb, storage_type, replication_type, duration_seconds
    )

    return energy_kwh, operational_gco2, embodied_gco2


@pytest.fixture
def vm1():
    """
    Returns a sample virtual machine dictionary.
    """
    return {
        "name": "/subscriptions/92c669c2-8bb7-4c50-94b7-24e2867ca637/resourceGroups/RG-REG-USE-AVD-001/providers/Microsoft.Compute/virtualMachines/USEAVDD409-0",
        "average_cpu_util": 0.0545,
        "memory_requested": 16,
        "vcpu_allocated": 4,
        "vcpu_total": 128,
        "tdp": 280,
        "storage_size": 128,
    }


@pytest.fixture
def storage1():
    """
    Returns a sample storage resource dictionary.
    """
    return {
        "storage_type": "SSD",
        "size_gb": 32.0,
        "carbon_intensity": 253.0,
        "replication_type": "LRS",
        "duration_seconds": 3600,
    }


@pytest.fixture
def mock_daemon_config() -> MagicMock:
    """
    Returns a mock DaemonConfig for testing.
    """
    config = MagicMock()
    config.source = MagicMock()
    config.source.type = "azure"
    config.upload = MagicMock()
    config.upload.type = "local"
    config.upload.local = MagicMock()
    config.upload.local.upload_path = TEST_REPORT_DIR
    return config


def test_carbon_daemon_with_sample_data(
    setup_report_dir: None,
    vm1: dict[str, str | float | int],
    storage1: dict[str, str | float | int],
    mock_daemon_config: MagicMock,
):
    """
    Test the daemon with sample VM data from test files.
    Validates real carbon calculations using the Impact Framework.
    """
    # Get sample VM data from test files
    sample_vms = mock_data.read_sample_vm_data(
        {"ppt": ["usage_2025-06-01_00.csv"] * 24}, ""
    )

    with (
        patch(
            "backend.src.daemon.readers.abstract_reader.AbstractReader"
        ) as mock_reader_abstract_class,
        patch(
            "backend.src.daemon.writers.abstract_writer.AbstractWriter"
        ) as mock_writer_abstract_class,
    ):
        # Set up reader mock to return sample VMs
        mock_reader_abstract = MagicMock()
        mock_reader_abstract_class.return_value = mock_reader_abstract
        mock_reader = MagicMock()
        mock_reader.read.return_value = sample_vms
        mock_reader_abstract.create_reader.return_value = mock_reader

        # Set up writer mock to capture processed VMs
        mock_writer_abstract = MagicMock()
        mock_writer_abstract_class.return_value = mock_writer_abstract
        mock_writer = MagicMock()

        captured_vms = []

        def capture_vms(config: MagicMock, vms: list[VirtualMachine]) -> MagicMock:
            captured_vms.extend(vms)
            return mock_writer

        mock_writer_abstract.create_writer.side_effect = capture_vms

        daemon = CarbonDaemonOrchestrator(
            mock_daemon_config,
            list_carbon_daemon_resource_processors=[CarbonDaemonProcessorCompute],
        )
        result = daemon.orchestrate_carbon_daemon()

        assert result.success is True
        assert result.list_processed_resources == sample_vms

        assert len(captured_vms) == len(sample_vms)

        if captured_vms:
            first_vm = captured_vms[0]

            (
                expected_energy,
                expected_operational_carbon,
                expected_embodied_carbon,
            ) = compute_expected_metrics(
                float(vm1["tdp"]),
                float(vm1["average_cpu_util"]),
                float(vm1["memory_requested"]),
                DURATION_IN_HOURS,
                float(vm1["vcpu_allocated"]),
                float(vm1["vcpu_total"]),
                float(vm1["storage_size"]),
            )

            assert first_vm.total_energy_consumed > 0, "Energy should be positive"
            assert (
                first_vm.total_carbon_operational > 0
            ), "Operational carbon should be positive"
            assert (
                first_vm.total_carbon_embodied > 0
            ), "Embodied carbon should be positive"

            calculated_total = (
                first_vm.total_carbon_operational + first_vm.total_carbon_embodied
            )
            assert calculated_total > 0, "Calculated total carbon should be positive"

            assert (
                abs(first_vm.total_energy_consumed - expected_energy) / expected_energy
                < 0.5
            ), f"Energy {first_vm.total_energy_consumed} vs expected {expected_energy} differs too much"


@patch("backend.src.daemon.abstract_carbon_daemon.config")
def test_daemon_with_mocked_components(
    mock_config: MagicMock,
    setup_report_dir: None,
    mock_daemon_config: MagicMock,
):
    """
    Test the daemon with fully mocked reader, writer, and carbon service.
    This test focuses on the integration and data flow rather than actual calculations.
    """
    mock_config.carmen_daemon = mock_daemon_config

    test_vms = [
        VirtualMachine(
            id="vm1", name="test-vm-1", region="eastus", vm_size="Standard_D2s_v3"
        ),
        VirtualMachine(
            id="vm2", name="test-vm-2", region="westus", vm_size="Standard_D4s_v3"
        ),
    ]

    processed_vms = [
        VirtualMachine(
            id="vm1",
            name="test-vm-1",
            region="eastus",
            vm_size="Standard_D2s_v3",
            total_energy_consumed=10.5,
            total_carbon_operational=250.0,
            total_carbon_embodied=150.0,
            total_carbon_emitted=400.0,
        ),
        VirtualMachine(
            id="vm2",
            name="test-vm-2",
            region="westus",
            vm_size="Standard_D4s_v3",
            total_energy_consumed=15.2,
            total_carbon_operational=380.0,
            total_carbon_embodied=220.0,
            total_carbon_emitted=600.0,
        ),
    ]

    with (
        patch(
            "backend.src.daemon.abstract_carbon_daemon.DefaultReaderFactory"
        ) as mock_reader_factory_class,
        patch(
            "backend.src.daemon.abstract_carbon_daemon.DefaultWriterFactory"
        ) as mock_writer_factory_class,
        patch(
            "backend.src.daemon.abstract_carbon_daemon.ioc_util.resolve"
        ) as mock_ioc_resolve,
    ):
        mock_reader_factory = MagicMock()
        mock_reader_factory_class.return_value = mock_reader_factory
        mock_reader = MagicMock()
        mock_reader.read.return_value = test_vms
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()
        mock_writer_factory_class.return_value = mock_writer_factory
        mock_writer = MagicMock()
        mock_writer_factory.create_writer.return_value = mock_writer

        mock_carbon_service = MagicMock()
        mock_carbon_service.run_engine.return_value = processed_vms
        mock_ioc_resolve.return_value = mock_carbon_service

        daemon = CarbonDaemon(mock_daemon_config)
        result = daemon.run()

        assert result.success is True
        assert result.vm_count == 2
        assert result.execution_time > 0
        assert result.error_message == ""

        mock_reader_factory.create_reader.assert_called_once_with(mock_daemon_config)
        mock_reader.read.assert_called_once()
        mock_carbon_service.run_engine.assert_called_once_with(test_vms)
        mock_writer_factory.create_writer.assert_called_once_with(
            mock_daemon_config, processed_vms
        )
        mock_writer.upload_compute_report.assert_called_once()


@patch("backend.src.daemon.abstract_carbon_daemon.config")
def test_daemon_computation_integration(
    mock_config: MagicMock,
    setup_report_dir: None,
    vm1: dict[str, str | float | int],
    mock_daemon_config: MagicMock,
):
    """
    Integration test that uses real carbon calculations with mocked I/O.
    This test validates that the carbon computation pipeline works correctly with actual IF calculations.
    """
    mock_config.carmen_daemon = mock_daemon_config

    from backend.src.utils.paas_ci_mapper import PaasCiMapper

    test_vm = VirtualMachine(
        id="test-vm-1",
        name=str(vm1["name"]),
        region="eastus",
        vm_size="Standard_D4s_v3",
        cpu_util=[float(vm1["average_cpu_util"])] * 24,  # 24 hours of data
        storage_size=[float(vm1["storage_size"])] * 24,
        time_points=[
            (datetime.now() - timedelta(hours=i)).isoformat() for i in range(24)
        ],
        carbon_intensity=PaasCiMapper.calculate_ci("eastus"),
    )

    with (
        patch(
            "backend.src.daemon.abstract_carbon_daemon.DefaultReaderFactory"
        ) as mock_reader_factory_class,
        patch(
            "backend.src.daemon.abstract_carbon_daemon.DefaultWriterFactory"
        ) as mock_writer_factory_class,
    ):
        mock_reader_factory = MagicMock()
        mock_reader_factory_class.return_value = mock_reader_factory
        mock_reader = MagicMock()
        mock_reader.read.return_value = [test_vm]
        mock_reader_factory.create_reader.return_value = mock_reader

        mock_writer_factory = MagicMock()
        mock_writer_factory_class.return_value = mock_writer_factory
        mock_writer = MagicMock()

        captured_vms = []

        def capture_vms(config: MagicMock, vms: list[VirtualMachine]) -> MagicMock:
            captured_vms.extend(vms)
            return mock_writer

        mock_writer_factory.create_writer.side_effect = capture_vms

        daemon = CarbonDaemon(mock_daemon_config)
        result = daemon.run()

        assert result.success is True
        assert result.vm_count == 1

        assert len(captured_vms) == 1
        processed_vm = captured_vms[0]

        assert processed_vm.total_energy_consumed > 0
        assert processed_vm.total_carbon_operational > 0
        assert processed_vm.total_carbon_embodied > 0

        calculated_total = (
            processed_vm.total_carbon_operational + processed_vm.total_carbon_embodied
        )
        assert calculated_total > 0, "Calculated total carbon should be positive"

        assert (
            0.1 < processed_vm.total_energy_consumed < 100.0
        ), f"Energy {processed_vm.total_energy_consumed} outside expected range"
        assert (
            10.0 < processed_vm.total_carbon_operational < 10000.0
        ), f"Operational carbon {processed_vm.total_carbon_operational} outside expected range"
        assert (
            1.0 < processed_vm.total_carbon_embodied < 5000.0
        ), f"Embodied carbon {processed_vm.total_carbon_embodied} outside expected range"


class TestMainFunction(unittest.TestCase):
    """
    Unit test class for the main function in the carbon_daemon module.
    """

    @patch("backend.src.daemon.abstract_carbon_daemon.config")
    @patch("backend.src.daemon.abstract_carbon_daemon.CarbonDaemon")
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

    @patch("backend.src.daemon.abstract_carbon_daemon.config")
    @patch("backend.src.daemon.abstract_carbon_daemon.CarbonDaemon")
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

    @patch("backend.src.daemon.abstract_carbon_daemon.config")
    @patch("backend.src.daemon.abstract_carbon_daemon.CarbonDaemon")
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
