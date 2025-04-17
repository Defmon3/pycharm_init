#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = []
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
File: google_bucketmanager.py
"""
import re
from typing import Optional

from google.cloud import storage

from loguru import logger as log


def validate_bucket_name(name: str) -> str:
    """
    Validates the GCS bucket name according to Google Cloud Storage naming conventions.
    :param name:
    :return:
    """
    pattern = r"^[a-z0-9](?:[-a-z0-9]{1,61}[a-z0-9])?$"
    if not re.match(pattern, name):
        raise ValueError(f"Invalid bucket name: {name!r}")
    return name


class BucketManager:
    """
    Manages file operations within a Google Cloud Storage bucket.
    Allows specifying a default remote folder for convenience.
    """

    def __init__(self, bucket_name: str):
        """
        Initializes the BucketManager.

        :param bucket_name: Name of the GCS bucket.
        """
        validate_bucket_name(bucket_name)
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

        log.debug(f"Initialized BucketManager for bucket: {self.bucket_name}'")

    def upload_file(self, local_file_path: str, remote_file_name: Optional[str] = None) -> None:
        """
        Uploads a local file. If remote_file_name is None, defaults to the
        local filename placed within self.remote_folder (if set). If remote_file_name
        is provided, it's used directly (should be the full desired path).

        :param local_file_path: Local path of the file to upload.
        :param remote_file_name: Optional full desired path in the bucket.
        """

        try:

            blob = self.bucket.blob(remote_file_name)
            blob.upload_from_filename(local_file_path)
        except Exception as e:  # pylint: disable=W0718
            log.warning(f"Failed to upload {local_file_path} to {self.bucket_name} {e}.")
        log.info(f"Uploaded {local_file_path} to {self.bucket_name}/{remote_file_name}.")

    def download_file(self, remote_file_name: str, local_file_path: str) -> None:
        """
        Downloads a file. If remote_file_name is just a filename (no slashes)
        and self.remote_folder is set, it prepends the remote_folder. Otherwise,
        it assumes remote_file_name is the full path.

        :param remote_file_name: Path or filename of the blob to download.
        :param local_file_path: Local path to save the downloaded file.
        """
        blob = self.bucket.blob(remote_file_name)
        blob.download_to_filename(local_file_path)
        log.debug(f"Downloaded {self.bucket_name}/{remote_file_name} to {local_file_path}.")

    def delete_file(self, remote_file_name: str) -> None:
        """
        Deletes a file. If remote_file_name is just a filename (no slashes)
        and self.remote_folder is set, it prepends the remote_folder. Otherwise,
        it assumes remote_file_name is the full path.

        :param remote_file_name: Path or filename of the blob to delete.
        """

        blob = self.bucket.blob(remote_file_name)
        blob.delete()
        log.debug(f"Deleted {self.bucket_name}/{remote_file_name}.")
