"""
Unit tests for CloudMetadata methods related to vCPU count resolution:
  - AbstractProviderConfig.get_cpu_max()
  - CloudMetadata._resolve_vcpu_count()   (fallback chain A / B / C)
"""

import pytest

from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import CarmenException
from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.impact_framework.models.cloud_metadata import (
    CloudMetadata,
)


# ---------------------------------------------------------------------------
# AbstractProviderConfig.get_cpu_max
# ---------------------------------------------------------------------------


class TestGetCpuMax:
    def test_returns_cpu_max_from_electricity_ratios(self):
        cfg = AbstractProviderConfig(electricity_ratios={"cpu_max": 3.76, "cpu_min": 0.78})
        assert cfg.get_cpu_max() == 3.76

    def test_returns_none_when_electricity_ratios_absent(self):
        cfg = AbstractProviderConfig()
        assert cfg.get_cpu_max() is None

    def test_returns_none_when_cpu_max_key_absent(self):
        cfg = AbstractProviderConfig(electricity_ratios={"cpu_min": 0.78})
        assert cfg.get_cpu_max() is None


# ---------------------------------------------------------------------------
# CloudMetadata._resolve_vcpu_count  (fallback chain)
# ---------------------------------------------------------------------------


class TestResolveVcpuCount:
    """Tests for the three-step fallback chain (billing → name parsing → raise)."""

    CPU_MAX = 3.76

    def _make_vm(self, vm_size: str, vcpu_count: int | None) -> VirtualMachine:
        return VirtualMachine(
            id="vm-x",
            name="vm-x",
            vm_size=vm_size,
            provider="azure",
            vcpu_count=vcpu_count,
            time_points=["2024-01-01T00:00:00Z"],
            cpu_util=[0.5],
            storage_size=[],
        )

    def test_fallback_path_a_uses_billing_vcpu_count(self):
        """Path A: vcpu_count already set from billing NbVCpus column."""
        vm = self._make_vm("Standard_Unknown_v99", vcpu_count=16)
        result = CloudMetadata._resolve_vcpu_count(vm, self.CPU_MAX)
        assert result == 16

    def test_fallback_path_b_parses_vcpu_count_from_name(self):
        """Path B: billing column absent, but name encodes vCPU count."""
        vm = self._make_vm("Standard_D32as_v5", vcpu_count=None)
        result = CloudMetadata._resolve_vcpu_count(vm, self.CPU_MAX)
        assert result == 32

    def test_fallback_path_c_raises_for_unresolvable_vm(self):
        """Path C: both billing column and name parsing fail → CarmenException."""
        vm = self._make_vm("Unknown_Type", vcpu_count=None)

        with pytest.raises(CarmenException) as exc_info:
            CloudMetadata._resolve_vcpu_count(vm, self.CPU_MAX)
        assert exc_info.value.error_code == ErrorCode.UNKNOWN_VM_INSTANCE_TYPE
