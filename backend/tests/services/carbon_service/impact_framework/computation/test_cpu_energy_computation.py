# pylint: disable=redefined-outer-name
"""
This file contains tests that check if the IF pipelines for apps and infra correctly compute the CPU energy.
"""

import logging
import numpy as np
import pytest

from backend.src.schemas.application import Application
from backend.src.schemas.pod import Pod
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.impact_framework.service.if_app_service import (
    IFAppService,
)
from backend.src.services.carbon_service.impact_framework.service.if_vm_service import (
    IFVMService,
)
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_tdp_ratio,
    compute_cpu_energy,
)

logger = logging.getLogger(__name__)

# TODO: Magic
SAMPLING_RATE_IN_SECONDS = 1800  # 30 min
TDP_APP = 3.67  # Average watts per core for Azure taken from CCF
# Standard_A1_v2 from azure_instances.csv: cpu-tdp=205 (full host), cores-utilized=1, cores-available=52
# The IF pipeline scales: vm_tdp = cpu-tdp * cores-utilized / cores-available
TDP_VM = 205 * 1.0 / 52.0


def compute_expected_cpu_energy(
    tdp: float, cpu_util: float, requested_cores: float = 1.0
):
    """
    Computes the expected CPU energy consumption based on TDP and CPU utilization.
    If `requested_cores` is provided, assumes TDP is per core.
    """
    tdp_ratio = compute_tdp_ratio(cpu_util)
    cpu_energy = compute_cpu_energy(tdp, tdp_ratio, SAMPLING_RATE_IN_SECONDS) / 3600
    return np.round(cpu_energy * requested_cores, 4)


@pytest.fixture
def sample_pods():
    """Fixture: Returns a sample list of pods."""
    return [
        Pod(
            id="0",
            name="pod1",
            time_points=["2021-01-01T00:00:00Z"],
            cpu_util=[0.3],
            app="app1",
            paas="paas1",
            namespace="namespace1",
            requested_cpu=[50],
            requested_memory=[0.0],
        ),
        Pod(
            id="1",
            name="pod2",
            time_points=["2021-01-01T00:00:00Z"],
            cpu_util=[0.4],
            app="app2",
            paas="paas1",
            namespace="namespace1",
            requested_cpu=[50],
            requested_memory=[50],
        ),
        Pod(
            id="2",
            name="pod3",
            time_points=["2021-01-01T00:00:00Z"],
            cpu_util=[0.6],
            app="app1",
            paas="paas2",
            namespace="namespace1",
            requested_cpu=[0.0],
            requested_memory=[50],
        ),
    ]


@pytest.fixture
def sample_app(sample_pods):
    """
    Mock Application list.
    """
    app = Application(id="app1", name="app1", pods=sample_pods)
    return [app]


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


@pytest.mark.asyncio
async def test_cpu_energy_computation_for_apps(sample_app):
    """
    Test: Verifies CPU energy computation for a single pod.
    """
    expected_result = np.sum(
        [
            compute_expected_cpu_energy(TDP_APP, pod.cpu_util[0], pod.requested_cpu[0])
            for pod in sample_app[0].pods
        ]
    )
    service = IFAppService(SAMPLING_RATE_IN_SECONDS)
    apps = await service.run_engine(sample_app)
    assert len(apps) == 1
    assert apps[0].cpu_energy[0] == pytest.approx(expected_result, rel=1e-4)


def test_cpu_energy_computation_for_virtual_machines(sample_vms):
    """
    Test: Verifies CPU energy computation for a single virtual machine.
    """
    expected_result = compute_expected_cpu_energy(TDP_VM, sample_vms[0].cpu_util[0])
    logger.info(f"sample_vms: {sample_vms}")
    service = IFVMService(SAMPLING_RATE_IN_SECONDS)
    vms = service.run_engine(sample_vms)

    assert len(vms) == 1
    assert vms[0].cpu_energy[0] == pytest.approx(expected_result, rel=1e-4)
