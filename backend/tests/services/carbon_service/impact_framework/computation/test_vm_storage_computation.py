# pylint: disable=redefined-outer-name
"""
This file contains tests that check if the IF pipelines for VMs correctly compute the storage energy and embodied
emissions.
"""

import pytest

from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.impact_framework.service.if_vm_service import (
    IFVMService,
)
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_storage_energy,
    compute_embodied_carbon,
)

SAMPLING_RATE_IN_SECONDS = 1800  # 30 min


@pytest.fixture
def sample_vms():
    """Fixture: Returns a sample list of virtual machines."""
    return [
        VirtualMachine(
            id="0",
            provider="azure",
            time_points=["2021-01-01T00:00:00Z"],
            cpu_util=[0.3],
            vm_size="Standard_A1_v2",
            storage_size=[128.0],
        )
    ]


def test_storage_energy_computation_for_virtual_machines(sample_vms):
    """
    Test: Verifies storage energy computation for a single virtual machine.
    """
    expected_storage_energy = round(
        compute_storage_energy(sample_vms[0].storage_size[0], 1), 4
    )
    service = IFVMService(SAMPLING_RATE_IN_SECONDS)
    vms = service.run_engine(sample_vms)

    assert len(vms) == 1
    assert vms[0].storage_energy[0] == pytest.approx(expected_storage_energy, rel=1e-4)


def test_storage_embodied_emissions_for_virtual_machines(sample_vms):
    """
    Test: Verifies that the computation of storage-specific embodied emissions is correct.
    """
    expected_storage_embodied = round(
        compute_embodied_carbon(0, 1, sample_vms[0].storage_size[0], 1), 4
    )
    service = IFVMService(SAMPLING_RATE_IN_SECONDS * 2)
    vms = service.run_engine(sample_vms)

    assert len(vms) == 1
    assert vms[0].storage_embodied[0] == pytest.approx(
        expected_storage_embodied, rel=1e-4
    )
