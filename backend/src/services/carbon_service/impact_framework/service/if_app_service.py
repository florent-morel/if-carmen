"""
This module defines the Impact Framework service class, which implements the IFService interface.
It provides functionality to compute carbon and energy metrics for pods using IF models.
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Any
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.schemas.application import Application
from backend.src.services.carbon_service.impact_framework.models.power.p_cores import (
    PCores,
)
from backend.src.services.carbon_service.impact_framework.models.power.p_mem import PMem
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_m_cpu import (
    SciMcpu,
)
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)
from backend.src.schemas.pod import Pod


class IFAppService(IFService):
    """
    This class implements the IFService abstract class and provides functionality to compute
    carbon and energy metrics for applications using IF models
    """

    def __init__(self, duration):
        super().__init__("app_template.yml.j2", "app_pipeline.yml", "both", duration)

    async def run_engine(
        self,
        compute_resources: List[ComputeResource],
        emission_breakdown_at_pod_level=False,
    ) -> List[ComputeResource] | Dict[str, Dict[str, Dict[str, List[Pod]]]]:
        """
        Executes the Impact Framework (IF) model to compute energy and CO2 metrics for a list of pods,
        returning the results at the application level or pod level.

        Args:
            compute_resources (List[ComputeResource]): A list of apps or clusters for which the metrics are to
                be computed.
            emission_breakdown_at_pod_level (bool, optional): If True, metrics are computed at the pod level.
                                              Defaults to application-level granularity.

        Returns:
            List[ComputeResource]: A list of applications with updated energy consumption and carbon emission metrics
            computed at application level.
            Dict[str, Dict[str, Dict[str, List[Pod]]]]: Dictionary of data for each pod of selected cluster, app and
            namespace at pod level.
        """

        self.run_if(compute_resources)
        output = self.parse_if_output(
            compute_resources, emission_breakdown_at_pod_level
        )
        return output

    def get_resource_data(self, data, compute_resources: List[Application]):
        """
        Fills the application dictionary with pod data required for the template
        """
        resources: Dict[str, Dict[str, Any]] = defaultdict(dict)
        for compute_resource in compute_resources:
            pod_data = {}
            for pod in compute_resource.pods:
                pod_data[pod.id] = self.get_resource_inputs(pod)
            resources[compute_resource.id] = pod_data
        data["resources"] = resources

    @staticmethod
    def get_resource_inputs(pod: Pod, models: Tuple[ModelUtilities] = (SciMcpu, PMem)):
        """
        Generates input data for each time point of a compute unit using the specified models.

        Args:
            pod (Pod): The pod to process.
            models (Tuple[ModelUtilities], optional): Additional models to include in the input generation.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing inputs for each time point.
        """
        return IFService.get_resource_inputs(pod, models)

    def get_models_info(self, data, provider: str = "azure"):
        """
        Concrete method that fills the model dictionary with basic model information depending on the defined
        pipeline.

        This is a concrete method in the IFService abstract class because it is commonly shared between
        the two types of IF services as of (21/05/2024).
        """
        super().get_models_info(data, provider)
        if "p-cores" in data["hardware_models"]:
            data["hardware_models"]["p-cores"] = PCores().__dict__
