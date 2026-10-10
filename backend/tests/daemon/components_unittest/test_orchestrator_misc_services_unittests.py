"""Tests for the shared cost ratios used by miscellaneous services."""

import logging
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.src.daemon.carbon_daemon_orchestrator import CarbonDaemonOrchestrator
from backend.src.daemon.runners.abstract_runner import AbstractRunner
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.resource import Resource, ResourceType
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)
from backend.src.utils.metrics_mapper import MetricsMapper


@pytest.mark.parametrize(
    "use_vm,use_storage", [(False, False), (True, False), (False, True), (True, True)]
)
def test_hydrate_misc_services_ratios_once_for_all_resources(
    use_vm, use_storage, caplog
):
    defaults = SimpleNamespace(
        compute_cost=1.0,
        compute_energy=0.15,
        compute_embodied=15.0,
        storage_cost=1.0,
        storage_energy=0.02,
        storage_embodied=65.0,
    )
    vm_result = SimpleNamespace(
        total_cost=400.0,
        total_energy_consumed=50.0,
        total_carbon_embodied=60.0,
    )
    storage_result = SimpleNamespace(
        total_cost=500.0,
        total_energy_consumed=70.0,
        total_carbon_embodied=80.0,
    )
    results = {}
    if use_vm:
        results[ResourceType.VIRTUAL_MACHINE] = vm_result
    if use_storage:
        results[ResourceType.STORAGE] = storage_result

    resources = [
        MiscServicesResource(id="service-1", time_points=["day-1", "day-2"]),
        MiscServicesResource(id="service-2", time_points=["day-1"]),
    ]
    with patch("backend.src.daemon.carbon_daemon_orchestrator.config") as mock_config:
        mock_config.carbon_values_config.default_misc_services_constants = defaults
        with caplog.at_level(logging.INFO):
            CarbonDaemonOrchestrator.__new__(
                CarbonDaemonOrchestrator
            )._hydrate_misc_services_resources(resources, results)

    compute_cost = vm_result.total_cost if use_vm else defaults.compute_cost
    storage_cost = storage_result.total_cost if use_storage else defaults.storage_cost
    compute_energy = (
        vm_result.total_energy_consumed if use_vm else defaults.compute_energy
    )
    storage_energy = (
        storage_result.total_energy_consumed if use_storage else defaults.storage_energy
    )
    compute_embodied = (
        vm_result.total_carbon_embodied if use_vm else defaults.compute_embodied
    )
    storage_embodied = (
        storage_result.total_carbon_embodied
        if use_storage
        else defaults.storage_embodied
    )
    expected_energy_ratio = (
        0.75 * compute_energy / compute_cost + 0.25 * storage_energy / storage_cost
    )
    expected_embodied_ratio = (
        0.75 * compute_embodied / compute_cost + 0.25 * storage_embodied / storage_cost
    )

    for resource in resources:
        assert resource.energy_cost_ratio == pytest.approx(expected_energy_ratio)
        assert resource.embodied_cost_ratio == pytest.approx(expected_embodied_ratio)
    assert (
        sum("Misc services cost ratios" in record.message for record in caplog.records)
        == 1
    )


@pytest.mark.parametrize(
    "result_type", [ResourceType.VIRTUAL_MACHINE, ResourceType.STORAGE]
)
def test_hydrate_misc_services_rejects_zero_measured_cost(result_type):
    defaults = SimpleNamespace(
        compute_cost=1.0,
        compute_energy=0.15,
        compute_embodied=15.0,
        storage_cost=1.0,
        storage_energy=0.02,
        storage_embodied=65.0,
    )
    measured_result = SimpleNamespace(
        total_cost=0.0,
        total_energy_consumed=50.0,
        total_carbon_embodied=60.0,
    )
    resource = MiscServicesResource(id="service-1", time_points=["day-1"])

    with patch("backend.src.daemon.carbon_daemon_orchestrator.config") as mock_config:
        mock_config.carbon_values_config.default_misc_services_constants = defaults
        with pytest.raises(
            ValueError, match="require nonzero compute and storage costs"
        ):
            CarbonDaemonOrchestrator.__new__(
                CarbonDaemonOrchestrator
            )._hydrate_misc_services_resources(
                [resource], {result_type: measured_result}
            )


def test_tiny_if_impact_remains_in_fleet_totals_and_cost():
    if_output = {
        "tiny": {
            "aggregated": {"carbon": 0.00004, "energy": 0.00004},
            "outputs": [{"carbon": 0.00004, "energy": 0.00004}],
        }
    }
    resource = Resource(id="tiny", cost=10.0)
    metrics = IFService.get_measurements_from_output(if_output, resource.id)
    MetricsMapper.map_metrics_to_resource(metrics, resource)

    result = AbstractRunner.create_resource_type_result(
        None, True, 0.0, ResourceType.VIRTUAL_MACHINE, [resource], []
    )

    assert result.total_energy_consumed == 0.00004
    assert result.total_carbon_emitted == 0.00004
    assert result.total_cost == 10.0
