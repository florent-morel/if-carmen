"""
Unit tests for cost helpers functions.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from backend.src.common.known_exception import KnownException
from backend.src.core.settings import settings
from backend.src.daemon.readers.helpers.cost_helpers import (
    get_carbon_and_energy_values,
    process_cost_csv,
    create_cost_resource,
    create_cost_report,
)
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.tests.daemon.test_data.test_data import (
    sample_vms,
    sample_storage_resources,
)


class TestCostHelpers(unittest.TestCase):
    """
    Unit tests for cost_helpers class functions.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.cost_resources = [
            CostResource(
                id="cost1",
                name="name1",
                region="eastus",
                subscription="sub1",
                carbon_intensity=100.0,
                services_cost=50.0,
            ),
            CostResource(
                id="cost2",
                name="name2",
                region="westus",
                subscription="sub2",
                carbon_intensity=150.0,
                services_cost=75.0,
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

    def test_process_cost_csv_empty(self):
        """
        Test process_cost_csv function with empty CSV data.
        """

        with self.assertRaises(KnownException) as context:
            process_cost_csv("")

        self.assertEqual(str(context.exception.details), "Cost CSV data is empty")

    def test_process_cost_csv(self):
        """
        Test process_cost_csv function with CSV data.
        """
        mock_csv_data = (
            "ResourceId,ConsumedService,CostInBillingCurrencyEUR\n"
            "cost1,microsoft.compute,100.0\n"
            "cost2,microsoft.compute,75.0\n"
            "cost3,microsoft.storage,50.0\n"
            "cost4,microsoft.storage,60.0\n"
            "cost5,network,80.0\n"
            ",,\n"
            "cost6,keyvault,90.0\n"
        )

        cost_resources, total_compute_cost, total_storage_cost = process_cost_csv(
            mock_csv_data
        )

        self.assertEqual(len(cost_resources), 2)
        self.assertEqual(total_compute_cost, 175.0)
        self.assertEqual(total_storage_cost, 110.0)

    @patch("backend.src.daemon.readers.helpers.cost_helpers.PaasCiMapper.calculate_ci")
    def test_create_cost_resource(self, mock_ci_calculator):
        """
        Test create_cost_resource function.
        """
        mock_row = {
            "ResourceId": "cost1",
            "ProductName": "costName",
            "ResourceLocation": "eastus",
            "SubscriptionId": "sub1",
            "CostInBillingCurrencyEUR": "120.0",
            "Date": "2025-11-01",
        }
        mock_ci_calculator.return_value = 200.0

        cost_resource = create_cost_resource(mock_row)

        self.assertEqual(cost_resource.id, "cost1")
        self.assertEqual(cost_resource.resource_type, "costName")
        self.assertEqual(cost_resource.region, "eastus")
        self.assertEqual(cost_resource.subscription, "sub1")
        self.assertEqual(cost_resource.carbon_intensity, 200.0)
        self.assertEqual(cost_resource.services_cost, 120.0)
        self.assertEqual(cost_resource.time_points[0], "2025-11-01")

    @patch("builtins.open", new_callable=mock_open)
    def test_create_cost_report(self, mock_file):
        """
        Test that create_cost_report writes cost resource data correctly to the CSV file.
        """
        mock_date = datetime.now() - timedelta(days=7)
        test_file_name = "test_cost_report.csv"

        with self.assertLogs(level="INFO") as log:
            create_cost_report(
                self.cost_resources, mock_date.strftime("%Y-%m-%d"), test_file_name
            )
            self.assertIn("Cost model report saved to:", log.output[1])

        mock_file.assert_called_once_with(
            test_file_name, mode="w", newline="", encoding="utf-8"
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_create_cost_report_headers(self, mock_file):
        """
        Test that create_cost_report writes cost resource data headers correctly to the CSV file.
        """
        mock_date = datetime.now() - timedelta(days=7)
        test_file_name = "test_cost_report.csv"
        expected_headers = settings.FINOPS.COST_REPORT_HEADERS[0]

        with self.assertLogs(level="INFO") as log:
            create_cost_report(
                self.cost_resources, mock_date.strftime("%Y-%m-%d"), test_file_name
            )
            self.assertIn("Cost model report saved to:", log.output[1])

        mock_file().write.assert_called()
        handle = mock_file()
        written_data = handle.write.call_args_list[0][0][0]
        headers = written_data.strip().split(",")
        self.assertCountEqual(headers, expected_headers)
