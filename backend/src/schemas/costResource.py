from typing import Optional

from backend.src.schemas.resource import Resource


class CostResource(Resource):
    region: Optional[str] = None
    subscription: Optional[str] = None
    compute_energy: float = 0.0
    storage_energy: float = 0.0
    compute_embodied: float = 0.0
    storage_embodied: float = 0.0
    compute_cost: float = 0.0
    storage_cost: float = 0.0
    services_cost: float = 0.0
    carbon_intensity: float = 0.0
    services_energy: float = 0.0
    services_operational: float = 0.0
    services_embodied: float = 0.0
