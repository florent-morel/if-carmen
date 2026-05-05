"""
Impact Framework service for cost model - extends IFService
"""
import concurrent
import logging
from typing import List

from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.services.carbon_service.impact_framework.models.carbon.cost import (
    CostModel,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)

logger = logging.getLogger(__name__)


class IFCostService(IFService):
    """
    Specialized Impact Framework service for cost model
    """

    def __init__(self, duration):
        super().__init__(
            "services_template.yml.j2", "services_pipeline.yml", "horizontal", duration
        )

    def run_engine(
        self, cost_resources: List[MiscServicesResource]
    ) -> List[MiscServicesResource]:
        """
        Executes the Impact Framework (IF) model to compute cost metrics for cost resources.
        """
        # Divide into chunks
        chunk_size = 10000

        chunks = [
            cost_resources[x : x + chunk_size]
            for x in range(0, len(cost_resources), chunk_size)
        ]

        def compute_metrics_for_chunk(chunk, index):
            self.run_if(chunk, file_id=index)
            self.parse_if_output(chunk, file_id=index)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(compute_metrics_for_chunk, chunk, i)
                for i, chunk in enumerate(chunks)
            ]
            concurrent.futures.wait(futures)

        return cost_resources

    def get_models_info(self, data, provider: str = ""):
        """
        Load cost-specific models
        """
        super().get_models_info(data, provider)

        if "cost-model" in data["hardware_models"]:
            data["hardware_models"]["cost-model"] = CostModel().__dict__

    @staticmethod
    def get_resource_inputs(
        cost_resource: MiscServicesResource, model: ModelUtilities = CostModel
    ):
        """
        Get cost model specific inputs
        """
        resource_inputs = []
        for time_index in range(len(cost_resource.time_points)):
            combined_inputs = {
                key: value
                for key, value in model.fill_inputs(cost_resource, time_index).items()
            }
            resource_inputs.append(combined_inputs)
        return resource_inputs
