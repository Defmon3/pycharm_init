#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = ["google-cloud-logging", "loguru"]
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
File: logging_setup.py
"""

import os
import sys

from loguru import logger


IS_GOOGLE_CLOUD = "K_SERVICE" in os.environ

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


if IS_GOOGLE_CLOUD:
    logger.remove(0)
    try:
        import google.cloud.logging
        from google.cloud.logging.handlers import CloudLoggingHandler

        client = google.cloud.logging.Client()

        gcp_handler = CloudLoggingHandler(client, name=f"{os.environ['K_SERVICE']}-logs")

        logger.add(
            gcp_handler,
            level=LOG_LEVEL,
            format="{message}",  # Let GCP handler do the formatting
            enqueue=True,  # Recommended for performance
            catch=True,  # Catch errors within the sink
        )
        # Log confirmation *using the configured logger*
        logger.info(f"Logger configured for GCP environment. Level: {LOG_LEVEL}")

    except ImportError:
        logger.warning("google-cloud-logging library not found.")
        logger.warning("Falling back to basic JSON logging to stdout for GCP environment.")
        logger.add(sys.stdout, level=LOG_LEVEL, serialize=True, enqueue=True, catch=True)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Error setting up Google Cloud Logging handler. Falling back.", exc_info=True)
        logger.add(sys.stdout, level=LOG_LEVEL, serialize=True, enqueue=True, catch=True)

else:

    logger.info(f"Logger configured for LOCAL environment. Level: {LOG_LEVEL}")
