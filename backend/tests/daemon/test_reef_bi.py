# pylint: disable=redefined-outer-name
"""
This module contains unit tests for the Reefbi class in the backend.src.daemon.reefbi module.
"""
import os
from unittest.mock import ANY, call, mock_open, patch, MagicMock
import pytest
from backend.src.daemon.reefbi import Reefbi


@pytest.fixture
def mock_blob_service_client() -> tuple[MagicMock, MagicMock]:
    """
    Fixture to mock the Azure Blob Service Client and Container Client.
    """
    mock_client = MagicMock()
    mock_container_client = MagicMock()
    mock_client.get_container_client.return_value = mock_container_client
    return mock_client, mock_container_client


@patch("builtins.open", new_callable=mock_open)
@patch("os.listdir")
@patch("os.path.isfile")
def test_push_directory_to_reef_bi(
    mock_is_file: MagicMock,
    mock_list_dir: MagicMock,
    mock_open: MagicMock,
    mock_blob_service_client: tuple,
) -> None:
    """
    Test case for successful push with the right files to reefbi.
    """
    mock_client, mock_container_client = mock_blob_service_client
    mock_list_dir.return_value = ["output1.yaml", "output2.yaml", "inpu1.yaml"]
    mock_is_file.return_value = True
    reefbi = Reefbi(
        "test-client-id",
        "test-client-secret",
        "test-tenant-id",
        "test-container-name",
        "test-storage-account-name",
    )
    reefbi.blob_service_client = mock_client
    reefbi.container_name = "test-container"
    reefbi.push_directory_to_reefbi("/test-directory", "/desired-directory/")

    assert mock_container_client.upload_blob.call_count == 2

    expected_calls = [
        call.upload_blob(
            name="/desired-directory/output1.yaml", data=ANY, overwrite=True
        ),
        call.upload_blob(
            name="/desired-directory/output2.yaml", data=ANY, overwrite=True
        ),
    ]

    mock_container_client.assert_has_calls(expected_calls, any_order=True)


@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_pull_directory_from_reefbi(
    mock_open: MagicMock, mock_makedirs: MagicMock, mock_blob_service_client: tuple
) -> None:
    """
    Test case for successful pull from reefbi.
    """
    mock_client, mock_container_client = mock_blob_service_client
    mock_blob = MagicMock()
    mock_blob.name = "desired-directory/output1.yaml"
    mock_container_client.walk_blobs.return_value = [mock_blob]
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.return_value.readall.return_value = b"test-data"
    mock_container_client.get_blob_client.return_value = mock_blob_client

    reefbi = Reefbi(
        "test-client-id",
        "test-client-secret",
        "test-tenant-id",
        "test-container-name",
        "test-storage-account-name",
    )
    reefbi.blob_service_client = mock_client
    reefbi.container_name = "test-container"
    reefbi.pull_directory_from_reefbi("/test-directory", "desired-directory")

    mock_makedirs.assert_called_once_with(
        os.path.join("/test-directory", "desired-directory"), exist_ok=True
    )
    mock_blob_client.download_blob.return_value.readall.assert_called_once()
    mock_open.return_value.write.assert_called_once_with(b"test-data")
