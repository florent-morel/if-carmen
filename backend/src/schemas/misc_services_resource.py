from backend.src.schemas.resource import Resource, ResourceType
from backend.src.common.constants import (
    SOURCE_SAMPLE_DURATION_SECONDS,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_SAMPLE_TIMESTAMP,
    SOURCE_PROVIDER,
    SOURCE_RESOURCE_NAME,
    SOURCE_RESOURCE_TYPE,
    SOURCE_COST,
)


class MiscServicesResource(Resource):
    energy_cost_ratio: float = 0.0
    embodied_cost_ratio: float = 0.0

    cost: float = 0.0

    misc_services_energy: float = 0.0
    misc_services_operational: float = 0.0
    misc_services_embodied: float = 0.0

    resource_type: ResourceType = ResourceType.MISC_SERVICES

    @staticmethod
    def mandatory_columns() -> list[str]:
        # Fetch common mandatory columns
        list_mandatory_columns: list[str] = super(MiscServicesResource, MiscServicesResource).common_mandatory_columns()

        # Append specific mandatory columns
        list_mandatory_columns.extend([
            # No specific column
        ])
        return list_mandatory_columns
