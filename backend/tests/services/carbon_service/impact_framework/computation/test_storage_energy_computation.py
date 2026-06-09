# pylint: disable=redefined-outer-name
"""
This file contains tests that check if the IF pipelines for storage services correctly compute the storage energy.
"""

import pytest

from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.impact_framework.service.if_storage_service import (
    IFStorageService,
)
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_storage_energy_helper,
    compute_storage_operational_helper,
    compute_storage_embodied_helper,
)

DURATION = 86400  # 24 hours (daily data)


@pytest.fixture
def sample_storage_resources():
    """Fixture: Returns a sample list of storage resources."""
    return [
        StorageResource(
            id="0",
            name="premium-ssd-p15",
            provider="azure",
            storage_type="SSD",
            replication_type="LRS",
            size_gb=256.0,  # P15 = 256 GB
            region="francecentral",
            carbon_intensity=56.0,
            time_points=["2025-04-10"],
        ),
        StorageResource(
            id="1",
            name="standard-hdd-s4",
            provider="azure",
            storage_type="HDD",
            replication_type="GRS",
            size_gb=32.0,  # S4 = 32 GB
            region="germanywestcentral",
            carbon_intensity=381.0,
            time_points=["2025-04-10"],
        ),
        StorageResource(
            id="2",
            name="standard-ssd-e10",
            provider="azure",
            storage_type="SSD",
            replication_type="ZRS",
            size_gb=128.0,  # E10 = 128 GB
            region="westeurope",
            carbon_intensity=268.0,
            time_points=["2025-04-10"],
        ),
        StorageResource(
            id="3",
            name="standard-ssd-e10",
            storage_type="SSD",
            replication_type="ZRS",
            size_gb=128.0,  # E10 = 128 GB
            region="westeurope",
            carbon_intensity=268.0,
            time_points=["2025-04-10"],
        ),
    ]


def test_storage_energy_computation_for_resources(sample_storage_resources, caplog):
    """
    Test: Verifies storage energy computation for storage resources.
    """
    # Calculate expected total energy manually for each resource
    expected_energy_ssd_lrs = compute_storage_energy_helper(
        256.0, "SSD", "LRS", DURATION
    )
    expected_energy_hdd_grs = compute_storage_energy_helper(
        32.0, "HDD", "GRS", DURATION
    )
    expected_energy_ssd_zrs = compute_storage_energy_helper(
        128.0, "SSD", "ZRS", DURATION
    )
    expected_energy_ssd_zrs_no_provider = compute_storage_energy_helper(
        128.0, "SSD", "", DURATION
    )

    service = IFStorageService(DURATION)
    with caplog.at_level("WARNING"):
        storage_resources = service.run_engine(sample_storage_resources)

    assert len(storage_resources) == 4
    assert storage_resources[0].total_energy_consumed == pytest.approx(
        expected_energy_ssd_lrs, rel=1e-2
    )
    assert storage_resources[1].total_energy_consumed == pytest.approx(
        expected_energy_hdd_grs, rel=1e-2
    )
    assert storage_resources[2].total_energy_consumed == pytest.approx(
        expected_energy_ssd_zrs, rel=1e-2
    )
    assert storage_resources[3].total_energy_consumed == pytest.approx(
        expected_energy_ssd_zrs_no_provider, rel=1e-2
    )
    
    assert (
        f"Storage resource {storage_resources[3].id} has no replication type; "
        "assuming replication factor of 1."
    ) in caplog.messages


def test_storage_embodied_computation_for_resources(sample_storage_resources):
    """
    Test: Verifies storage embodied carbon computation for storage resources.
    """
    expected_embodied_ssd_lrs = compute_storage_embodied_helper(
        256.0, "SSD", "LRS", DURATION
    )
    expected_embodied_hdd_grs = compute_storage_embodied_helper(
        32.0, "HDD", "GRS", DURATION
    )
    expected_embodied_ssd_zrs = compute_storage_embodied_helper(
        128.0, "SSD", "ZRS", DURATION
    )
    expected_embodied_ssd_zrs_no_provider = compute_storage_embodied_helper(
        128.0, "SSD", "", DURATION
    )

    service = IFStorageService(DURATION)
    storage_resources = service.run_engine(sample_storage_resources)

    assert len(storage_resources) == 4
    assert storage_resources[0].total_carbon_embodied == pytest.approx(
        expected_embodied_ssd_lrs, rel=1e-4
    )
    assert storage_resources[1].total_carbon_embodied == pytest.approx(
        expected_embodied_hdd_grs, rel=1e-4
    )
    assert storage_resources[2].total_carbon_embodied == pytest.approx(
        expected_embodied_ssd_zrs, rel=1e-4
    )
    assert storage_resources[3].total_carbon_embodied == pytest.approx(
        expected_embodied_ssd_zrs_no_provider, rel=1e-4
    )


def test_storage_operational_computation_for_resources(sample_storage_resources):
    """
    Test: Verifies storage operational carbon computation for storage resources.
    """
    # First calculate expected energy for each resource
    expected_energy_ssd_lrs = compute_storage_energy_helper(
        256.0, "SSD", "LRS", DURATION
    )
    expected_energy_hdd_grs = compute_storage_energy_helper(
        32.0, "HDD", "GRS", DURATION
    )
    expected_energy_ssd_zrs = compute_storage_energy_helper(
        128.0, "SSD", "ZRS", DURATION
    )
    expected_energy_ssd_zrs_no_provider = compute_storage_energy_helper(
        128.0, "SSD", "", DURATION
    )

    # Then calculate operational carbon using respective carbon intensities
    expected_operational_ssd_lrs = compute_storage_operational_helper(
        expected_energy_ssd_lrs, 56.0  # francecentral
    )
    expected_operational_hdd_grs = compute_storage_operational_helper(
        expected_energy_hdd_grs, 381.0  # germanywestcentral
    )
    expected_operational_ssd_zrs = compute_storage_operational_helper(
        expected_energy_ssd_zrs, 268.0  # westeurope
    )
    expected_operational_ssd_zrs_no_provider = compute_storage_operational_helper(
        expected_energy_ssd_zrs_no_provider, 268.0  # westeurope (default region CI)
    )

    service = IFStorageService(DURATION)
    storage_resources = service.run_engine(sample_storage_resources)

    assert len(storage_resources) == 4
    assert storage_resources[0].total_carbon_operational == pytest.approx(
        expected_operational_ssd_lrs, rel=1e-4
    )
    assert storage_resources[1].total_carbon_operational == pytest.approx(
        expected_operational_hdd_grs, rel=1e-4
    )
    assert storage_resources[2].total_carbon_operational == pytest.approx(
        expected_operational_ssd_zrs, rel=1e-4
    )
    assert storage_resources[3].total_carbon_operational == pytest.approx(
        expected_operational_ssd_zrs_no_provider, rel=1e-4
    )