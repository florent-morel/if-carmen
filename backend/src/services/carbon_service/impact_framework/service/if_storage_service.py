"""
Impact Framework service for storage resources - extends IFService
"""
from __future__ import annotations

import concurrent
import logging
from itertools import groupby

from backend.src.core.yaml_config_loader import config
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)
from backend.src.schemas.storage_resource import StorageResource
from backend.src.services.carbon_service.impact_framework.models.power.p_storage import (
    PStorage,
)
from backend.src.services.carbon_service.impact_framework.models.energy.e_storage import (
    EStorage,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.m_storage import (
    MStorage,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

logger = logging.getLogger(__name__)


class IFStorageService(IFService):
    """
    Specialized Impact Framework service for storage resources.
    Uses StorageP, StorageE and StorageM models.
    """

    def __init__(self, duration):
        super().__init__(
            "storage_template.yml.j2", "storage_pipeline.yml", "horizontal", duration
        )

    def run_engine(
        self, storage_resources: list[StorageResource]
    ) -> list[StorageResource]:
        """
        Executes the Impact Framework (IF) model to compute energy and CO2 metrics for storage resources.
        Divides storage resources into chunks and processes them in parallel.
        """
        logger.info(
            "Starting storage carbon calculation for %d resources...",
            len(storage_resources),
        )

        # Statistics before processing
        total_size = sum(storage.size_gb for storage in storage_resources)

        ssd_count = sum(
            1 for storage in storage_resources if "ssd" in storage.storage_type.lower()
        )

        hdd_count = sum(
            1 for storage in storage_resources if "hdd" in storage.storage_type.lower()
        )

        logger.info(
            "Storage inventory: %.1f GB total (%d SSD, %d HDD)",
            total_size,
            ssd_count,
            hdd_count,
        )

        chunk_size = 10000

        # Group by provider so each IF run uses the correct provider-specific config.
        def _provider_key(s: StorageResource) -> str:
            return s.provider if isinstance(s.provider, str) else ""

        sorted_resources = sorted(storage_resources, key=_provider_key)
        all_chunks: list[list[StorageResource]] = []
        for _, group in groupby(sorted_resources, key=_provider_key):
            group_list = list(group)
            for x in range(0, len(group_list), chunk_size):
                all_chunks.append(group_list[x : x + chunk_size])

        def compute_metrics_for_chunk(chunk, index):
            """Process a chunk of storage resources."""
            self.run_if(chunk, index)  # Generate IF input file with file_id=index
            # Parse IF output file with file_id=index
            self.parse_if_output(chunk, file_id=index)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(compute_metrics_for_chunk, chunk, i)
                for i, chunk in enumerate(all_chunks)
            ]
            concurrent.futures.wait(futures)

        total_energy = sum(
            storage.total_energy_consumed for storage in storage_resources
        )
        total_operational = sum(
            storage.total_carbon_operational for storage in storage_resources
        )
        total_embodied = sum(
            storage.total_carbon_embodied for storage in storage_resources
        )
        total_carbon = sum(
            storage.total_carbon_emitted for storage in storage_resources
        )

        logger.info("Storage calculation completed:")
        logger.info("   Energy: %.4f kWh", total_energy)
        logger.info("   Operational: %.2f gCO2", total_operational)
        logger.info("   Embodied: %.2f gCO2", total_embodied)
        logger.info("   Total: %.2f gCO2", total_carbon)

        # Top 5 carbon emitters for debugging
        sorted_by_carbon = sorted(
            storage_resources, key=lambda x: x.total_carbon_emitted, reverse=True
        )
        logger.debug("Top 5 carbon emitters:")
        for i, storage in enumerate(sorted_by_carbon[:5]):
            logger.debug(
                "   %d. ID %s: %s: %.2f gCO2 (%s, %.1f GB, %s)",
                i + 1,
                storage.id,
                storage.resource_type,
                storage.total_carbon_emitted,
                storage.storage_type,
                storage.size_gb,
                storage.replication_type,
            )

        return storage_resources

    def get_models_info(self, data, provider: str = ""):
        """
        Load storage-specific models
        """
        provider_config = config.provider_configs.get(provider)
        super().get_models_info(data, provider)

        if "p-storage" in data["hardware_models"]:
            data["hardware_models"]["p-storage"] = PStorage(provider_config).__dict__
        if "e-storage" in data["hardware_models"]:
            data["hardware_models"]["e-storage"] = EStorage().__dict__
        if "m-storage" in data["hardware_models"]:
            data["hardware_models"]["m-storage"] = MStorage(provider_config).__dict__

    def fill_parser_data(self, data, resources):
        """
        Override to pass provider-specific model instances to get_resource_inputs
        so fill_inputs can access provider_config.
        """
        provider = (resources[0].provider if resources else None) or ""
        provider_config = config.provider_configs.get(provider)
        self.get_models_info(data, provider)
        models = (PStorage(provider_config), EStorage(), MStorage(provider_config))
        data["resources"] = {
            resource.id: self.get_resource_inputs(resource, models)
            for resource in resources
        }

    @staticmethod
    def get_resource_inputs(
        storage_resource: StorageResource,
        models: tuple[ModelUtilities, ...],
    ):
        """
        Generates input data for each time point of a storage resource using storage-specific models.
        """
        resource_inputs = []

        time_points_count = (
            len(storage_resource.time_points) if storage_resource.time_points else 1
        )

        for time_index in range(time_points_count):
            combined_inputs = {
                "timestamp": (
                    storage_resource.time_points[time_index]
                    if storage_resource.time_points
                    else "2025-01-01"
                ),
                "grid/carbon-intensity": storage_resource.carbon_intensity,
            }

            # Add inputs from each storage model
            for model in models:
                try:
                    model_inputs = model.fill_inputs(storage_resource, time_index)
                    combined_inputs.update(model_inputs)
                except (AttributeError, KeyError, ValueError, TypeError) as e:
                    logger.warning(
                        "Error getting inputs from %s for storage %s: %s",
                        type(model).__name__,
                        storage_resource.id,
                        e,
                    )
                    continue

            resource_inputs.append(combined_inputs)

        return resource_inputs
