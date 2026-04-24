"""
Cost model to calculate service energy and emissions
"""
from backend.src.common.constants import PLUGIN_PATH
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.services.carbon_service.impact_framework.models.metadata import Metadata
from backend.src.services.carbon_service.impact_framework.models.model_utilities import ModelUtilities


# TODO: rename in Misc Service Model
class CostModel(ModelUtilities):
    """
    Concrete class for the Cost model
    """

    def __init__(self):
        config = {
            "input-parameters": [
                "compute-energy",
                "storage-energy",
                "compute-embodied",
                "storage-embodied",
                "compute-cost",
                "storage-cost",
                "services-cost",
                "carbon-intensity"
            ],
            "output-parameters": [
                "services-energy",
                "services-operational",
                "services-embodied"
            ]
        }
        output_metadata = [
            Metadata(
                "services-energy",
                "kWh",
                "Total energy consumed for the services",
                "sum",
                "sum",
            ),
            Metadata(
                "services-operational",
                "gCO2e",
                "Services opex emissions",
                "sum",
                "sum",
            ),
            Metadata(
                "services-embodied",
                "gCO2e",
                "Services capex emissions ",
                "sum",
                "sum",
            )
        ]
        # TODO: path parameter below will be changed later
        super().__init__(PLUGIN_PATH, "CostModelPlugin", config, output_metadata)

    @staticmethod
    def fill_inputs(cost_resource: MiscServicesResource, time_index: int):
        """
        Fills the time point specific input values.
        """
        return {
            "compute-energy": cost_resource.compute_energy,
            "storage-energy": cost_resource.storage_energy,
            "compute-embodied": cost_resource.compute_embodied,
            "storage-embodied": cost_resource.storage_embodied,
            "compute-cost": cost_resource.compute_cost,
            "storage-cost": cost_resource.storage_cost,
            "services-cost": cost_resource.services_cost,
            "carbon-intensity": cost_resource.carbon_intensity,
            "timestamp": cost_resource.time_points[time_index]
        }
