"""
Tests that check if the misc services IF pipelines correctly compute energy consumption and carbon emissions.
"""
import pytest

from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.services.carbon_service.impact_framework.service.if_misc_services_service import (
    IFMiscServicesService,
)
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_services_energy_helper,
    compute_services_operational_helper,
    compute_services_embodied_helper,
)

SAMPLING_RATE_IN_SECONDS = 86400  # 24 hours


@pytest.fixture
def mock_misc_services_resources():
    """
    Fixture to create mock misc services resource list for testing.
    """
    return [
        MiscServicesResource(
            id="misc_service1",
            compute_energy=500.0,
            storage_energy=200.0,
            compute_embodied=300.0,
            storage_embodied=100.0,
            compute_cost=250.0,
            storage_cost=100.0,
            cost=50.0,
            carbon_intensity=100.0,
            time_points=["2025-11-10"],
        ),
        MiscServicesResource(
            id="misc_service2",
            compute_energy=400.0,
            storage_energy=300.0,
            compute_embodied=200.0,
            storage_embodied=150.0,
            compute_cost=150.0,
            storage_cost=125.0,
            cost=80.0,
            carbon_intensity=120.0,
            time_points=["2025-11-10"],
        ),
    ]


def test_services_energy_computation_for_misc_services_resources(
    mock_misc_services_resources,
):
    """
    Test that verifies services energy computation for misc services resources.
    """
    # Calculate expected energy for each resource
    expected_energy_misc_service1 = compute_services_energy_helper(
        compute_energy=500.0,
        storage_energy=200.0,
        compute_cost=250.0,
        storage_cost=100.0,
        cost=50.0,
    )
    expected_energy_misc_service2 = compute_services_energy_helper(
        compute_energy=400.0,
        storage_energy=300.0,
        compute_cost=150.0,
        storage_cost=125.0,
        cost=80.0,
    )

    service = IFMiscServicesService(SAMPLING_RATE_IN_SECONDS)
    misc_services_resources = service.run_engine(mock_misc_services_resources)

    assert len(misc_services_resources) == 2
    assert misc_services_resources[0].total_energy_consumed == pytest.approx(
        expected_energy_misc_service1, rel=1e-2
    )
    assert misc_services_resources[1].total_energy_consumed == pytest.approx(
        expected_energy_misc_service2, rel=1e-2
    )


def test_services_operational_computation_for_misc_services_resources(
    mock_misc_services_resources,
):
    """
    Test that verifies services operational carbon computation for misc services resources.
    """
    # Calculate expected operational carbon for each resource
    expected_operational_misc_service1 = compute_services_operational_helper(
        compute_energy=500.0,
        storage_energy=200.0,
        compute_cost=250.0,
        storage_cost=100.0,
        cost=50.0,
        carbon_intensity=100.0,
    )
    expected_operational_misc_service2 = compute_services_operational_helper(
        compute_energy=400.0,
        storage_energy=300.0,
        compute_cost=150.0,
        storage_cost=125.0,
        cost=80.0,
        carbon_intensity=120.0,
    )

    service = IFMiscServicesService(SAMPLING_RATE_IN_SECONDS)
    misc_services_resources = service.run_engine(mock_misc_services_resources)

    assert len(misc_services_resources) == 2
    assert misc_services_resources[0].total_carbon_operational == pytest.approx(
        expected_operational_misc_service1, rel=1e-4
    )
    assert misc_services_resources[1].total_carbon_operational == pytest.approx(
        expected_operational_misc_service2, rel=1e-4
    )


def test_services_embodied_computation_for_misc_services_resources(
    mock_misc_services_resources,
):
    """
    Test that verifies services embodied carbon computation for misc services resources.
    """
    # Calculate expected embodied carbon for each resource
    expected_embodied_misc_service1 = compute_services_embodied_helper(
        compute_embodied=300.0,
        storage_embodied=100.0,
        compute_cost=250.0,
        storage_cost=100.0,
        cost=50.0,
    )
    expected_embodied_misc_service2 = compute_services_embodied_helper(
        compute_embodied=200.0,
        storage_embodied=150.0,
        compute_cost=150.0,
        storage_cost=125.0,
        cost=80.0,
    )

    service = IFMiscServicesService(SAMPLING_RATE_IN_SECONDS)
    misc_services_resources = service.run_engine(mock_misc_services_resources)

    assert len(misc_services_resources) == 2
    assert misc_services_resources[0].total_carbon_embodied == pytest.approx(
        expected_embodied_misc_service1, rel=1e-4
    )
    assert misc_services_resources[1].total_carbon_embodied == pytest.approx(
        expected_embodied_misc_service2, rel=1e-4
    )
