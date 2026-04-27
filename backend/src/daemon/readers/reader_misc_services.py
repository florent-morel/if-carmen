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
from backend.src.schemas.resource import Resource
from backend.src.schemas.cost_resource import CostResource
from backend.src.core.yaml_config_loader import DaemonConfig
from backend.src.daemon.readers.helpers.storage_helpers import (
    calculation_period_days,
    process_storage_row,
)
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

        # COST MODEL PROCESSING
        # TODO: CSV path will be changed when we start fetching the files from finops
        cost_resources, total_compute_cost, total_storage_cost = self.process_cost_csv(
            csv_data
        )
        logger.info(
            "Loaded %d cost resources from local test file",
            len(cost_resources),
        )
        #     TODO: what is this?
        #     cost_resources = []
        #     total_compute_cost, total_storage_cost = 1.0, 1.0

        # # Add missing fields to cost resources
        # for cost_resource in cost_resources:
        #     cost_resource.compute_embodied = vm_total_carbon
        #     cost_resource.compute_energy = vm_total_energy
        #     cost_resource.storage_embodied = storage_total_carbon
        #     cost_resource.storage_energy = storage_total_energy
        #     cost_resource.compute_cost = total_compute_cost
        #     cost_resource.storage_cost = total_storage_cost
        self.list_resources_to_process = cost_resources

        return self.list_resources_to_process

    def process_cost_csv(
        self, csv_data: str
    ) -> tuple[list[CostResource], float, float]:
        """
        Process CSV data into a CostResource list.

        Args:
            csv_data: Raw CSV data

        Returns:
            list[CostResource]: Processed cost resource list
            float: Total compute cost
            float: Total storage cost
        """
        rows = csv_data.splitlines()
        if len(rows) <= 1:
            raise KnownException(ErrorCode.CSV_FILE_NOT_FOUND, "Cost CSV data is empty")

        csv_reader = csv.DictReader(rows)

        logger.info("Processing Cost CSV...")
        cost_resources: list[CostResource] = []
        total_compute_cost = 0.0
        total_storage_cost = 0.0
        for row in csv_reader:
            consumed_service = row.get("ConsumedService", "").lower()
            if "microsoft.compute" == consumed_service:
                total_compute_cost += str_to_float(
                    row.get("CostInBillingCurrencyEUR", "0")
                )
            elif "microsoft.storage" == consumed_service:
                total_storage_cost += str_to_float(
                    row.get("CostInBillingCurrencyEUR", "0")
                )
            else:
                cost_resource = self.create_cost_resource(row)
                if cost_resource.id == "":
                    continue
                cost_resources.append(cost_resource)
        logger.info("Cost CSV processed")
        return cost_resources, total_compute_cost, total_storage_cost

    def create_cost_resource(row):
        """
        Creates a cost resource from the given row
        """
        region = row.get("ResourceLocation", "unknown")
        cost_resource = CostResource(
            id=row.get("ResourceId"),
            name=row.get("ProductName", ""),
            region=region,
            subscription=row.get("SubscriptionId", "unknown"),
            carbon_intensity=PaasCiMapper.calculate_ci(region.lower()),
            services_cost=str_to_float(row.get("CostInBillingCurrencyEUR", "0")),
        )
        timestamp = row.get(
            "Date", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        )
        cost_resource.time_points = [timestamp]
        return cost_resource
