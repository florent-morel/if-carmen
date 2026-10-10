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

from backend.src.common.constants import (
    IF_INPUT_INPUT_PARAMETERS,
    IF_INPUT_OUTPUT_PARAMETERS,
    IF_INPUT_MISC_SERVICES_ENERGY_COST_RATIO,
    IF_INPUT_MISC_SERVICES_EMBODIED_COST_RATIO,
    IF_INPUT_COST,
    IF_INPUT_MISC_SERVICES_ENERGY,
    IF_INPUT_MISC_SERVICES_ENERGY_TXT,
    IF_INPUT_MISC_SERVICES_OPERATIONAL,
    IF_INPUT_MISC_SERVICES_EMBODIED,
    IF_INPUT_CARBON_INTENSITY,
    IF_INPUT_SUM,
    IF_INPUT_ENERGY_KWH,
    IF_INPUT_CARBON_GCO2,
    IF_INPUT_MISC_SERVICES_CAPEX,
    IF_INPUT_MISC_SERVICES_OPEX,
    IF_INPUT_TIMESTAMP,
)


class MiscServicesModel(ModelUtilities):
    """
    Concrete class for the Misc Services model
    """

    def __init__(self):
        config = {
            IF_INPUT_INPUT_PARAMETERS: [
                IF_INPUT_MISC_SERVICES_ENERGY_COST_RATIO,
                IF_INPUT_MISC_SERVICES_EMBODIED_COST_RATIO,
                IF_INPUT_COST,
                IF_INPUT_CARBON_INTENSITY,
            ],
            IF_INPUT_OUTPUT_PARAMETERS: [
                IF_INPUT_MISC_SERVICES_ENERGY,
                IF_INPUT_MISC_SERVICES_OPERATIONAL,
                IF_INPUT_MISC_SERVICES_EMBODIED,
            ],
        }
        output_metadata = [
            Metadata(
                IF_INPUT_MISC_SERVICES_ENERGY,
                IF_INPUT_ENERGY_KWH,
                IF_INPUT_MISC_SERVICES_ENERGY_TXT,
                IF_INPUT_SUM,
                IF_INPUT_SUM,
            ),
            Metadata(
                IF_INPUT_MISC_SERVICES_OPERATIONAL,
                IF_INPUT_CARBON_GCO2,
                IF_INPUT_MISC_SERVICES_OPEX,
                IF_INPUT_SUM,
                IF_INPUT_SUM,
            ),
            Metadata(
                IF_INPUT_MISC_SERVICES_EMBODIED,
                IF_INPUT_CARBON_GCO2,
                IF_INPUT_MISC_SERVICES_CAPEX,
                IF_INPUT_SUM,
                IF_INPUT_SUM,
            ),
        ]
        # TODO: path parameter below will be changed later
        super().__init__(
            PLUGIN_PATH, "MiscServicesModelPlugin", config, output_metadata
        )

    @staticmethod
    def fill_inputs(misc_services_resource: MiscServicesResource, time_index: int):
        """
        Fills the time point specific input values.
        """
        return {
            IF_INPUT_MISC_SERVICES_ENERGY_COST_RATIO: misc_services_resource.energy_cost_ratio,
            IF_INPUT_MISC_SERVICES_EMBODIED_COST_RATIO: misc_services_resource.embodied_cost_ratio,
            IF_INPUT_COST: misc_services_resource.cost,
            IF_INPUT_CARBON_INTENSITY: misc_services_resource.carbon_intensity,
            IF_INPUT_TIMESTAMP: misc_services_resource.time_points[time_index],
        }
