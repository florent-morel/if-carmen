"""
This module provides services for retrieving and processing data from Thanos,
a system for collecting, storing, and querying time series data.
Note: This module requires access to Thanos for data retrieval.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TypeVar, Callable
import numpy as np

from backend.src.schemas.application import Application
from backend.src.schemas.cluster import Cluster
from backend.src.api.dependencies import AppDao
from backend.src.common.enums import Label, HardwareConsumptionType, SamplingRate
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.utils.helpers import (
    return_desired_metric_from_response,
    group_clusters_by_level,
    get_timestamps,
)
from backend.src.schemas.pod import Pod
from backend.src.common.errors import ErrorCode
from backend.src.common.carmen_exception import DataFetchError
from backend.src.crud.prometheus_query_builder import PromQBuilder
from backend.src.core.yaml_config_loader import config
from backend.src.core.settings import settings


from backend.src.core.settings.providers.abstract_provider_config import (
    AbstractProviderConfig,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=ComputeResource)


class ArgosService:
    """
    Service class to interact with Thanos for retrieving app pods and related data.
    """

    def __init__(self) -> None:
        self.external_labels = config.carmen_api.external_labels
        provider = config.carmen_api.provider if config.carmen_api else None
        self.provider_config = config.provider_configs.get(provider or "")
        self.labels = config.carmen_api.labels
        self.resource_label_value = lambda resources: (
            "|".join(resources) if resources else ".*"
        )

    async def exec_query_for_compute_resource(
        self, compute_resource_label: str, extra_labels: dict[str, str] = None
    ) -> list:
        """
        Executes a query to retrieve the compute resource data from Thanos.

        Args:
            compute_resource_label (str): The label to group the compute resource data by.
            :param extra_labels: additional labels to filter the query.
        """
        extra_labels = extra_labels or {}
        query = (
            PromQBuilder()
            .metric("kube_namespace_labels", **{**self.external_labels, **extra_labels})
            .group_by(compute_resource_label)
            .build()
        )
        response = await AppDao.exec_query(query, time_series=False)
        compute_resources = return_desired_metric_from_response(
            response, compute_resource_label
        )
        return compute_resources

    async def get_available_resources(
        self, applications: list[str] = None, clusters: list[str] = None
    ) -> dict[str, list[str]]:
        """
        Retrieve a dictionary of available resources (app, clusters or namespace).
        """
        available_resources: dict[str, list[str]] = {}
        extra_labels = {}
        if applications:
            extra_labels[self.labels.app_label] = "|".join(applications)
        if clusters:
            extra_labels[self.labels.cluster_label] = "|".join(clusters)
        if not applications and not clusters:
            logger.info("Retrieving applications and clusters from Thanos...")
            available_resources[
                "applications"
            ] = await self.exec_query_for_compute_resource(self.labels.app_label)
            available_resources[
                "clusters"
            ] = await self.exec_query_for_compute_resource(self.labels.cluster_label)
            return available_resources
        if not clusters:
            logger.info("Retrieving clusters from Thanos...")
            clusters = await self.exec_query_for_compute_resource(
                self.labels.cluster_label, extra_labels
            )
            available_resources["clusters"] = clusters

            logger.info("Retrieving namespaces from Thanos...")
            extra_labels[self.labels.cluster_label] = "|".join(clusters)
            available_resources[
                "namespaces"
            ] = await self.exec_query_for_compute_resource(
                self.labels.namespace_label, extra_labels
            )
        else:
            logger.info("Retrieving namespaces from Thanos...")
            available_resources[
                "namespaces"
            ] = await self.exec_query_for_compute_resource(
                self.labels.namespace_label, extra_labels
            )
        return available_resources

    async def retrieve_telemetry_data(
        self,
        interval_start: datetime,
        interval_end: datetime,
        sampling_rate: SamplingRate,
        clusters: list,
        applications: list = None,
        namespaces: list = None,
    ) -> list[Cluster | Application]:
        # The UI sends all available resources because it already knows which ones are available thanks to the
        # get_available_resources endpoint.
        """
        Retrieve a list of pod objects within the specified time range according to the selected resources (cluster,
        app, or namespace).

        Args:
            interval_start: Start date for the query. YYYY-mm-dd HH:MM:SS
            interval_end: End date for the query. YYYY-mm-dd HH:MM:SS
            applications: Optional list of application names.
            sampling_rate: Sampling rate. Available values : 15s, 30s, 1m, 5m, 30m, 1h, 6h, 1d
            clusters: List of clusters names.
            namespaces: Optional list of namespaces.

        Returns:
            list[Pod]: List of pods.
        """

        start_time = time.time()
        tasks = [
            (
                lambda applications, clusters, namespaces: (
                    f"({self.cpu_used_cores()(applications, clusters, namespaces)}) / "
                    f"({self.resource_query('cpu')(applications, clusters, namespaces)})"
                ),
                HardwareConsumptionType.CPU_UTIL,
            ),
            (self.resource_query("cpu"), HardwareConsumptionType.REQUESTED_CORES),
            (self.resource_query("memory"), HardwareConsumptionType.REQUESTED_BYTES),
        ]

        interp_pod_telemetries = {}

        # commented out for now, as it is not viewed as expected in the UI. Now, it is similar to the grafana graphs
        # interval_end = subtract_last_time_point(interval_end, sampling_rate)
        desired_timestamps = get_timestamps(interval_start, interval_end, sampling_rate)
        clusters = group_clusters_by_level(
            clusters, settings.THANOS.CLUSTER_GROUPING_LEVEL
        )
        for cluster_group in clusters:
            logger.info("Retrieving data for cluster(s): %s", cluster_group)
            try:
                for query, consumption_type in tasks:
                    pod_data = await AppDao.exec_query(
                        query(applications, cluster_group, namespaces),
                        interval_start,
                        interval_end,
                        sampling_rate.value,
                    )
                    logger.info(
                        "Parsing %s pod data. Number of data points: %d",
                        consumption_type.value,
                        len(pod_data),
                    )
                    interp_pod_telemetries = await ArgosService().parse_pod_data(
                        pod_data,
                        interp_pod_telemetries,
                        desired_timestamps,
                        consumption_type,
                    )
            except DataFetchError as ex:
                logging.error(
                    "Failed to retrieve hardware consumption data due to the following error: %s\n"
                    "Skipped cluster(s): %s",
                    ex.formatted_string,
                    cluster_group,
                )

        logger.info(
            "Data retrieval completed in %d seconds.", round(time.time() - start_time)
        )

        # Filter out pods that do not report at least one hardware metric data
        pod_telemetries = [
            pod
            for pod in interp_pod_telemetries.values()
            if pod.requested_cpu and pod.requested_memory and pod.cpu_util
        ]

        if not pod_telemetries:
            raise DataFetchError(
                ErrorCode.DATA_FETCH_NO_RESULTS,
                source="ArgosService",
                details="no pods found after filtering telemetry data",
            )

        logger.info("Number of pods after filtering: %d", len(pod_telemetries))

        if applications:
            return ArgosService.split_pods_by_resource(
                pod_telemetries,
                key=lambda pod: pod.app,
                factory=lambda key, pods, idx: ArgosService.create_resource(
                    Application, key, pods, idx, desired_timestamps
                ),
            )
        return ArgosService.split_pods_by_resource(
            pod_telemetries,
            key=lambda pod: pod.paas,
            factory=lambda key, pods, idx: ArgosService.create_resource(
                Cluster, key, pods, idx, desired_timestamps
            ),
        )

    async def parse_pod_data(
        self,
        pod_data: list[dict[str, dict | list]],
        pod_telemetries: dict[str, Pod],
        desired_timestamps: list[datetime],
        consumption_type: HardwareConsumptionType,
    ) -> dict[str, Pod]:
        """
        Parses the pod data retrieved from Thanos.
        Args:
            pod_data: List of the pod data retrieved from Thanos.
            pod_telemetries: A dictionary containing parsed pod data, where the key is the Pod's id.
            desired_timestamps: A list of datetime objects at the specified intervals from start to end.
            consumption_type: Hardware consumption type indicating if resources are requested/used/cpu/memory

        Returns:
            Dict[str, Pod]: Parsed pods.
        """

        for data in pod_data:
            uid = data["metric"][Label.UID.value]
            app = data["metric"][Label.SERVICE.value]
            paas = data["metric"][Label.PAAS.value]
            namespace = data["metric"][Label.NAMESPACE.value]
            pod = data["metric"][Label.POD.value]
            carbon_intensity = PaasCiMapper.get_ci_from_paas(paas)

            pod_telemetries.setdefault(
                uid,
                Pod(
                    id=uid,
                    app=app,
                    paas=paas,
                    namespace=namespace,
                    name=pod,
                    carbon_intensity=carbon_intensity,
                    pue=self.provider_config.get_pue()
                    if self.provider_config
                    else config.defaults.pue,
                    time_points=desired_timestamps,
                ),
            )
            values_list = [float(value[1]) for _, value in enumerate(data["values"])]
            time_points = [value[0] for _, value in enumerate(data["values"])]

            if len(time_points) < len(desired_timestamps):
                # apply interpolation
                values_list = ArgosService.interpolate_field_data(
                    desired_timestamps,
                    np.array(time_points),
                    np.array(values_list),
                )

            if consumption_type == HardwareConsumptionType.CPU_UTIL:
                pod_telemetries[uid].cpu_util = values_list
            elif consumption_type == HardwareConsumptionType.REQUESTED_CORES:
                pod_telemetries[uid].requested_cpu = values_list
            elif consumption_type == HardwareConsumptionType.REQUESTED_BYTES:
                pod_telemetries[uid].requested_memory = values_list
            elif consumption_type == HardwareConsumptionType.STORAGE_CAPACITY_BYTES:
                pod_telemetries[uid].storage_capacity = values_list

        return pod_telemetries

    @staticmethod
    def interpolate_field_data(
        desired_ts: list[datetime], pod_ts: np.ndarray, values: np.array
    ) -> list[float]:
        """
        Interpolates the data for a specific field of a pod onto new timestamps.

        Args:
            values: The hardware values to interpolate (e.g., 'requested_cpu').
            desired_ts: A numpy array of the desired timepoints (timestamps).
            pod_ts: A numpy array of the pod's original timepoints (timestamps).

        Returns:
            A numpy array of interpolated values.
        """
        # UTC+1 timezone
        desired_ts_float = np.array(
            [(t + timedelta(hours=1)).timestamp() for t in desired_ts]
        )

        return np.interp(desired_ts_float, pod_ts, values).tolist()

    @staticmethod
    def split_pods_by_resource(
        pods: list[Pod],
        key: Callable[[Pod], str],
        factory: Callable[[str, list[Pod], int], T],
    ) -> list[T]:
        """
        Groups pods by an arbitrary key and creates resource objects using a factory function.

        Args:
            pods: List of Pod objects.
            key: Function to extract the grouping key from a Pod (e.g. lambda pod: pod.app).
            factory: Function to create the resource from (group_key, pods, index).

        Returns:
            List of resource objects.
        """
        groups = defaultdict(list)
        for pod in pods:
            groups[key(pod)].append(pod)
        result = [
            factory(group_key, group, idx)
            for idx, (group_key, group) in enumerate(groups.items())
        ]
        return result

    @staticmethod
    def create_resource(
        resource_cls: type[T],
        resource_key: str,
        pods: list[Pod],
        idx: int,
        desired_timestamps: list[datetime],
    ) -> T:
        """
        Creates a resource (Application or Cluster) by aggregating hardware usage data from a list of pods.

        Args:
            resource_cls: The class (Application or Cluster) to instantiate.
            resource_key: The grouping key for the resource's 'name' field.
            pods: List of Pod objects.
            idx: An index for the resource's 'id' field.
            desired_timestamps: A list of datetime objects at the specified intervals from start to end.

        Returns:
            An instance of cls with aggregated data.
        """
        resource = resource_cls(
            id=str(idx), name=resource_key, pods=pods, time_points=desired_timestamps
        )
        # Aggregate the fields
        resource.requested_cpu = np.sum(
            np.array([pod.requested_cpu for pod in pods]), axis=0
        ).tolist()
        resource.requested_memory = np.sum(
            np.array([pod.requested_memory for pod in pods]), axis=0
        ).tolist()
        resource.cpu_util = np.mean(
            np.array([pod.cpu_util for pod in pods]), axis=0
        ).tolist()
        return resource

    def cpu_used_cores(self) -> callable:
        """
        Returns a function that builds a Prometheus query to compute the CPU cores used
        by specific applications in given clusters and namespaces.
        Returns:
            callable: A function that accepts applications, clusters, and namespaces as lists
                    and returns a PromQL query string.
        """

        def build_query(applications: list, clusters: list, namespaces: list) -> str:
            """
            Constructs a PromQL query string to measure CPU usage per application.

            Args:
                applications (list): List of application identifiers.
                clusters (list): List of cluster identifiers.
                namespaces (list): List of namespace identifiers.

            Returns:
                str: A PromQL query string for CPU usage.
            """
            usage_match_labels = {
                **self.external_labels,
                self.labels.cluster_label: self.resource_label_value(clusters),
                self.labels.namespace_label: self.resource_label_value(namespaces),
            }

            pod_match_labels = {
                self.labels.cluster_label: self.resource_label_value(clusters),
                self.labels.namespace_label: self.resource_label_value(namespaces),
                self.labels.app_label: self.resource_label_value(applications),
            }

            usage_query = (
                PromQBuilder()
                .metric("pod:container_cpu_usage:sum", **usage_match_labels)
                .sum_by(
                    self.labels.cluster_label,
                    self.labels.namespace_label,
                    self.labels.pod_label,
                )
            )

            pod_query = PromQBuilder().metric("kube_pod_labels", **pod_match_labels)

            full_query = usage_query.op(
                "*",
                pod_query,
                on=[
                    self.labels.namespace_label,
                    self.labels.cluster_label,
                    self.labels.pod_label,
                ],
                grouping_side="left",
                grouping_labels=[self.labels.app_label, "uid"],
            ).build()

            return full_query

        return build_query

    def resource_query(self, resource: str) -> callable:
        """
        Returns a function that builds a Prometheus query to retrieve resource request data
        for a given resource type (e.g., CPU, memory) across applications, clusters, and namespaces.
        Args:
            resource (str): The resource type to query (e.g., "cpu", "memory").
        Returns:
            callable: A function that accepts applications, clusters, and namespaces as lists
                    and returns a PromQL query string.
        """

        def build_query(applications: list, clusters: list, namespaces: list) -> str:
            """
            Constructs a PromQL query string to measure resource requests.

            Args:
                applications (list): List of application identifiers.
                clusters (list): List of cluster identifiers.
                namespaces (list): List of namespace identifiers.

            Returns:
                str: A PromQL query string for resource requests.
            """
            base_labels = {
                self.labels.cluster_label: self.resource_label_value(clusters),
                self.labels.namespace_label: self.resource_label_value(namespaces),
                self.labels.app_label: self.resource_label_value(applications),
            }
            lhs = (
                PromQBuilder()
                .metric(
                    "kube_pod_container_resource_requests",
                    **{
                        **self.external_labels,
                        self.labels.cluster_label: self.resource_label_value(clusters),
                        self.labels.namespace_label: self.resource_label_value(
                            namespaces
                        ),
                        "resource": resource,
                    },
                )
                .sum_by("uid")
            )
            rhs = PromQBuilder().metric("kube_pod_labels", **base_labels)
            query = lhs.op(
                "*",
                rhs,
                on=["uid"],
                grouping_side="left",
                grouping_labels=[
                    self.labels.app_label,
                    self.labels.namespace_label,
                    self.labels.cluster_label,
                    self.labels.pod_label,
                ],
            ).build()
            return query

        return build_query
