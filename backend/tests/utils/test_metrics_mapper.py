"""
This file contains unit tests for the metrics mapper
"""

from backend.src.schemas.compute_resource import ComputeResource
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.schemas.storage_resource import StorageResource
from backend.src.utils.metrics_mapper import MetricsMapper


def test_map_metrics_to_compute_resource():
    """
    Tests if the metrics are correctly mapped to the compute resource
    """
    metrics = {
        "carbon": {"observations": [10, 20, 30], "aggregated": 60},
        "energy": {"observations": [5, 15, 25], "aggregated": 45},
        "carbon-embodied": {"observations": [1, 2, 3], "aggregated": 6},
        "carbon-operational": {"observations": [4, 5, 6], "aggregated": 15},
        "cpu/energy": {"observations": [7, 8, 9], "aggregated": 24},
        "cpu/power": {"observations": [11, 12, 13], "aggregated": None},
        "resources-reserved": {"observations": [14, 15, 16], "aggregated": None},
        "memory/energy": {"observations": [17, 18, 19], "aggregated": 54},
    }

    compute_resource = ComputeResource(id="test_id")
    MetricsMapper.map_metrics_to_resource(metrics, compute_resource)

    assert compute_resource.carbon_emitted == [10, 20, 30]
    assert compute_resource.total_carbon_emitted == 60
    assert compute_resource.energy_consumed == [5, 15, 25]
    assert compute_resource.total_energy_consumed == 45
    assert compute_resource.carbon_embodied == [1, 2, 3]
    assert compute_resource.total_carbon_embodied == 6
    assert compute_resource.carbon_operational == [4, 5, 6]
    assert compute_resource.total_carbon_operational == 15
    assert compute_resource.cpu_energy == [7, 8, 9]
    assert compute_resource.memory_energy == [17, 18, 19]
    assert compute_resource.total_cpu_energy == 24
    assert compute_resource.cpu_power == [11, 12, 13]
    assert compute_resource.requested_cpu == [14, 15, 16]


def test_map_metrics_to_vm():
    """
    Tests if the metrics are correctly mapped to the virtual machine
    """

    metrics = {
        "storage/energy": {"observations": [20, 21, 22], "aggregated": 63},
        "storage-embodied": {"observations": [23, 24, 25], "aggregated": 72},
    }

    virtual_machine = VirtualMachine(id="test_id")
    MetricsMapper.map_metrics_to_resource(metrics, virtual_machine)

    assert virtual_machine.storage_energy == [20, 21, 22]
    assert virtual_machine.total_storage_energy == 63
    assert virtual_machine.storage_embodied == [23, 24, 25]
    assert virtual_machine.total_storage_embodied == 72


def test_map_metrics_to_storage_resource():
    """
    Tests if the storage-specific metrics are correctly mapped to the storage resource
    """
    metrics = {
        "carbon": {"observations": [10, 20, 30], "aggregated": 60},
        "energy": {"observations": [5, 15, 25], "aggregated": 45},
        "storage/energy": {"observations": [20, 21, 22], "aggregated": 63},
        "storage-embodied": {"observations": [23, 24, 25], "aggregated": 72},
    }

    storage_resource = StorageResource(
        id="test_id", storage_type="SSD", replication_type="LRS", size_gb=128.0
    )
    MetricsMapper.map_metrics_to_resource(metrics, storage_resource)

    # Base resource fields
    assert storage_resource.carbon_emitted == [10, 20, 30]
    assert storage_resource.total_carbon_emitted == 60
    assert storage_resource.energy_consumed == [5, 15, 25]
    assert storage_resource.total_energy_consumed == 45

    # Storage-specific fields
    assert storage_resource.storage_energy == [20, 21, 22]
    assert storage_resource.total_storage_energy == 63
    assert storage_resource.storage_embodied == [23, 24, 25]
    assert storage_resource.total_storage_embodied == 72


def test_map_metrics_to_cost_resource():
    """
    Tests if the cost-specific metrics are correctly mapped to the cost resource
    """
    metrics = {
        "services-energy": {"observations": [50], "aggregated": 50},
        "services-operational": {"observations": [60], "aggregated": 60},
        "services-embodied": {"observations": [70], "aggregated": 70},
    }

    cost_resource = MiscServicesResource(id="test_id")
    MetricsMapper.map_metrics_to_resource(metrics, cost_resource)

    assert cost_resource.services_energy == [50]
    assert cost_resource.total_energy_consumed == 50
    assert cost_resource.services_operational == [60]
    assert cost_resource.total_carbon_operational == 60
    assert cost_resource.services_embodied == [70]
    assert cost_resource.total_carbon_embodied == 70
