"""
Unit tests for misc services helpers functions.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from backend.src.common.carmen_exception import CarmenException
from backend.src.core.settings import settings, ReportConfig
from backend.src.daemon.readers.helpers.misc_services_helpers import (
    get_carbon_and_energy_values,
    create_misc_services_resource,
    create_misc_services_report,
)
from backend.src.schemas.misc_services_resource import MiscServicesResource
from etc.sample_data.test_data.test_data import (
    sample_vms,
    sample_storage_resources,
)
from backend.src.schemas.resource import ResourceType


class TestMiscServicesHelpers(unittest.TestCase):
    """
    Unit tests for misc_services_helpers class functions.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.misc_services_resources = [
            MiscServicesResource(
                id="misc_service1",
                name="name1",
                region="eastus",
                subscription="sub1",
                carbon_intensity=100.0,
                misc_services_cost=50.0,
            ),
            MiscServicesResource(
                id="misc_service2",
                name="name2",
                region="westus",
                subscription="sub2",
                carbon_intensity=150.0,
                misc_services_cost=75.0,
            ),
        ]

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
            "BillingCost": "120.0",
            "Date": "2025-11-01",
        }
        mock_ci_calculator.return_value = 200.0

        misc_services_resource = create_misc_services_resource(mock_row)

        self.assertEqual(misc_services_resource.id, "misc_service1")
        self.assertEqual(misc_services_resource.resource_type, ResourceType.MISC_SERVICES)
        self.assertEqual(misc_services_resource.region, "eastus")
        self.assertEqual(misc_services_resource.subscription, "sub1")
        self.assertEqual(misc_services_resource.carbon_intensity, 200.0)
        self.assertEqual(misc_services_resource.misc_services_cost, 120.0)
        self.assertEqual(misc_services_resource.time_points[0], "2025-11-01")

    @patch("builtins.open", new_callable=mock_open)
    def test_create_misc_services_report(self, mock_file):
        """
        Test that create_misc_services_report writes misc services resource data correctly to the CSV file.
        """
        mock_date = datetime.now() - timedelta(days=7)
        test_file_name = "test_misc_services_report.csv"

        with self.assertLogs(level="INFO") as log:
            create_misc_services_report(
                self.misc_services_resources,
                mock_date.strftime("%Y-%m-%d"),
                test_file_name,
            )
            self.assertIn("misc_services model report saved to:", log.output[1])

        mock_file.assert_called_once_with(
            test_file_name, mode="w", newline="", encoding="utf-8"
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_create_misc_services_report_headers(self, mock_file):
        """
        Test that create_misc_services_report writes misc services resource data headers correctly to the CSV file.
        """
        mock_date = datetime.now() - timedelta(days=7)
        test_file_name = "test_misc_services_report.csv"
        expected_headers = ReportConfig.MISC_SERVICES_REPORT_HEADERS[0]

        with self.assertLogs(level="INFO") as log:
            create_misc_services_report(
                self.misc_services_resources,
                mock_date.strftime("%Y-%m-%d"),
                test_file_name,
            )
            self.assertIn("misc_services model report saved to:", log.output[1])

        mock_file().write.assert_called()
        handle = mock_file()
        written_data = handle.write.call_args_list[0][0][0]
        headers = written_data.strip().split(",")
        self.assertCountEqual(headers, expected_headers)
