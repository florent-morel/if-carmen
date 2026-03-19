"""
Unit tests for the FinOpsDatalake class.
"""

# pylint: disable=arguments-differ
import os
import unittest
from collections import defaultdict
from unittest.mock import patch, mock_open
from datetime import datetime, timedelta
import pandas as pd
import pyarrow
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from requests import RequestException
from backend.src.common.known_exception import KnownException
from backend.src.core.config import settings
from backend.src.daemon.finops_datalake import FinOpsDatalake
from backend.tests.daemon.test_data.test_data import (
    sample_vms,
    sample_storage_resources,
)

TEST_REPORT_FILE_NAME = "test_report.csv"


class TestFinOpsDatalake(unittest.TestCase):
    """
    Unit tests for the FinOpsDatalake class.

    Tests cover successful file upload, handling of deactivated datalake access,
    and various error scenarios including file not found, invalid credentials,
    and service availability issues.
    """

    @patch("backend.src.daemon.finops_datalake.ClientSecretCredential")
    @patch("backend.src.daemon.finops_datalake.FinOpsDatalake.load_azure_instances")
    def setUp(self, mock_load_azure_instances, __):
        self.empty_csv_data = (
            "Date,Time,Id,AverageCpuPercentage,MinimumCpuPercentage,MaximumCpuPercentage,"
            "AverageAvailableMemoryGB,MinimumAvailableMemoryGB,MaximumAvailableMemoryGB,Region,"
            "Subscription,ResourceGroup,Name,Size,Family,NbVCpus,MemoryGB,DiskSizeGb,Priority,"
            "Zone,AvailabilitySet,ProximityPlacementGroup,VirtualMachineScaleSet,"
            "ProvisioningState,DisplayStatus,Service,Instance,Component,Environment,Partition,Tags"
        )

        self.current_file_directory = os.path.dirname(os.path.abspath(__file__))
        azure_instances_df = pd.DataFrame(
            {"instance-class": ["test_vm_size", "exist_vm_size"]}
        )
        mock_load_azure_instances.return_value = azure_instances_df

        self.datalake = FinOpsDatalake(
            storage_account_url="https://example.blob.core.windows.net/",
            container_name_read="test-container_read",
            container_name_upload="test-container-upload",
            client_id="test-client-id",
            secret="test-secret",
            tenant_id="test-tenant-id",
        )

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_upload_file_to_datalake_file_not_found_error(self, _):
        """
        Test handling of a FileNotFoundError during file upload.

        Simulates a scenario where the specified file does not exist and
        verifies that an appropriate error message is logged.
        """

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(KnownException):
                self.datalake.upload_file_to_datalake(
                    "non_existent_file.csv", "test_folder_path/"
                )

        self.assertIn(
            "File 'non_existent_file.csv' not found at path ''", log.output[0]
        )

    @patch(
        "backend.src.daemon.finops_datalake.ContainerClient",
        side_effect=ValueError("Invalid credentials"),
    )
    def test_upload_file_to_datalake_value_error(self, _):
        """
        Test handling of a ValueError during file upload.

        Simulates invalid credentials being provided and verifies that
        an appropriate error message is logged.
        """

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(KnownException):
                self.datalake.upload_file_to_datalake(
                    "test_file.csv", "test_folder_path/"
                )

        self.assertIn("Invalid parameter for upload", log.output[0])

    @patch(
        "backend.src.daemon.finops_datalake.ContainerClient",
        side_effect=HttpResponseError("Service unavailable"),
    )
    def test_upload_file_to_datalake_http_response_error(self, _):
        """
        Test handling of an HttpResponseError during file upload.

        Simulates a service availability issue and verifies that an
        appropriate error message is logged.
        """

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(KnownException):
                self.datalake.upload_file_to_datalake(
                    "test_file.csv", "test_folder_path/"
                )

        self.assertIn(
            "Azure HTTP error (status None) while uploading file", log.output[0]
        )

    @patch("builtins.open", side_effect=TypeError("Invalid type"))
    def test_upload_file_to_datalake_type_error(self, _):
        """
        Test handling of a TypeError during file upload.

        Simulates a scenario where a TypeError occurs, and verifies that an
        appropriate error message is logged.
        """

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(KnownException):
                self.datalake.upload_file_to_datalake(
                    "test_file.csv", "test_folder_path/"
                )

        self.assertIn("Type error while uploading file", log.output[0])

    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    @patch(
        "backend.src.daemon.finops_datalake.FinOpsDatalake.create_missing_instances_report"
    )
    def test_read_file_from_datalake_resource_not_found_error(
        self, mock_report, mock_blob_service_client
    ):
        """
        Test handling of a ResourceNotFoundError during file reading.

        Simulates a scenario where the specified file does not exist and
        verifies that the missing_blobs set is updated with the correct number of missing files.
        """
        # Setting up mock BlobServiceClient
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError

        # Call the method with a non-existent file
        self.datalake.read_file_from_datalake(
            {"file_group": ["non_existent_file1.csv", "non_existent_file2.csv"]},
            "test_destination_folder/",
        )

        # Assert the missing_blobs set has the correct length
        args = mock_report.call_args[
            0
        ]  # Capture the arguments passed to create_missing_instances_report
        missing_blobs = args[1]  # The second argument should be the missing_blobs set

        assert {"non_existent_file1.csv", "non_existent_file2.csv"} == missing_blobs

    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    def test_read_file_from_datalake_type_error(self, mock_blob_service_client):
        """
        Test handling of a TypeError during file reading.

        Simulates a scenario where a TypeError occurs and verifies that an appropriate error message is logged.
        """
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.return_value.readall.side_effect = TypeError(
            "Invalid Type"
        )

        with self.assertLogs(level="ERROR") as log:
            self.assertRaises(
                TypeError,
                self.datalake.read_file_from_datalake,
                {"file_group1": "existent_file.csv"},
                "test_destination_folder/",
            )

        self.assertIn("Type error processing file from datalake", log.output[0])

    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    def test_read_file_from_datalake_key_error(self, mock_blob_service_client):
        """
        Test handling of a KeyError during file reading.

        Simulates a scenario where a KeyError occurs and verifies that an appropriate error message is logged.
        """
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.return_value.readall.side_effect = KeyError(
            "File not found"
        )

        with self.assertLogs(level="ERROR") as log:
            self.assertRaises(
                KeyError,
                self.datalake.read_file_from_datalake,
                {"file_group1": "existent_file.csv"},
                "test_destination_folder/",
            )

        self.assertIn(
            "Key error processing file from datalake for file group file_group1",
            log.output[0],
        )

    @patch(
        "backend.src.daemon.finops_datalake.FinOpsDatalake.process_vm_csv_data",
        return_value=True,
    )
    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    def test_read_file_from_datalake_success(
        self, mock_blob_service_client, mock_process_csv_data
    ):
        """
        Test case to handle successful deserialization of a VM from the csv file
        """
        with open(
            os.path.join(self.current_file_directory, "test.csv"), "r", encoding="utf-8"
        ) as test_file:
            sample_csv_data = test_file.read()

        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.return_value.readall.return_value = (
            sample_csv_data.encode("utf-8")
        )

        with self.assertLogs(level="INFO") as log:
            self.datalake.read_file_from_datalake(
                {"test_file_group": ["test.csv"]}, "test_destination_folder/"
            )

        mock_process_csv_data.assert_called_once_with(
            sample_csv_data, {}, defaultdict(set), {}
        )
        self.assertIn("Reading file group 'test_file_group'...", log.output[0])

    @patch(
        "backend.src.daemon.finops_datalake.FinOpsDatalake.process_vm_csv_data",
        return_value=False,
    )
    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    def test_read_file_from_datalake_empty_csv(
        self, mock_blob_service_client, mock_process_csv_data
    ):
        """
        Test handling of empty CSV data.
        """
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.return_value.readall.return_value = (
            self.empty_csv_data.encode("utf-8")
        )

        with self.assertLogs(level="INFO") as log:
            self.datalake.read_file_from_datalake(
                {"file_group": ["empty_file.csv"]}, "test_destination_folder/"
            )

        mock_process_csv_data.assert_called_once()
        self.assertIn("Resource is empty! Skipped file: empty_file.csv", log.output[1])

    @patch("backend.src.daemon.finops_datalake.calculate_vm_count_for_missing_regions")
    @patch("backend.src.utils.helpers.str_to_float", side_effect=float)
    def test_process_csv_data(self, _, mock_calculate_vm_count_for_missing_regions):
        """
        Test process_csv_data with a valid CSV file.

        Verifies that process_csv_data correctly processes CSV data into vm_dict.
        """

        vm_dict = {}
        with open(
            os.path.join(self.current_file_directory, "test.csv"), "r", encoding="utf-8"
        ) as test_file:
            sample_csv_data = test_file.read()

        result = self.datalake.process_vm_csv_data(
            sample_csv_data, vm_dict, defaultdict(set), {}
        )

        self.assertTrue(result)
        self.assertIn("test_id", vm_dict)
        virtual_machine = vm_dict["test_id"]
        self.assertEqual(virtual_machine.id, "test_id")
        self.assertEqual(virtual_machine.region, "francecentral")
        self.assertEqual(virtual_machine.vm_size, "test_vm_size")
        self.assertEqual(virtual_machine.service, "OpenShift")
        self.assertEqual(virtual_machine.component, "other")
        self.assertEqual(virtual_machine.subscription, "amacp-ccp-fc-mng-gob-01")
        self.assertEqual(virtual_machine.name, "test_vm_name")
        self.assertEqual(virtual_machine.instance, "ccp-fc-mgob01a")
        self.assertEqual(virtual_machine.environment, "ccp")
        self.assertEqual(virtual_machine.partition, "")
        self.assertEqual(virtual_machine.carbon_intensity, 44)
        self.assertEqual(virtual_machine.time_points, ["05:10:00"])
        self.assertEqual(virtual_machine.cpu_util, [0.2])
        self.assertEqual(virtual_machine.storage_size, [350.0])
        mock_calculate_vm_count_for_missing_regions.assert_called_once_with(
            {}, "francecentral"
        )

    def test_process_empty_csv_data(self):
        """
        Test process_csv_data with an empty CSV file.

        Verifies that process_csv_data returns False for empty CSV data.
        """
        result = self.datalake.process_vm_csv_data(
            self.empty_csv_data, {}, defaultdict(set), {}
        )
        self.assertFalse(result)

    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    def test_read_parquet_from_datalake_resource_not_found_error(
        self, mock_blob_service_client
    ):
        """
        Test handling of a ResourceNotFoundError during file reading.

        Simulates a scenario where the specified file does not exist and
        verifies that an appropriate error message is logged.
        """
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError

        with self.assertLogs(level="INFO") as log:
            with self.assertRaises(ResourceNotFoundError):
                self.datalake.read_parquet_from_datalake(
                    "folder_path/", "non_existent_file.parquet"
                )

        self.assertIn(
            "Resource not found! Skipped file: non_existent_file.parquet", log.output[0]
        )

    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    @patch("backend.src.daemon.finops_datalake.pq.read_table")
    def test_read_parquet_from_datalake_arrow_invalid_error(
        self, mock_read_table, mock_blob_service_client
    ):
        """
        Test handling of a pyarrow.ArrowInvalid error during Parquet data processing.

        Simulates a scenario where the Parquet file content is invalid and
        verifies that an appropriate error message is logged.
        """
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.return_value.readall.return_value = (
            b"invalid parquet data"
        )

        # Setting up mock read_table to raise ArrowInvalid
        mock_read_table.side_effect = pyarrow.ArrowInvalid

        folder_path = "folder_path/"
        file_name = "invalid_parquet_file.parquet"

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(pyarrow.ArrowInvalid):
                self.datalake.read_parquet_from_datalake(folder_path, file_name)

        self.assertIn("Invalid Parquet data format in file", log.output[0])

    @patch("backend.src.daemon.finops_datalake.BlobServiceClient")
    @patch("backend.src.daemon.finops_datalake.pq.read_table")
    def test_read_parquet_from_datalake_value_error(
        self, mock_read_table, mock_blob_service_client
    ):
        """
        Test handling of a ValueError during Parquet data processing.

        Simulates a scenario where an error occurs during the reading process and
        verifies that an appropriate error message is logged.
        """
        mock_container_client = (
            mock_blob_service_client.return_value.get_container_client.return_value
        )
        mock_blob_client = mock_container_client.get_blob_client.return_value
        mock_blob_client.download_blob.return_value.readall.return_value = (
            b"some parquet data"
        )

        # Setting up mock read_table to raise ValueError
        mock_read_table.side_effect = ValueError

        # Calling the method under test with corrupt Parquet content
        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(ValueError):
                self.datalake.read_parquet_from_datalake(
                    "folder_path/", "corrupt_parquet_file.parquet"
                )

        self.assertIn("Value error processing data in file", log.output[0])

    @patch("backend.src.daemon.finops_datalake.pd.read_csv")
    @patch("backend.src.daemon.finops_datalake.requests.head")
    def test_load_azure_instances_success(self, mock_head, mock_read_csv):
        """
        Test that load_azure_instances successfully loads the CSV data when the URL is accessible.
        """
        # Simulate successful head request
        mock_head.return_value.status_code = 200

        mock_df = pd.DataFrame({"instance-class": ["test_vm_size_1", "test_vm_size_2"]})
        mock_read_csv.return_value = mock_df

        df = self.datalake.load_azure_instances()

        # Assert the read_csv method was called with the correct URL
        mock_read_csv.assert_called_once()

        # Check if the DataFrame is returned correctly
        self.assertEqual(df.shape[0], 2)
        self.assertIn("instance-class", df.columns)
        self.assertIn(["test_vm_size_1", "test_vm_size_2"], df["instance-class"].values)

    @patch("backend.src.daemon.finops_datalake.pd.read_csv")
    @patch(
        "backend.src.daemon.finops_datalake.requests.head", side_effect=RequestException
    )
    def test_load_azure_instances_request_error(self, _, mock_read_csv):
        """
        Test that load_azure_instances raises a KnownException when the URL is not accessible.
        """

        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(RequestException):
                self.datalake.load_azure_instances()

        self.assertIn(
            "Error loading the cloud-metdata-azure-instances.csv file from web",
            log.output[0],
        )
        mock_read_csv.assert_not_called()  # Ensure pandas.read_csv is never called

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.join", return_value="missing_instances_report.txt")
    def test_create_missing_instances_report(self, _, mock_file):
        """
        Test that create_missing_instances_report writes the correct report.
        """
        missing_cloud_instances = {
            "standardEASv4Family": {"vm1", "vm2"},
            "D4s_v3": {"vm3"},
        }
        missing_blobs = {"missing_blob1.csv", "missing_blob2.csv"}

        with self.assertLogs(level="DEBUG") as log:
            FinOpsDatalake.create_missing_instances_report(
                missing_cloud_instances, missing_blobs
            )
            self.assertIn(
                "Missing instances report created with 2 cloud instance types and 2 missing files.",
                "\n".join(log.output),
            )

        mock_file.assert_called_once_with(
            "missing_instances_report.txt", "w", encoding="utf-8"
        )

        # Check that the file was written to properly
        handle = mock_file()
        handle.write.assert_any_call("standardEASv4Family\n")
        handle.write.assert_any_call("D4s_v3\n")
        handle.write.assert_any_call("Total excluded VMs: 3\n\n")
        handle.write.assert_any_call("missing_blob1.csv\n")
        handle.write.assert_any_call("missing_blob2.csv\n")

        # Check that logging was called

    @patch("builtins.open", new_callable=mock_open)
    def test_create_co2_report(self, mock_file):
        """
        Test that create_co2_report writes virtual machine data correctly to the CSV file.
        """
        vms = sample_vms
        storage_resources = sample_storage_resources
        mock_now = datetime.now()
        mock_start_daemon = mock_now - timedelta(days=7)
        with self.assertLogs(level="INFO") as log:
            FinOpsDatalake.create_co2_report(
                vms,
                storage_resources,
                mock_start_daemon.strftime("%Y-%m-%d"),
                TEST_REPORT_FILE_NAME,
            )
            self.assertIn("CSV report created in", log.output[1])

        mock_file.assert_called_once_with(
            TEST_REPORT_FILE_NAME, mode="w", newline="", encoding="utf-8"
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_create_co2_report_headers(self, mock_file):
        """
        Test that create_co2_report writes virtual machine
        data headers correctly to the CSV file.
        """

        vms = sample_vms
        storage_resources = sample_storage_resources
        mock_now = datetime.now()
        mock_start_daemon = mock_now - timedelta(days=7)
        expected_headers = settings.FINOPS.REPORT_HEADERS[0]

        with self.assertLogs(level="INFO") as log:
            FinOpsDatalake.create_co2_report(
                vms,
                storage_resources,
                mock_start_daemon.strftime("%Y-%m-%d"),
                TEST_REPORT_FILE_NAME,
            )
            self.assertIn("CSV report created in", log.output[1])

        # Check the headers of the created CSV file
        mock_file().write.assert_called()
        handle = mock_file()
        written_data = handle.write.call_args_list[0][0][0]
        headers = written_data.strip().split(",")
        self.assertCountEqual(headers, expected_headers)


if __name__ == "__main__":
    unittest.main()
