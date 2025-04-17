#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = ["google-cloud-secret-manager", "python-dotenv"]
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
File: google_secretmanager.py
Dependancies
    uv add google-cloud-secret-manager
"""

import io
from typing import Optional
from loguru import logger as log
from dotenv import dotenv_values
from google.cloud import secretmanager


def get_secret(secret_id: str, project_id: str, version: Optional[str] = "latest") -> str:
    """
    Retrieve the secret from Google Secret Manager.

    :param secret_id: Name of the secret.
    :param project_id: Project id where the secret is stored.
    :param version: Version of the secret, defaults to 'latest'.
    :return: The secret as a string.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")


def get_secret_env(secret_id: str, project_id: str, version: Optional[str] = "latest") -> dict[str, str]:
    """
    Retrieve and parse the secret as dotenv format.

    :param secret_id: Name of the secret.
    :param project_id: Project id where the secret is stored.
    :param version: Version of the secret, defaults to 'latest'.
    :return: A dictionary of environment variables.
    """
    secret_str = get_secret(secret_id, project_id, version)
    env_vars = dotenv_values(stream=io.StringIO(secret_str))

    if not env_vars:
        log.opt(depth=1).error("Failed to parse secret as dotenv format: Empty or invalid format.")
        raise ValueError("Failed to parse secret as dotenv format: Empty or invalid format.")
    return env_vars


if __name__ == "__main__":
    import os

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/path/to/credentials.json"
