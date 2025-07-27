#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = []
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: config.py
uv add pydantic pydantic-settings pydantic[email] --no-cache-dir
"""

from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration settings for the application.
    Loads environment variables from `project.env` file and provides type-safe access
    to application settings.
    """
    service_name: str = Field(..., alias="SERVICE_NAME")
    project_id: str = Field(..., alias="PROJECT_ID")
    region: str = Field(..., alias="REGION")
    runtime: str = Field(..., alias="RUNTIME")
    timeout: int = Field(..., alias="TIMEOUT")
    runtime_service_account_email: EmailStr = Field(..., alias="RUNTIME_SERVICE_ACCOUNT_EMAIL")
    discord_hook_url: str = Field(..., alias="DISCORD_HOOK_URL")

    model_config = {
        "env_file": "project.env",
        "case_sensitive": False,
        "extra": "allow",
    }


settings = Settings()
