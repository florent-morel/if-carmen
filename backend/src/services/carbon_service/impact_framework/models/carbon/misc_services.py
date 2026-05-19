"""
Misc Services model to calculate service energy and emissions
"""
from backend.src.common.constants import PLUGIN_PATH
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)


class MiscServicesModel(ModelUtilities):
    """
    Concrete class for the Misc Services model
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
                "misc-services-cost",
                "carbon-intensity",
            ],
            "output-parameters": [
                "misc-services-energy",
                "misc-services-operational",
                "misc-services-embodied",
            ],
        }
        output_metadata = [
            Metadata(
                "misc-services-energy",
                "kWh",
                "Total energy consumed for the services",
                "sum",
                "sum",
            ),
            Metadata(
                "misc-services-operational",
                "gCO2e",
                "Services opex emissions",
                "sum",
                "sum",
            ),
            Metadata(
                "misc-services-embodied",
                "gCO2e",
                "Services capex emissions ",
                "sum",
                "sum",
            ),
        ]
        # TODO: path parameter below will be changed later
        super().__init__(
            PLUGIN_PATH, "MiscServicesModelPlugin", config, output_metadata
        )

    @staticmethod
    # Fetch CarbonDaemonResult values to fill compute-energy, etc.
    def fill_inputs(misc_services_resource: MiscServicesResource, time_index: int):
        """
        Fills the time point specific input values.
        """
        return {
            "compute-energy": misc_services_resource.compute_energy,
            "storage-energy": misc_services_resource.storage_energy,
            "compute-embodied": misc_services_resource.compute_embodied,
            "storage-embodied": misc_services_resource.storage_embodied,
            "compute-cost": misc_services_resource.compute_cost,
            "storage-cost": misc_services_resource.storage_cost,
            "misc-services-cost": misc_services_resource.misc_services_cost,
            "carbon-intensity": misc_services_resource.carbon_intensity,
            "timestamp": misc_services_resource.time_points[time_index],
        }
