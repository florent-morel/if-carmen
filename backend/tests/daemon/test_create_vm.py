"""
Unit tests for virtual_machine_helpers functions related to VM creation and vCPU count resolution:
  - parse_vcpu_count_from_azure_vm_size (name-parsing heuristic, Azure only)
  - _parse_vcpu_count_from_row  (accessed via create_vm)
  - create_vm                  (vcpu_count field populated)
"""

import unittest
from unittest.mock import patch, MagicMock

from backend.src.daemon.readers.helpers.virtual_machine_helpers import (
    parse_vcpu_count_from_azure_vm_size,
    create_vm,
)


# ---------------------------------------------------------------------------
# parse_vcpu_count_from_azure_vm_size
# ---------------------------------------------------------------------------


class TestParseVcpuCountFromVmSize(unittest.TestCase):
    def test_standard_d_series(self):
        self.assertEqual(parse_vcpu_count_from_azure_vm_size("Standard_D32as_v5"), 32)

    def test_standard_e_series(self):
        self.assertEqual(parse_vcpu_count_from_azure_vm_size("Standard_E4s_v3"), 4)

    def test_standard_a_series(self):
        self.assertEqual(parse_vcpu_count_from_azure_vm_size("Standard_A1_v2"), 1)

    def test_standard_b_series(self):
        self.assertEqual(parse_vcpu_count_from_azure_vm_size("Standard_B2ms"), 2)

    def test_case_insensitive(self):
        self.assertEqual(parse_vcpu_count_from_azure_vm_size("standard_d8s_v3"), 8)

    def test_unrecognised_format_returns_none(self):
        # Does not start with Standard_ — heuristic cannot apply
        self.assertIsNone(parse_vcpu_count_from_azure_vm_size("Unknown_Type"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_vcpu_count_from_azure_vm_size(""))

    def test_none_string_returns_none(self):
        # Defensive: callers may pass None even though the annotation says str
        self.assertIsNone(parse_vcpu_count_from_azure_vm_size(None))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# create_vm — vcpu_count field
# ---------------------------------------------------------------------------

_MINIMAL_ROW = {
    "Region": "eastus",
    "Provider": "azure",
    "VmSize": "Standard_D4as_v5",
    "Service": "compute",
    "Component": "",
    "ResourceName": "vm-1",
    "Instance": "",
    "Environment": "prd",
    "Partition": "",
    "Cost": "10.5",
}


class TestCreateVmVcpuCount(unittest.TestCase):
    """Tests that create_vm correctly populates vcpu_count from the VmNbCpus column."""

    def _make_row(self, nb_vcpus_value):
        row = dict(_MINIMAL_ROW)
        if nb_vcpus_value is not None:
            row["VmNbCpus"] = nb_vcpus_value
        return row

    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.PaasCiMapper")
    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.config")
    def test_vcpu_count_populated_from_input_csv_column(self, mock_config, mock_mapper):
        mock_config.provider_configs.get.return_value = MagicMock(get_pue=lambda: 1.2)
        mock_mapper.calculate_ci.return_value = 200.0

        row = self._make_row("4")
        vm = create_vm(row, "vm-id-1")

        self.assertEqual(vm.vcpu_count, 4)

    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.PaasCiMapper")
    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.config")
    def test_vcpu_count_is_none_when_column_absent(self, mock_config, mock_mapper):
        mock_config.provider_configs.get.return_value = MagicMock(get_pue=lambda: 1.2)
        mock_mapper.calculate_ci.return_value = 200.0

        row = self._make_row(None)  # VmNbCpus column missing entirely
        vm = create_vm(row, "vm-id-2")

        self.assertIsNone(vm.vcpu_count)

    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.PaasCiMapper")
    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.config")
    def test_vcpu_count_is_none_for_dash_value(self, mock_config, mock_mapper):
        mock_config.provider_configs.get.return_value = MagicMock(get_pue=lambda: 1.2)
        mock_mapper.calculate_ci.return_value = 200.0

        row = self._make_row("-")
        vm = create_vm(row, "vm-id-3")

        self.assertIsNone(vm.vcpu_count)

    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.PaasCiMapper")
    @patch("backend.src.daemon.readers.helpers.virtual_machine_helpers.config")
    def test_vcpu_count_handles_float_string(self, mock_config, mock_mapper):
        """CSV may store integers as floats e.g. '4.0'; int(float('4.0')) == 4."""
        mock_config.provider_configs.get.return_value = MagicMock(get_pue=lambda: 1.2)
        mock_mapper.calculate_ci.return_value = 200.0

        row = self._make_row("4.0")
        vm = create_vm(row, "vm-id-4")

        self.assertEqual(vm.vcpu_count, 4)


if __name__ == "__main__":
    unittest.main()
