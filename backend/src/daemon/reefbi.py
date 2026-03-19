"""
This module contains a class to handle interactions with ReefBi
"""

import logging
import os
from azure.core.exceptions import AzureError, HttpResponseError
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


class Reefbi:
    """
    A class for handling interactions with ReefBi.
    It contains methods for pushing and pulling directories from an Azure Blob Storage.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        container_name: str,
        storage_account: str,
    ) -> None:
        self.container_name = container_name
        self.storage_account = storage_account
        self.credential = ClientSecretCredential(
            client_id=client_id, client_secret=client_secret, tenant_id=tenant_id
        )
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.storage_account}.blob.core.windows.net",
            credential=self.credential,
        )

    def push_directory_to_reefbi(
        self, directory_path: str, blob_folder_name: str
    ) -> None:
        """
        Uploads files from a specified directory to a blob storage container in Reefbi.

        Args:
            directory_path (str): The path to the directory containing the files to be uploaded.
            blob_folder_name (str): The name of the folder in the blob storage where the files will be uploaded.

        Raises:
            AzureError: If there is an error uploading a file to the blob storage.
            HttpResponseError: If there is an HTTP response error during the upload process.

        Logs:
            Info: When the upload process starts and when all files are successfully uploaded.
            Error: If there is an error uploading any file.
        """
        logger.info("Uploading files from directory %s to Reefbi", directory_path)
        data_files = [
            f
            for f in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, f)) and "output" in f
        ]
        container_client = self.blob_service_client.get_container_client(
            container=self.container_name
        )
        all_files_uploaded = True
        for file in data_files:
            with open(os.path.join(directory_path, file), "rb") as data:
                try:
                    container_client.upload_blob(
                        name=blob_folder_name + file, data=data, overwrite=True
                    )
                except HttpResponseError:
                    logger.exception("HTTP response error uploading %s to Reefbi", file)
                    all_files_uploaded = False
                    continue
                except AzureError:
                    logger.exception("Azure error uploading %s to Reefbi", file)
                    all_files_uploaded = False
                    continue
        if all_files_uploaded:
            logger.info("Uploaded all files to Reefbi")

    def pull_directory_from_reefbi(
        self, directory_path: str, blob_folder_name: str
    ) -> None:
        """
        Downloads files from a specified blob folder in Reefbi to a local directory.
        Args:
            directory_path (str): The local directory path where the files will be downloaded.
            blob_folder_name (str): The name of the blob folder in Reefbi to download files from.
        Returns:
            None
        Logs:
            - Info: When the download process starts and when all files are successfully downloaded.
            - Error: If there is an error downloading any file from Reefbi.
        """
        logger.info("Downloading files from Reefbi to directory %s", directory_path)
        container_client = self.blob_service_client.get_container_client(
            container=self.container_name
        )
        blobs = container_client.walk_blobs(
            name_starts_with=blob_folder_name, delimiter="/"
        )
        os.makedirs(os.path.join(directory_path, blob_folder_name), exist_ok=True)
        all_files_downloaded = True
        for blob in blobs:
            try:
                blob_client = container_client.get_blob_client(blob.name)
                with open(os.path.join(directory_path, blob.name), "wb") as file:
                    data = blob_client.download_blob().readall()
                    file.write(data)
            except (AzureError, HttpResponseError):
                logger.exception("Error downloading %s from Reefbi", blob.name)
                all_files_downloaded = False
        if all_files_downloaded:
            logger.info("Downloaded all files from Reefbi")
