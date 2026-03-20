# pylint: disable=redefined-outer-name
"""
This module contains tests for various functionalities the Argos class.
"""
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta

import numpy as np
import pytest
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import DataFetchError
from backend.src.schemas.application import Application
from backend.src.schemas.cluster import Cluster

from backend.src.services.argos_service import ArgosService
from backend.src.schemas.pod import Pod
from backend.src.common.enums import HardwareConsumptionType, Label, SamplingRate
from backend.tests.services.carbon_service.impact_framework.computation.test_cpu_energy_computation import (
    sample_pods,
)

# Sample response mocks
APPLICATIONS_RESPONSE = [
    {"metric": {"service": "app1"}},
    {"metric": {"service": "app2"}},
]
CLUSTERS_RESPONSE = [{"metric": {"paas": "cluster1"}}, {"metric": {"paas": "cluster2"}}]
NAMESPACES_RESPONSE = [
    {"metric": {"namespace": "namespace1"}},
    {"metric": {"namespace": "namespace2"}},
]


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query")
@patch("backend.src.services.argos_service.return_desired_metric_from_response")
async def test_get_available_resources_no_args(
    mock_return_desired_metric, mock_exec_query
):
    """
    Test when both applications and clusters are None.
    """
    mock_exec_query.side_effect = [APPLICATIONS_RESPONSE, CLUSTERS_RESPONSE]
    mock_return_desired_metric.side_effect = [
        ["app1", "app2"],
        ["cluster1", "cluster2"],
    ]

    result = await ArgosService().get_available_resources()

    assert result == {
        "applications": ["app1", "app2"],
        "clusters": ["cluster1", "cluster2"],
    }


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query")
@patch("backend.src.services.argos_service.return_desired_metric_from_response")
async def test_get_available_resources_with_apps_and_clusters(
    mock_return_desired_metric, mock_exec_query
):
    """
    Test when both applications and clusters are provided.
    """
    mock_exec_query.return_value = NAMESPACES_RESPONSE
    mock_return_desired_metric.return_value = ["namespace1", "namespace2"]

    applications = ["app1"]
    clusters = ["cluster1"]
    result = await ArgosService().get_available_resources(applications, clusters)
    assert result == {
        "namespaces": ["namespace1", "namespace2"],
    }


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query")
@patch("backend.src.services.argos_service.return_desired_metric_from_response")
async def test_get_available_resources_with_apps_only(
    mock_return_desired_metric, mock_exec_query
):
    """
    Test when only applications are provided.
    """
    mock_exec_query.side_effect = [CLUSTERS_RESPONSE, NAMESPACES_RESPONSE]
    mock_return_desired_metric.side_effect = [
        ["cluster1", "cluster2"],
        ["namespace1", "namespace2"],
    ]

    applications = ["app1"]

    result = await ArgosService().get_available_resources(applications)

    assert result == {
        "clusters": ["cluster1", "cluster2"],
        "namespaces": ["namespace1", "namespace2"],
    }


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query")
@patch("backend.src.services.argos_service.return_desired_metric_from_response")
async def test_get_available_resources_with_clusters_only(
    mock_return_desired_metric, mock_exec_query
):
    """
    Test when only clusters are provided.
    """
    mock_exec_query.return_value = NAMESPACES_RESPONSE
    mock_return_desired_metric.return_value = ["namespace1", "namespace2"]

    clusters = ["cluster1"]

    result = await ArgosService().get_available_resources(clusters=clusters)
    assert result == {
        "namespaces": ["namespace1", "namespace2"],
    }


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query", new_callable=AsyncMock)
@patch(
    "backend.src.services.argos_service.ArgosService.parse_pod_data",
    new_callable=AsyncMock,
)
async def test_retrieve_telemetry_data_success(mock_parse_pod_data, mock_exec_query):
    """
    Test successful retrieval and parsing of pod telemetries.
    """
    start = datetime.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime("2023-01-01 02:0:00", "%Y-%m-%d %H:%M:%S")
    sampling_rate = SamplingRate.ONE_HOUR
    clusters = ["cluster1", "cluster2"]
    applications = ["app1", "app2"]
    namespaces = ["namespace1"]

    mock_exec_query.return_value = [
        {"metric": {"pod": "pod1", "values": [[1, "0.5"], [2, "0.6"]]}}
    ]

    mock_parse_pod_data.side_effect = (
        lambda pod_data, pod_telemetries, desired_timestamps, consumption_type: {
            "pod1": Pod(
                id="pod1",
                app="app1",
                paas="paas1",
                namespace="namespace1",
                time_points=[
                    datetime.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2023-01-01 01:00:00", "%Y-%m-%d %H:%M:%S"),
                ],
                cpu_util=[0.5, 0.6],
                requested_cpu=[0.5, 0.6],
                requested_memory=[0.5, 0.6],
            )
        }
    )
    result = await ArgosService().retrieve_telemetry_data(
        start, end, sampling_rate, clusters, applications, namespaces
    )
    result = result[0].pods
    assert len(result) == 1
    assert isinstance(result[0], Pod)
    assert result[0].id == "pod1"
    assert (
        len(result[0].cpu_util)
        == len(result[0].requested_cpu)
        == len(result[0].requested_memory)
    )

    mock_exec_query.assert_called()
    mock_parse_pod_data.assert_called()


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query", new_callable=AsyncMock)
@patch(
    "backend.src.services.argos_service.ArgosService.parse_pod_data",
    new_callable=AsyncMock,
)
async def test_retrieve_telemetry_data_no_pods_found(
    mock_parse_pod_data, mock_exec_query
):
    """
    Test the case where no pods are found after filtering.
    """
    start = datetime.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime("2023-01-02 00:00:00", "%Y-%m-%d %H:%M:%S")
    sampling_rate = SamplingRate.ONE_HOUR
    clusters = ["cluster1"]

    mock_exec_query.return_value = [
        {"metric": {"pod": "pod1", "values": [[1, "0.5"], [2, "0.6"]]}}
    ]

    mock_parse_pod_data.side_effect = (
        lambda pod_data, pod_telemetries, desired_timestamps, consumption_type: {
            "pod1": Pod(
                id="pod1",
                app="app1",
                paas="paas1",
                namespace="namespace1",
                cpu_util=[0.5, 0.6],
            )
        }
    )

    with pytest.raises(DataFetchError) as exc_info:
        await ArgosService().retrieve_telemetry_data(
            start, end, sampling_rate, clusters
        )


@pytest.mark.asyncio
@patch("backend.src.services.argos_service.AppDao.exec_query", new_callable=AsyncMock)
@patch(
    "backend.src.services.argos_service.ArgosService.parse_pod_data",
    new_callable=AsyncMock,
)
async def test_retrieve_telemetry_data_exception_handling(
    mock_parse_pod_data, mock_exec_query
):
    """
    Test the case where a KnownException is raised during hardware consumption data retrieval.
    """
    start = datetime.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime("2023-01-02 00:00:00", "%Y-%m-%d %H:%M:%S")
    sampling_rate = SamplingRate.ONE_HOUR
    clusters = ["cluster1", "cluster2"]

    mock_exec_query.side_effect = DataFetchError(
        ErrorCode.DATA_FETCH_FAILED,
        source="Thanos",
        details="Hardware consumption data retrieval failed.",
    )

    with pytest.raises(DataFetchError) as exc_info:
        await ArgosService().retrieve_telemetry_data(
            start, end, sampling_rate, clusters
        )

    assert "no pods found" in exc_info.value.formatted_string.lower()

    mock_exec_query.assert_called()
    mock_parse_pod_data.assert_not_called()


@pytest.mark.asyncio
@patch(
    "backend.src.services.argos_service.ArgosService.interpolate_field_data",
    return_value=[0.5, 0.6],
)
@patch(
    "backend.src.services.argos_service.PaasCiMapper.get_ci_from_paas", return_value=368
)
async def test_parse_pod_data(mock_get_ci, mock_interpolate):
    """
    Test the parse_pod_data method.
    """
    pod_data = [
        {
            "metric": {
                Label.SERVICE.value: "app1",
                Label.PAAS.value: "paas1",
                Label.NAMESPACE.value: "namespace1",
                Label.POD.value: "pod1",
                Label.UID.value: "uid1",
            },
            "values": [[1, "0.5"], [2, "0.6"]],
        }
    ]
    pod_telemetries = {}

    consumption_type = HardwareConsumptionType.CPU_UTIL

    result = await ArgosService().parse_pod_data(
        pod_data,
        pod_telemetries,
        [datetime(2023, 1, 2, 12), datetime(2023, 1, 2, 13)],
        consumption_type,
    )

    assert "uid1" in result
    assert result["uid1"].id == "uid1"
    assert result["uid1"].app == "app1"
    assert result["uid1"].paas == "paas1"
    assert result["uid1"].namespace == "namespace1"
    assert result["uid1"].cpu_util == [0.5, 0.6]


def test_interpolate_field_data():
    """
    Test the interpolation of missing telemetry data for a list of pods.
    """
    desired_ts = [
        datetime.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"),
        datetime.strptime("2023-01-01 01:00:00", "%Y-%m-%d %H:%M:%S"),
        datetime.strptime("2023-01-01 02:00:00", "%Y-%m-%d %H:%M:%S"),
    ]
    pod_ts = np.array(
        [
            (
                datetime.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
                + timedelta(hours=1)
            ).timestamp(),
            (
                datetime.strptime("2023-01-01 02:00:00", "%Y-%m-%d %H:%M:%S")
                + timedelta(hours=1)
            ).timestamp(),
        ]
    )
    values = np.array([1.0, 3.0])
    expected = [1.0, 2.0, 3.0]
    result = ArgosService.interpolate_field_data(desired_ts, pod_ts, values)
    assert result == expected


def test_create_resource_application(sample_pods):
    """
    Test the creation of an Application object.
    """
    pods = [pod for pod in sample_pods if pod.app == "app1"]
    application = ArgosService.create_resource(
        Application,
        "app1",
        pods,
        1,
        desired_timestamps=[
            datetime.strptime("2021-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        ],
    )
    assert application.id == "1"
    assert application.name == "app1"
    assert application.pods == pods
    assert application.cpu_util == np.mean(np.array([0.6, 0.3]))
    assert application.requested_cpu == np.array(50)
    assert application.requested_memory == np.array(50)


def test_create_resource_cluster(sample_pods):
    """
    Test the creation of a Cluster object.
    """
    pods = [pod for pod in sample_pods if pod.paas == "paas1"]
    cluster = ArgosService.create_resource(
        Cluster,
        "paas1",
        pods,
        1,
        desired_timestamps=[
            datetime.strptime("2021-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        ],
    )
    assert cluster.id == "1"
    assert cluster.name == "paas1"
    assert cluster.pods == pods
    assert cluster.cpu_util == np.mean(np.array([0.4, 0.3]))
    assert cluster.requested_cpu == np.array(100)
    assert cluster.requested_memory == np.array(50)


def test_split_pods_by_resource_cluster(sample_pods):
    """
    Test splitting pods by cluster.
    """
    clusters = ArgosService.split_pods_by_resource(
        sample_pods,
        lambda pod: pod.paas,
        lambda key, pod, idx: ArgosService.create_resource(
            Cluster,
            key,
            pod,
            idx,
            desired_timestamps=[
                datetime.strptime("2021-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
            ],
        ),
    )
    assert len(clusters) == 2
    assert clusters[0].pods == [pod for pod in sample_pods if pod.paas == "paas1"]
    assert clusters[1].pods == [pod for pod in sample_pods if pod.paas == "paas2"]


def test_split_pods_by_resource_apps(sample_pods):
    """
    Test splitting pods by application.
    """
    applications = ArgosService.split_pods_by_resource(
        sample_pods,
        lambda pod: pod.app,
        lambda key, pod, idx: ArgosService.create_resource(
            Application,
            key,
            pod,
            idx,
            desired_timestamps=[
                datetime.strptime("2021-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
            ],
        ),
    )
    assert len(applications) == 2
    assert applications[0].pods == [pod for pod in sample_pods if pod.app == "app1"]
    assert applications[1].pods == [pod for pod in sample_pods if pod.app == "app2"]
