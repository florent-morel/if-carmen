"""
This module maps metrics taken from the if-output to a compute resource object.
"""

from backend.src.schemas.compute_resource import Resource


class MetricsMapper:
    """
    A class that maps metrics to a compute resource.
    """

    METRICS_MAPPER = {
        "carbon": {
            "observations": "carbon_emitted",
            "aggregated": "total_carbon_emitted",
        },
        "energy": {
            "observations": "energy_consumed",
            "aggregated": "total_energy_consumed",
        },
        "carbon-embodied": {
            "observations": "carbon_embodied",
            "aggregated": "total_carbon_embodied",
        },
        "carbon-operational": {
            "observations": "carbon_operational",
            "aggregated": "total_carbon_operational",
        },
        "cpu/energy": {"observations": "cpu_energy", "aggregated": "total_cpu_energy"},
        "cpu/power": {"observations": "cpu_power", "aggregated": None},
        "resources-reserved": {"observations": "requested_cpu", "aggregated": None},
        "memory/energy": {
            "observations": "memory_energy",
            "aggregated": "total_memory_energy",
        },
        "storage/energy": {
            "observations": "storage_energy",
            "aggregated": "total_storage_energy",
        },
        "storage-embodied": {
            "observations": "storage_embodied",
            "aggregated": "total_storage_embodied",
        },
        "misc-services-energy": {
            "observations": "misc_services_energy",
            "aggregated": "total_energy_consumed",
        },
        "misc-services-operational": {
            "observations": "misc_services_operational",
            "aggregated": "total_carbon_operational",
        },
        "misc-services-embodied": {
            "observations": "misc_services_embodied",
            "aggregated": "total_carbon_embodied",
        },
    }

    @classmethod
    def map_metrics_to_resource(cls, metrics: dict, resource: Resource):
        """
        Maps metrics to the attributes of a resource.

        Args:
            metrics (dict): A dictionary containing metric data. The keys are metric names,
                            and the values are dictionaries with "observations" and optionally
                            "aggregated" values.
            resource (Resource): An instance of `Resource` or its subclasses where the
                               metrics will be mapped to its attributes.
        """
        for metric_key, attribute_mapping in cls.METRICS_MAPPER.items():
            if metric_key in metrics:
                observations = metrics[metric_key]["observations"]
                setattr(resource, attribute_mapping["observations"], observations)
                if attribute_mapping["aggregated"]:
                    aggregated_value = metrics[metric_key]["aggregated"]
                    setattr(resource, attribute_mapping["aggregated"], aggregated_value)

        # Derive total_carbon_emitted from operational + embodied when not set directly
        # (e.g. misc_services IF output provides carbon-operational and carbon-embodied but not carbon)
        if resource.total_carbon_emitted == 0.0 and (
            resource.total_carbon_operational > 0 or resource.total_carbon_embodied > 0
        ):
            resource.total_carbon_emitted = round(
                resource.total_carbon_operational + resource.total_carbon_embodied, 4
            )

        # Guard against pipelines that do not emit a direct per-observation total carbon series. 
        # Reconstruct it here so the rest of the code can rely on carbon_emitted being populated.
        if not resource.carbon_emitted and (
            resource.carbon_operational or resource.carbon_embodied
        ):
            # The two component lists can differ in length. Iterate over the
            # longest one and treat any missing value on the shorter side as 0.0.
            observation_count = max(
                len(resource.carbon_operational), len(resource.carbon_embodied)
            )
            resource.carbon_emitted = [
                # For each observation index, total carbon is operational + embodied.
                round(
                    (resource.carbon_operational[index] if index < len(resource.carbon_operational) else 0.0)
                    + (resource.carbon_embodied[index] if index < len(resource.carbon_embodied) else 0.0),
                    4,
                )
                for index in range(observation_count)
            ]
