from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.schemas.storage_resource import StorageResource

sample_vms = [
    VirtualMachine(
        id="vm1",
        name="test_vm_1",
        component="component_1",
        provider="azure",
        region="region_1",
        subscription="subscription_1",
        vm_size="size_1",
        service="service_1",
        instance="instance_1",
        environment="environment_1",
        partition="partition_1",
        total_energy_consumed=100.0,
        total_carbon_operational=100.0,
        total_carbon_embodied=100.0,
        total_carbon_emitted=200.0,
        carbon_intensity=281.0,
    )
]

sample_storage_resources = [
    StorageResource(
        id="storage1",
        name="test_premium_ssd",
        provider="azure",
        storage_type="Premium_SSD",
        replication_type="LRS",
        size_gb=128.0,
        region="francecentral",
        subscription="test_subscription",
        carbon_intensity=250.0,
        total_energy_consumed=50.0,
        total_carbon_operational=100.0,
        total_carbon_embodied=25.0,
        total_carbon_emitted=125.0,
    ),
    StorageResource(
        id="storage2",
        name="test_standard_hdd",
        provider="azure",
        storage_type="Standard_HDD",
        replication_type="GRS",
        size_gb=500.0,
        region="germanywestcentral",
        subscription="test_subscription",
        carbon_intensity=381.0,
        total_energy_consumed=75.0,
        total_carbon_operational=150.0,
        total_carbon_embodied=30.0,
        total_carbon_emitted=180.0,
    ),
]
