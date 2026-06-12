from backend.src.schemas.resource import Resource, ResourceType
from backend.src.common.constants import (
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_DATE,
    SOURCE_PROVIDER,
    SOURCE_PRODUCT_NAME,
    SOURCE_RESOURCE_TYPE,
    SOURCE_COST,
)


class MiscServicesResource(Resource):
    # TODO: Should be set in Orchestrator context to be used only once.
    compute_energy: float = 0.0
    storage_energy: float = 0.0
    compute_embodied: float = 0.0
    storage_embodied: float = 0.0

    compute_cost: float = 0.0
    storage_cost: float = 0.0

    cost: float = 0.0

    misc_services_energy: float = 0.0
    misc_services_operational: float = 0.0
    misc_services_embodied: float = 0.0

    resource_type: ResourceType = ResourceType.MISC_SERVICES

    @staticmethod
    def mandatory_columns() -> list[str]:
        list_mandatory_columns: list[str] = [
            SOURCE_RESOURCE_ID,
            SOURCE_REGION,
            SOURCE_PROVIDER,
            SOURCE_RESOURCE_TYPE,
            SOURCE_DATE,
            SOURCE_PRODUCT_NAME,
            SOURCE_COST,
        ]
        return list_mandatory_columns
