
"""
Unit tests for the Storage Reader class in the daemon.readers module.

"""

import unittest
from unittest.mock import MagicMock

from unittest.mock import patch

from backend.src.common.constants import (
    HOURLY_INTERVAL_SECONDS,
)
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.readers.reader_misc_services import Reader_Misc_Services

import logging

logger = logging.getLogger(__name__)


class TestReaderMiscServices(unittest.TestCase):
    """
    Unit test class for the CarbonDaemon class and related to storage
    calculation functionality.
    """

    # def create_sample_storage(
    #     self,
    #     storage_id,
    #     product_name,
    #     storage_type,
    #     replication_type,
    #     size_gb,
    #     region,
    #     subscription,
    #     resource_group,
    #     carbon_intensity,
    #     time_points,
    #     duration_seconds,
    # ) -> StorageResource:
    #     """
    #     Returns a sample storage resource dictionary.
    #     """
    #     storageResource = StorageResource(
    #         id=storage_id,
    #         name=product_name,
    #         storage_type=storage_type,
    #         replication_type=replication_type,
    #         size_gb=size_gb,
    #         region=region,
    #         subscription=subscription,
    #         resource_group=resource_group,
    #         carbon_intensity=carbon_intensity,
    #         time_points=[],
    #         duration_seconds=duration_seconds,
    #     )
    #     return storageResource

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()

    def test_reader_misc_services_success(self):
        """
        Test successful Misc Services Reader execution.
        """
        mock_csv_data = (
            "ResourceId,ConsumedService,BillingCost\n"
            "misc_service1,Compute,100.0\n"
            "misc_service2,Compute,75.0\n"
            "misc_service3,Storage,50.0\n"
            "misc_service4,Storage,60.0\n"
            "misc_service5,network,80.0\n"
            ",,\n"
            "misc_service6,keyvault,90.0\n"
        )

        reader_misc_services = Reader_Misc_Services(self.mock_config)

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.MISC_SERVICES
        mock_processor.reader = reader_misc_services

        logger.debug(f"Inside test reader Misc Services: {self}")
        list_processed_resources = reader_misc_services.read(mock_csv_data)

        self.assertEqual(len(list_processed_resources), 2)

        resultMiscServicesResource = list_processed_resources[0]

        # Ensure input data is not altered.
        # TODO: check what needs to be validated in output of Misc Services Reader
        # self.assertEqual(resultMiscServicesResource.size_gb, 32.0)
        # self.assertEqual(resultMiscServicesResource.storage_type, "SSD")
        # self.assertEqual(resultMiscServicesResource.replication_type, "LRS")

        # TODO: these should be UT
        # self.assertEqual(total_compute_cost, 175.0)
        # self.assertEqual(total_storage_cost, 110.0)
