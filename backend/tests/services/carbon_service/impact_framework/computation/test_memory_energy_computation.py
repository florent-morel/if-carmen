# pylint: disable=redefined-outer-name
"""
Test: Memory Energy Computation for Applications
"""
import pytest

from backend.src.schemas.application import Application
from backend.src.schemas.pod import Pod
from backend.src.services.carbon_service.impact_framework.service.if_app_service import (
    IFAppService,
)
from backend.tests.services.carbon_service.impact_framework.computation.computation_helpers import (
    compute_memory_energy,
)
from backend.tests.services.carbon_service.impact_framework.computation.test_cpu_energy_computation import (
    SAMPLING_RATE_IN_SECONDS,
)


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
            requested_cpu=[0.116],
            requested_memory=[32637906964.0],
            carbon_intensity=291.0,
        ),
        Pod(
            id="1",
            name="pod2",
            time_points=["2021-01-01T00:00:00Z"],
            cpu_util=[0.4],
            app="app1",
            paas="paas1",
            namespace="namespace1",
            requested_cpu=[0.116],
            requested_memory=[32637906964.0],
            carbon_intensity=291.0,
        ),
        Pod(
            id="2",
            name="pod3",
            time_points=["2021-01-01T00:00:00Z"],
            cpu_util=[0.6],
            app="app1",
            paas="paas2",
            namespace="namespace1",
            requested_cpu=[0.116],
            requested_memory=[32637906964.0],
            carbon_intensity=291.0,
        ),
    ]


@pytest.fixture
def sample_app(sample_pods):
    """
    Mock Application list.
    """
    app = Application(id="app1", name="app1", pods=sample_pods)
    return [app]


@pytest.mark.asyncio
async def test_memory_energy_computation_for_apps(sample_app):
    """
    Test: Verifies memory energy computation for an app.
    """
    memory_requested = (
        sum(pod.requested_memory[0] for pod in sample_app[0].pods) / 1000000000
    )  # memory in GB
    expected_result = (
        compute_memory_energy(memory_requested, SAMPLING_RATE_IN_SECONDS) / 3600
    )
    service = IFAppService(SAMPLING_RATE_IN_SECONDS)
    apps = await service.run_engine(sample_app)
    assert len(apps) == 1
    assert apps[0].memory_energy[0] == pytest.approx(expected_result, rel=1e-4)
