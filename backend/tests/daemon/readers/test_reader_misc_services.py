
"""
Unit tests for the Storage Reader class in the daemon.readers module.

"""

import unittest
from unittest.mock import MagicMock
from collections import Counter

from unittest.mock import patch

from backend.src.common.constants import (
    CSV_PATH,
    CSV_FILE_TEST,
    CSV_FILE_ENCODING,
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_PROVIDER,
    SOURCE_BILLING_COST,
    SOURCE_COMPUTE,
    SOURCE_STORAGE,
    SOURCE_CONSUMED_SERVICE,
)
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.resource import ResourceType
from backend.src.daemon.readers.reader_misc_services import Reader_Misc_Services

import logging

logger = logging.getLogger(__name__)


class TestReaderMiscServices(unittest.TestCase):
    """
    Unit test class for the Misc Services Reader.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()

    def test_reader_misc_services_success(self):
        """
        Test successful Misc Services Reader execution.
        """
        mock_csv_data = (
            f"{SOURCE_RESOURCE_ID},{SOURCE_CONSUMED_SERVICE},{SOURCE_PROVIDER},{SOURCE_REGION},{SOURCE_BILLING_COST}\n"
            "misc_service1,Compute,provider_abc,centralus,100.0\n"
            "misc_service2,Compute,provider_abc,centralus,75.0\n"
            "misc_service3,Storage,provider_abc,centralus,50.0\n"
            "misc_service4,Storage,provider_abc,centralus,60.0\n"
            "misc_service5,network,provider_abc,centralus,80.0\n"
            ",,\n"
            "misc_service6,keyvault,provider_abc,centralus,90.0\n"
        )

        reader_misc_services = Reader_Misc_Services(self.mock_config)
        reader_misc_services.known_regions = ["australiaeast", "centralus", "eastasia", "eastus", "francecentral", "centralindia"]
        reader_misc_services.unknown_regions = Counter()
        reader_misc_services.unknown_providers = Counter()
        reader_misc_services.dict_log_info = {}

        mock_processor = MagicMock()
        mock_processor.resource_type = ResourceType.MISC_SERVICES
        mock_processor.reader = reader_misc_services

        logger.debug(f"Inside test reader Misc Services: {self}")
        list_processed_resources = reader_misc_services.read(mock_csv_data)

        self.assertEqual(len(list_processed_resources), 6)

        resultMiscServicesResource = list_processed_resources[0]

        # Ensure input data is not altered.
        # TODO: check what needs to be validated in output of Misc Services Reader
        self.assertEqual(resultMiscServicesResource.resource_type, ResourceType.MISC_SERVICES)
        self.assertEqual(resultMiscServicesResource.id, "misc_service1")
        self.assertEqual(resultMiscServicesResource.misc_services_cost, 100.0)
        self.assertEqual(resultMiscServicesResource.provider, "provider_abc")
        self.assertEqual(resultMiscServicesResource.region, "centralus")

        # TODO: these should be UT
        # self.assertEqual(total_compute_cost, 175.0)
        # self.assertEqual(total_storage_cost, 110.0)
