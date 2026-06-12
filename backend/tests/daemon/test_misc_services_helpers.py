"""
Unit tests for misc services helpers functions.
"""
import unittest
import logging

from unittest.mock import patch

from backend.src.daemon.readers.helpers.misc_services_helpers import (
    get_carbon_and_energy_values,
    create_misc_services_resource,
)
from etc.sample_data.test_data.test_data import (
    sample_vms,
    sample_storage_resources,
)
from backend.src.schemas.resource import ResourceType

logger = logging.getLogger(__name__)

class TestMiscServicesHelpers(unittest.TestCase):
    """
    Unit tests for misc_services_helpers class functions.
    """

    def test_get_carbon_and_energy_values(self):
        """
        Test get_carbon_and_energy_values function.
        """
        (
            storage_total_carbon,
            storage_total_energy,
            vm_total_carbon,
            vm_total_energy,
        ) = get_carbon_and_energy_values(sample_vms, sample_storage_resources)

        self.assertEqual(storage_total_carbon, 305.0)
        self.assertEqual(storage_total_energy, 125.0)
        self.assertEqual(vm_total_carbon, 200.0)
        self.assertEqual(vm_total_energy, 100.0)

    # TODO: Implement UT to validate exception is raised
    # if no CSV provided. (Should be in reader)
    # def test_process_misc_services_csv_empty(self):
    #     """
    #     Test process_misc_services_csv function with empty CSV data.
    #     """

    #     with self.assertRaises(CarmenException) as context:
    #         process_misc_services_csv("")

    #     self.assertEqual(str(context.exception.details), "Misc Services CSV data is empty")

    @patch(
        "backend.src.daemon.readers.helpers.misc_services_helpers.PaasCiMapper.calculate_ci"
    )
    def test_create_misc_services_resource(self, mock_ci_calculator):
        """
        Test create_misc_services_resource function.
        """
        mock_row = {
            "ResourceId": "misc_service1",
            "ProductName": "misc_service_name",
            "Region": "eastus",
            "SubscriptionId": "sub1",
            "Cost": "120.0",
            "Date": "2025-11-01",
        }
        mock_ci_calculator.return_value = 200.0

        misc_services_resource = create_misc_services_resource(mock_row)

        self.assertEqual(misc_services_resource.id, "misc_service1")
        self.assertEqual(misc_services_resource.resource_type, ResourceType.MISC_SERVICES)
        self.assertEqual(misc_services_resource.region, "eastus")
        self.assertEqual(misc_services_resource.carbon_intensity, 200.0)
        self.assertEqual(misc_services_resource.cost, 120.0)
        self.assertEqual(misc_services_resource.time_points[0], "2025-11-01")

        # No custom columns as we directly create the resource
        self.assertEqual(len(misc_services_resource.dict_custom_columns), 0)
