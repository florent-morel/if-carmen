"""
Tests that check if the cost IF pipelines correctly compute energy consumption and carbon emissions.
"""
import pytest

from backend.src.schemas.costResource import CostResource
from backend.src.services.carbon_service.impact_framework.service.if_cost_service import IFCostService
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_services_energy_helper,
    compute_services_operational_helper,
    compute_services_embodied_helper,
)

SAMPLING_RATE_IN_SECONDS = 86400  # 24 hours


@pytest.fixture
def mock_cost_resources():
    """
    Fixture to create mock cost resource list for testing.
    """
    return [
        CostResource(
            id="cost1",
            compute_energy=500.0,
            storage_energy=200.0,
            compute_embodied=300.0,
            storage_embodied=100.0,
            compute_cost=250.0,
            storage_cost=100.0,
            services_cost=50.0,
            carbon_intensity=100.0,
            time_points=["2025-11-10"]
        ),
        CostResource(
            id="cost2",
            compute_energy=400.0,
            storage_energy=300.0,
            compute_embodied=200.0,
            storage_embodied=150.0,
            compute_cost=150.0,
            storage_cost=125.0,
            services_cost=80.0,
            carbon_intensity=120.0,
            time_points=["2025-11-10"]
        )]


def test_services_energy_computation_for_cost_resources(mock_cost_resources):
    """
    Test that verifies services energy computation for cost resources.
    """
    # Calculate expected energy for each resource
    expected_energy_cost1 = compute_services_energy_helper(
        compute_energy=500.0,
        storage_energy=200.0,
        compute_cost=250.0,
        storage_cost=100.0,
        services_cost=50.0,
    )
    expected_energy_cost2 = compute_services_energy_helper(
        compute_energy=400.0,
        storage_energy=300.0,
        compute_cost=150.0,
        storage_cost=125.0,
        services_cost=80.0,
    )

    service = IFCostService(SAMPLING_RATE_IN_SECONDS)
    cost_resources = service.run_engine(mock_cost_resources)

    assert len(cost_resources) == 2
    assert cost_resources[0].total_energy_consumed == pytest.approx(
        expected_energy_cost1, rel=1e-2
    )
    assert cost_resources[1].total_energy_consumed == pytest.approx(
        expected_energy_cost2, rel=1e-2
    )


def test_services_operational_computation_for_cost_resources(mock_cost_resources):
    """
    Test that verifies services operational carbon computation for cost resources.
    """
    # Calculate expected operational carbon for each resource
    expected_operational_cost1 = compute_services_operational_helper(
        compute_energy=500.0,
        storage_energy=200.0,
        compute_cost=250.0,
        storage_cost=100.0,
        services_cost=50.0,
        carbon_intensity=100.0,
    )
    expected_operational_cost2 = compute_services_operational_helper(
        compute_energy=400.0,
        storage_energy=300.0,
        compute_cost=150.0,
        storage_cost=125.0,
        services_cost=80.0,
        carbon_intensity=120.0,
    )

    service = IFCostService(SAMPLING_RATE_IN_SECONDS)
    cost_resources = service.run_engine(mock_cost_resources)

    assert len(cost_resources) == 2
    assert cost_resources[0].total_carbon_operational == pytest.approx(
        expected_operational_cost1, rel=1e-4
    )
    assert cost_resources[1].total_carbon_operational == pytest.approx(
        expected_operational_cost2, rel=1e-4
    )


def test_services_embodied_computation_for_cost_resources(mock_cost_resources):
    """
    Test that verifies services embodied carbon computation for cost resources.
    """
    # Calculate expected embodied carbon for each resource
    expected_embodied_cost1 = compute_services_embodied_helper(
        compute_embodied=300.0,
        storage_embodied=100.0,
        compute_cost=250.0,
        storage_cost=100.0,
        services_cost=50.0,
    )
    expected_embodied_cost2 = compute_services_embodied_helper(
        compute_embodied=200.0,
        storage_embodied=150.0,
        compute_cost=150.0,
        storage_cost=125.0,
        services_cost=80.0,
    )

    service = IFCostService(SAMPLING_RATE_IN_SECONDS)
    cost_resources = service.run_engine(mock_cost_resources)

    assert len(cost_resources) == 2
    assert cost_resources[0].total_carbon_embodied == pytest.approx(
        expected_embodied_cost1, rel=1e-4
    )
    assert cost_resources[1].total_carbon_embodied == pytest.approx(
        expected_embodied_cost2, rel=1e-4
    )
