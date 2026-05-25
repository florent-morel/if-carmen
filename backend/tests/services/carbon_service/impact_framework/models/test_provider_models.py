"""
Unit tests for provider-aware IF models: PVmStorage, PStorage, MStorage.

Each test covers two scenarios:
- With a provider_config (correct coefficients used)
- Without a provider_config (graceful fallback defaults used)
"""

import pytest
from unittest.mock import MagicMock

from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)
from backend.src.services.carbon_service.impact_framework.models.power.p_vm_storage import (
    PVmStorage,
)
from backend.src.services.carbon_service.impact_framework.models.power.p_storage import (
    PStorage,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.m_storage import (
    MStorage,
)
from backend.src.schemas.storage_resource import StorageResource


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def azure_provider_config():
    """Minimal AbstractProviderConfig matching the azure.yaml coefficients."""
    return AbstractProviderConfig(
        electricity_ratios={
            "ssd": 0.0000012,
            "hdd": 0.00000065,
            "unknown": 0.000000925,
        },
        storage_replication_factors={"lrs": 3, "grs": 6, "zrs": 3},
    )


@pytest.fixture
def ssd_storage_resource():
    return StorageResource(
        id="disk-001",
        storage_type="ssd",
        replication_type="lrs",
        size_gb=128.0,
        region="westeurope",
        carbon_intensity=253.0,
        duration_seconds=86400,
    )


@pytest.fixture
def hdd_storage_resource():
    return StorageResource(
        id="disk-002",
        storage_type="hdd",
        replication_type="grs",
        size_gb=1024.0,
        region="westeurope",
        carbon_intensity=253.0,
        duration_seconds=86400,
    )


# ---------------------------------------------------------------------------
# PVmStorage
# ---------------------------------------------------------------------------

class TestPVmStorage:
    def test_with_provider_config_uses_unknown_ratio(self, azure_provider_config):
        """Coefficient in IF config comes from provider's unknown ratio."""
        model = PVmStorage(azure_provider_config)
        assert model.config["coefficient"] == pytest.approx(0.000000925)

    def test_without_provider_config_uses_global_defaults(self):
        """When no provider_config, the global unknown ratio from carbon_values.yaml is used."""
        model = PVmStorage(None)
        assert model.config["coefficient"] == pytest.approx(0.000000925)

    def test_without_provider_config_with_empty_ratios_uses_global_defaults(self):
        """When provider_config has no electricity_ratios, the global default is used."""
        cfg = AbstractProviderConfig()  # all None
        model = PVmStorage(cfg)
        assert model.config["coefficient"] == pytest.approx(0.000000925)

    def test_fill_inputs_returns_storage_size(self, azure_provider_config):
        """fill_inputs returns the VM disk size at the given time index."""
        # PVmStorage.fill_inputs reads from VirtualMachine.storage_size
        vm = MagicMock()
        vm.storage_size = [128.0, 256.0]
        model = PVmStorage(azure_provider_config)
        result = model.fill_inputs(vm, 1)
        assert result == {"storage/requested": 256.0}


# ---------------------------------------------------------------------------
# PStorage
# ---------------------------------------------------------------------------

class TestPStorage:
    def test_with_provider_config_ssd_lrs(self, azure_provider_config, ssd_storage_resource):
        """SSD + LRS: uses ssd electricity ratio and 3× replication factor."""
        model = PStorage(azure_provider_config)
        result = model.fill_inputs(ssd_storage_resource, 0)

        expected_size = 128.0 * 3  # LRS = 3 replicas
        expected_coeff = 0.0000012  # ssd ratio
        assert result["storage/requested"] == pytest.approx(expected_size)
        assert result["power/coefficient"] == pytest.approx(expected_coeff)

    def test_with_provider_config_hdd_grs(self, azure_provider_config, hdd_storage_resource):
        """HDD + GRS: uses hdd ratio and 6× replication factor."""
        model = PStorage(azure_provider_config)
        result = model.fill_inputs(hdd_storage_resource, 0)

        expected_size = 1024.0 * 6  # GRS = 6 replicas
        expected_coeff = 0.00000065
        assert result["storage/requested"] == pytest.approx(expected_size)
        assert result["power/coefficient"] == pytest.approx(expected_coeff)

    def test_without_provider_config_uses_global_defaults(self, ssd_storage_resource):
        """When no provider_config, global ratios from carbon_values.yaml are used."""
        model = PStorage(None)
        result = model.fill_inputs(ssd_storage_resource, 0)
        assert result["power/coefficient"] == pytest.approx(0.0000012)  # global ssd ratio

    def test_unknown_storage_type_falls_back_to_unknown(self, azure_provider_config):
        """An unrecognised storage type falls back to unknown ratio."""
        resource = StorageResource(
            id="disk-x",
            storage_type="nvme",
            replication_type="lrs",
            size_gb=64.0,
            region="eastus",
            carbon_intensity=100.0,
            duration_seconds=86400,
        )
        model = PStorage(azure_provider_config)
        result = model.fill_inputs(resource, 0)
        assert result["power/coefficient"] == pytest.approx(0.000000925)


# ---------------------------------------------------------------------------
# MStorage
# ---------------------------------------------------------------------------

class TestMStorage:
    def test_with_ssd_uses_carbon_values_coefficient(self, ssd_storage_resource):
        """SSD embodied coefficient comes from carbon_values.yaml (160 gCO2e/GB)."""
        model = MStorage()
        result = model.fill_inputs(ssd_storage_resource, 0)
        assert result["storage/embodied-coefficient"] == pytest.approx(160.0)

    def test_with_hdd_uses_carbon_values_coefficient(self, hdd_storage_resource):
        """HDD embodied coefficient comes from carbon_values.yaml (20 gCO2e/GB)."""
        model = MStorage()
        result = model.fill_inputs(hdd_storage_resource, 0)
        assert result["storage/embodied-coefficient"] == pytest.approx(20.0)

    def test_unknown_storage_type_falls_back_to_unknown_key(self):
        """Unrecognised storage type uses the 'unknown' key from carbon_values.yaml."""
        resource = StorageResource(
            id="disk-x",
            storage_type="nvme",
            replication_type="lrs",
            size_gb=64.0,
            region="eastus",
            carbon_intensity=100.0,
            duration_seconds=86400,
        )
        model = MStorage()
        result = model.fill_inputs(resource, 0)
        assert result["storage/embodied-coefficient"] == pytest.approx(90.0)

    def test_provider_config_arg_accepted_for_compatibility(self, azure_provider_config, ssd_storage_resource):
        """MStorage still accepts a provider_config argument without breaking."""
        model = MStorage(azure_provider_config)
        result = model.fill_inputs(ssd_storage_resource, 0)
        # Coefficient still comes from carbon_values.yaml, not provider_config
        assert result["storage/embodied-coefficient"] == pytest.approx(160.0)
