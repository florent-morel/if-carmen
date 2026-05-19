"""
Impact Framework service for Misc Services model - extends IFService
"""
import concurrent
import logging
from typing import List

from backend.src.schemas.resource import Resource
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.services.carbon_service.impact_framework.models.carbon.misc_services import (
    MiscServicesModel,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)

logger = logging.getLogger(__name__)


class IFMiscServicesService(IFService):
    """
    Specialized Impact Framework service for Misc Services model
    """

    def __init__(self, duration):
        super().__init__(
            "misc_services_template.yml.j2",
            "misc_services_pipeline.yml",
            "horizontal",
            duration,
        )

    def run_engine(
        self,
        misc_services_resources: List[MiscServicesResource],
    ) -> List[MiscServicesResource]:
        """
        Executes the Impact Framework (IF) model to estimate impact for misc resources.
        """
        # Divide into chunks
        # TODO: Magic number
        chunk_size = 10000

        chunks = [
            misc_services_resources[x: x + chunk_size]
            for x in range(0, len(misc_services_resources), chunk_size)
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

        return misc_services_resources

    def get_models_info(self, data, provider: str = ""):
        """
        Load misc_services-specific models
        """
        super().get_models_info(data, provider)

        if "misc_services-model" in data["hardware_models"]:
            data["hardware_models"][
                "misc_services-model"
            ] = MiscServicesModel().__dict__

    @staticmethod
    def get_resource_inputs(
        misc_services_resource: MiscServicesResource,
        model: ModelUtilities = MiscServicesModel,
    ):
        """
        Get Misc Services model specific inputs
        """
        resource_inputs = []
        for time_index in range(len(misc_services_resource.time_points)):
            combined_inputs = {
                key: value
                for key, value in model.fill_inputs(
                    misc_services_resource, time_index
                ).items()
            }
            resource_inputs.append(combined_inputs)
        return resource_inputs
