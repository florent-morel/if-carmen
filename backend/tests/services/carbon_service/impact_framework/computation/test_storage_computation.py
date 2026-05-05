# pylint: disable=redefined-outer-name
"""
End-to-end tests for storage computation in impact framework.
"""
import pytest
import logging

from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.impact_framework.service.if_storage_service import (
    IFStorageService,
)
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_storage_energy_helper,
    compute_storage_embodied_helper,
)

from backend.src.schemas.resource import Resource, ResourceType
from backend.src.common.constants import DAILY_SECONDS

logger = logging.getLogger(__name__)


@pytest.fixture
def base_storage():
    """
    Fixture: Base storage resource.
    """
    return StorageResource(
        id="storage_test",
        name="Test Storage",
        storage_type="SSD",
        replication_type="LRS",
        size_gb=128.0,
        region="francecentral",
        carbon_intensity=44.0,
        time_points=["2021-01-01"],
        duration_seconds=DAILY_SECONDS,
        provider="azure",
    )


@pytest.mark.parametrize(
    "storage_type,size_gb,region,carbon_intensity",
    [
        ("SSD", 128.0, "francecentral", 44.0),
        ("HDD", 500.0, "germanywestcentral", 344.0),
    ],
)
def test_storage_energy_computation_by_type(
    base_storage, storage_type, size_gb, region, carbon_intensity
):
    """
    Tests energy computation for different storage types (SSD vs HDD).
    Replaces test_storage_energy_computation_ssd + test_storage_energy_computation_hdd.
    """
    # Customize the base storage for this test
    storage = base_storage.model_copy()
    storage.storage_type = storage_type
    storage.size_gb = size_gb
    storage.region = region
    storage.carbon_intensity = carbon_intensity
    storage.id = f"storage_{storage_type.lower()}"
    # storage.resource_type = f"{storage_type} Test"

    expected_energy = compute_storage_energy_helper(
        size_gb, storage_type, "LRS", DAILY_SECONDS
    )

    service = IFStorageService(DAILY_SECONDS)
    storage_resources = service.run_engine([storage])

    logger.info(f"storage_resources: {storage_resources}")

    assert len(storage_resources) == 1
    assert storage_resources[0].energy_consumed[0] == pytest.approx(
        expected_energy, rel=1e-2
    )


def test_storage_embodied_computation(base_storage):
    """
    Tests embodied emissions computation for SSD storage.
    Verifies embodied emissions calculation based on storage type.
    """
    storage = base_storage.model_copy()
    storage.id = "storage_embodied_test"
    storage.resource_type = "SSD Embodied Test"

    expected_embodied = compute_storage_embodied_helper(
        storage.size_gb,
        storage.storage_type,
        storage.replication_type,
        storage.duration_seconds,
    )

    service = IFStorageService(DAILY_SECONDS)
    storage_resources = service.run_engine([storage])

    assert len(storage_resources) == 1
    assert storage_resources[0].carbon_embodied[0] == pytest.approx(
        expected_embodied, rel=1e-2
    )


def test_storage_replication_factor_impact(base_storage):
    """
    Tests replication factor impact between LRS vs GRS.
    Verifies that GRS (factor 6) consumes 2x energy compared to LRS (factor 3).
    """
    # Test LRS (factor 3)
    lrs_storage = base_storage.model_copy()
    lrs_storage.replication_type = "LRS"
    lrs_storage.id = "storage_lrs_test"

    # Test GRS (factor 6)
    grs_storage = base_storage.model_copy()
    grs_storage.replication_type = "GRS"
    grs_storage.id = "storage_grs_test"

    service = IFStorageService(DAILY_SECONDS)
    lrs_result = service.run_engine([lrs_storage])
    grs_result = service.run_engine([grs_storage])

    # GRS should consume exactly 2x energy compared to LRS (6/3 = 2)
    lrs_energy = lrs_result[0].energy_consumed[0]
    grs_energy = grs_result[0].energy_consumed[0]

    assert grs_energy == pytest.approx(lrs_energy * 2, rel=1e-2)
