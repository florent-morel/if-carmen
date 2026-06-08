
"""
Unit tests for the Storage Reader class in the daemon.readers module.

"""

import unittest
from unittest.mock import MagicMock
from collections import Counter

from unittest.mock import patch

from backend.src.common.constants import (
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_PROVIDER,
    SOURCE_COST,
    SOURCE_RESOURCE_TYPE,
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
            f"{SOURCE_RESOURCE_ID},{SOURCE_RESOURCE_TYPE},{SOURCE_PROVIDER},{SOURCE_REGION},{SOURCE_COST}\n"
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

        # Compute and Storage rows are excluded by the reader filter.
        # Only "network" and "keyvault" rows produce valid misc service resources.
        # The empty row is skipped (no id).
        self.assertEqual(len(list_processed_resources), 2)

        resultMiscServicesResource = list_processed_resources[0]

        # Ensure input data is not altered.
        # TODO: check what needs to be validated in output of Misc Services Reader
        self.assertEqual(resultMiscServicesResource.resource_type, ResourceType.MISC_SERVICES)
        self.assertEqual(resultMiscServicesResource.id, "misc_service5")  # first non-compute/storage row
        self.assertEqual(resultMiscServicesResource.cost, 80.0)
        self.assertEqual(resultMiscServicesResource.provider, "provider_abc")
        self.assertEqual(resultMiscServicesResource.region, "centralus")

        # TODO: these should be UT
        # self.assertEqual(total_compute_cost, 175.0)
        # self.assertEqual(total_storage_cost, 110.0)

    def test_reader_misc_services_dict_log_info(self):
        """
        Verify dict_log_info counters after processing a CSV with
        compute/storage exclusions and a skipped (empty-id) row.
        """
        mock_csv_data = (
            f"{SOURCE_RESOURCE_ID},{SOURCE_RESOURCE_TYPE},{SOURCE_PROVIDER},{SOURCE_REGION},{SOURCE_COST}\n"
            "misc_service1,Compute,provider_abc,centralus,100.0\n"   # excluded: compute
            "misc_service2,Compute,provider_abc,centralus,75.0\n"    # excluded: compute
            "misc_service3,Storage,provider_abc,centralus,50.0\n"    # excluded: storage
            "misc_service4,Storage,provider_abc,centralus,60.0\n"    # excluded: storage
            "misc_service5,network,provider_abc,centralus,80.0\n"    # valid misc
            ",,,,\n"                                                  # skipped: empty id
            "misc_service6,keyvault,provider_abc,centralus,90.0\n"  # valid misc
        )

        reader = Reader_Misc_Services(self.mock_config)
        reader.known_regions = ["centralus"]
        reader.unknown_regions = Counter()
        reader.unknown_providers = Counter()

        reader.read(mock_csv_data)

        self.assertEqual(reader.dict_log_info["total_rows"], 7)
        self.assertEqual(reader.dict_log_info["compute_rows"], 2)
        self.assertEqual(reader.dict_log_info["storage_rows"], 2)
        self.assertEqual(reader.dict_log_info["skipped_rows"], 1)
        self.assertEqual(reader.dict_log_info["misc_services_rows"], 2)
