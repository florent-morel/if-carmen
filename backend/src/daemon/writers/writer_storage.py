import logging
from typing import Any, Iterable

from backend.src.core.settings import settings
from backend.src.daemon.writers.abstract_writer import AbstractWriter
from backend.src.schemas.storage_resource import StorageResource

logger = logging.getLogger(__name__)


class Writer_Storage(AbstractWriter):

    def build_content(resources: list[StorageResource]) -> Iterable[Iterable[Any]]:
        storage_resource_carbon = 0
        storage_resource_energy = 0

        # Add resources
        list_rows = []
        for storage_resource in resources:
            storage_resource.total_carbon_emitted = (
                storage_resource.total_carbon_operational + storage_resource.total_carbon_embodied
            )
            storage_resource_carbon += storage_resource.total_carbon_emitted
            storage_resource_energy += storage_resource.total_energy_consumed

            # Build common columns
            row = super.build_common_content(storage_resource)

            # storage_resource specific columns
            row.append(storage_resource.storage_resource_size)
            row.append(storage_resource.service)
            row.append(storage_resource.instance)
            row.append(storage_resource.environment)
            row.append(storage_resource.partition)
            row.append(storage_resource.component)

            list_rows.append(row)

        logging.info("Total carbon emitted: %.2f kg CO2", storage_resource_carbon)
        logging.info("Total energy consumed: %.2f kWh", storage_resource_energy)
        logger.info(
            "  Resources: %d resources",
            len(resources),
        )
        return list_rows
