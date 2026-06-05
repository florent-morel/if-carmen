"""
Storage module for reading and processing compute resource data.
"""

import csv
import logging


from backend.src.common.carmen_exception import CarmenException
from backend.src.common.constants import (
    SOURCE_RESOURCE_TYPE_COMPUTE,
    SOURCE_RESOURCE_TYPE,
    SOURCE_PROVIDER,
    SOURCE_REGION,
    SOURCE_RESOURCE_TYPE_STORAGE,
)
from backend.src.common.errors import ErrorCode
from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.utils.helpers import (
    process_custom_columns,
)

from backend.src.daemon.readers.helpers.misc_services_helpers import (
    create_misc_services_resource,
)
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.resource import Resource

logger = logging.getLogger(__name__)


class Reader_Misc_Services(AbstractReader):
    """
    Class for reading misc services input data.
    Misc services relate to all services shared by your applications.
    This might include:
    - Network appliances.
    - Security applications.
    In Carmen today's implementation, no model is provided for each of these
    atomic services.
    Hence a Misc Services implementation.
    """

    def read(self, csv_data) -> list[Resource]:
        """
        Read and process files to extract misc services resource information.

        Returns:
            list[StorageResource]: List of storage resources extracted from the
            data source.
        """
        logger.info(f"Inside reader misc services: {self}")
        logger.debug(f"csv_data: {csv_data}")

        self.list_resources_to_process = self.process_csv_data(csv_data)
        logger.info(
            "Loaded %d misc services resources from input file",
            len(self.list_resources_to_process),
        )

        self.log_processing_results()

        return self.list_resources_to_process

    def process_csv_data(
        self, csv_data: str
    ) -> tuple[list[MiscServicesResource], float, float]:
        """
        Process CSV data into a MiscServicesResourcelist.

        Args:
            csv_data: Raw CSV data

        Returns:
            list[MiscServicesResource]: Processed misc services resource list
            float: Total compute cost
            float: Total storage cost
        """
        rows = csv_data.splitlines()
        if len(rows) <= 1:
            raise CarmenException(
                ErrorCode.CSV_FILE_NOT_FOUND, "Misc Services CSV data is empty"
            )

        csv_reader = csv.DictReader(rows)

        logger.info("Processing Misc services CSV...")
        misc_services_resources: list[MiscServicesResource] = []
        logger.debug(f"csv_data: {csv_data}")

        total_rows = 0
        compute_rows = 0
        storage_rows = 0
        skipped_rows = 0
        misc_services_rows = 0

        for row in csv_reader:
            total_rows += 1
            logger.debug(f"row: {row}")
            self.process_unknown_regions(row[SOURCE_REGION])
            self.process_unknown_providers(row[SOURCE_PROVIDER])

            consumed_service = row.get(SOURCE_RESOURCE_TYPE, "").lower()
            if consumed_service == SOURCE_RESOURCE_TYPE_COMPUTE.lower():
                compute_rows += 1
                continue
            if consumed_service == SOURCE_RESOURCE_TYPE_STORAGE.lower():
                storage_rows += 1
                continue
            misc_services_resource = create_misc_services_resource(row)
            if not misc_services_resource or misc_services_resource.id == "":
                skipped_rows += 1
                continue
            misc_services_resources.append(misc_services_resource)
            misc_services_rows += 1
            # End of row process, fetch custom columns
            process_custom_columns(misc_services_resource, row,
                                        MiscServicesResource.mandatory_columns())

        self.dict_log_info["total_rows"] = total_rows
        self.dict_log_info["compute_rows"] = compute_rows
        self.dict_log_info["storage_rows"] = storage_rows
        self.dict_log_info["skipped_rows"] = skipped_rows
        self.dict_log_info["misc_services_rows"] = misc_services_rows

        logger.info("Misc services CSV processed")
        return misc_services_resources

    def log_processing_results(self) -> None:
        """
        Log the results of the processing operation.
        """
        logger.info(
            "Processing completed found %d misc services resources",
            len(self.list_resources_to_process),
        )

        logger.debug("Misc services processing summary:")
        logger.debug("  Total rows: %s", self.dict_log_info.get("total_rows", 0))
        logger.debug("  Compute rows (excluded): %s", self.dict_log_info.get("compute_rows", 0))
        logger.debug("  Storage rows (excluded): %s", self.dict_log_info.get("storage_rows", 0))
        logger.debug("  Skipped rows (no id): %s", self.dict_log_info.get("skipped_rows", 0))
        logger.debug("  Misc services rows: %s", self.dict_log_info.get("misc_services_rows", 0))

        self.log_unknown_info()

        logger.info(
            "Local Reader processing finished successfully"
            "for resource type misc services."
        )
