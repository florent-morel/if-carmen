"""
Storage module for reading and processing compute resource data.
"""

import csv
import os
import logging
from datetime import datetime, timedelta

from pydantic import ValidationError
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException

from backend.src.daemon.readers.abstract_reader import AbstractReader
from backend.src.daemon.readers.helpers.cost_helpers import (
    create_misc_services_resource,
)
from backend.src.schemas.resource import Resource
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.utils.helpers import str_to_float
from backend.src.utils.paas_ci_mapper import PaasCiMapper
from backend.src.schemas.storage_resource import StorageResource
from backend.src.common.constants import (
    CSV_PATH,
    CSV_FILE_TEST,
    CSV_FILE_ENCODING,
)

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

    def __init__(self, input_file, config: DaemonConfig):
        self.config: DaemonConfig = config
        self.input_file = os.getenv(CSV_PATH, CSV_FILE_TEST)

    def read(self, csv_data) -> list[Resource]:
        """
        Read and process files to extract misc services resource information.

        Returns:
            list[StorageResource]: List of storage resources extracted from the
            data source.
        """
        logger.info(f"Inside reader misc services: {self}")

        # MISC SERVICES MODEL PROCESSING
        (
            misc_services_resources,
            total_compute_cost,
            total_storage_cost,
        ) = self.process_csv_data(csv_data)
        logger.info(
            "Loaded %d misc services resources from input file",
            len(misc_services_resources),
        )
        #     TODO: what is this?
        #     cost_resources = []
        #     total_compute_cost, total_storage_cost = 1.0, 1.0

        # Add missing fields to cost resources
        for misc_service_resource in misc_services_resources:
            # TODO: implementation to be done for these values
            # misc_service_resource.compute_embodied = vm_total_carbon
            # misc_service_resource.compute_energy = vm_total_energy
            # misc_service_resource.storage_embodied = storage_total_carbon
            # misc_service_resource.storage_energy = storage_total_energy
            misc_service_resource.compute_cost = total_compute_cost
            misc_service_resource.storage_cost = total_storage_cost

        self.list_resources_to_process = misc_services_resources

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
            list[CostResource]: Processed misc services resource list
            float: Total compute cost
            float: Total storage cost
        """
        rows = csv_data.splitlines()
        if len(rows) <= 1:
            raise KnownException(ErrorCode.CSV_FILE_NOT_FOUND, "Cost CSV data is empty")

        csv_reader = csv.DictReader(rows)

        logger.info("Processing Misc services CSV...")
        misc_services_resources: list[MiscServicesResource] = []
        total_compute_misc_services = 0.0
        total_storage_misc_services = 0.0
        for row in csv_reader:
            self.process_unknown_regions(row["Region"])
            self.process_unknown_providers(row["Provider"])

            consumed_service = row.get("ConsumedService", "").lower()
            # TODO V1: Set a test CSV with ConsumedService, since it's never tested.
            # TODO V1 Critical: Missing logic - there is no mapping between Compute/Storage items' cost, and their emissions/consumptions.
            # It will lead to computing the energy/cost ratios based on
            # - the summed cost of all Compute/Storage services from the input file used here,
            # - and on the energy computed from other input files (the ones used for Compute/Storage processing).
            # There is a critical gap to compute ratios based on cost of Compute/Storage items together with their associated computed energy.
            # Possible solution: add a new BillingCost column in the input files for Compute/Storage, and compute total_compute_misc_services
            # (to be renamed to total_cost_compute / total_cost_storage) from Compute/Storage processing, to then be reused here.
            # TODO: This switch/case should be dynamic to ease future new resource implementation
            if "Compute" == consumed_service:
                total_compute_misc_services += str_to_float(row.get("BillingCost", "0"))
            elif "Storage" == consumed_service:
                total_storage_misc_services += str_to_float(row.get("BillingCost", "0"))
            else:
                misc_services_resource = create_misc_services_resource(row)
                if misc_services_resource.id == "":
                    continue
                misc_services_resources.append(misc_services_resource)
        logger.info("Misc services CSV processed")
        return (
            misc_services_resources,
            total_compute_misc_services,
            total_storage_misc_services,
        )

    def log_processing_results(self) -> None:
        """
        Log the results of the processing operation.
        """
        logger.info(
            "Processing completed found %d misc services resources",
            len(self.list_resources_to_process),
        )

        self.log_unknown_info(self)

        logger.info(
            "Local Reader processing finished successfully"
            "for resource type misc services."
        )
