from backend.src.schemas.resource import Resource, ResourceType


class MiscServicesResource(Resource):
    compute_energy: float = 0.0
    storage_energy: float = 0.0
    compute_embodied: float = 0.0
    storage_embodied: float = 0.0

    # TODO: Might not be need once billing_cost is implemented in Resource
    compute_cost: float = 0.0
    storage_cost: float = 0.0

    misc_services_cost: float = 0.0

    misc_services_energy: float = 0.0
    misc_services_operational: float = 0.0
    misc_services_embodied: float = 0.0

    resource_type: ResourceType = ResourceType.MISC_SERVICES
