#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = []
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: discord_hook.py

"""


import asyncio
import io
import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

import httpx
from loguru import logger as log

MAX_LEN = 2000
MAX_VISIBLE_ERROR_LENGTH = 1000
DISCORD_AT_MENTION = os.environ.get("DISCORD_AT_MENTION", "")
DEFAULT_MESSAGE_FORMATS: dict[str, str] = {
    "default": "{message}",
    "debug": "🛠️ **Debug:** {message}",
    "info": "ℹ️ {message}",
    "success": "✅ {message}",
    "fail": f"❌ {DISCORD_AT_MENTION}" + " {message}",
    "warning": "⚠️ **Warning:** {message}",
    "error": f"🚨 {DISCORD_AT_MENTION}" + "**Error:** {message}",
    "critical": f"💥 {DISCORD_AT_MENTION}" + " **Critical:** {message}",
    "code": "```{message}```",
}


@dataclass
class DiscordAttachment:
    """Represents content to be sent as a file attachment."""

    content: Optional[str] = None
    filename: str = "details.log"
    buffer: io.BytesIO = field(init=False, default_factory=io.BytesIO)
    prepared: bool = field(init=False, default=False)

    def prepare(self) -> bool:
        """Encodes content to bytes and prepares the BytesIO buffer."""
        if not self.content:
            self.prepared = False
            return False
        try:
            attachment_bytes = self.content.encode("utf-8")
            self.buffer = io.BytesIO(attachment_bytes)
            self.prepared = True
            return True
        except Exception as buf_err:  # pylint: disable=broad-except
            log.exception("Failed to create file buffer for attachment. Error:" f" {buf_err}")
            self.prepared = False
            return False

    def get_file_tuple(self) -> Optional[Tuple[str, io.BytesIO, str]]:
        """Returns the tuple needed for httpx files argument."""
        if self.prepared:
            self.buffer.seek(0)
            return (self.filename, self.buffer, "text/plain")
        return None

    def close(self) -> None:
        """Closes the buffer."""
        if hasattr(self, "buffer") and self.buffer:
            self.buffer.close()


def _format_discord_message(
    message: str,
    msg_type: str,
    message_formats: Optional[dict[str, str]],
    func_name: str,
) -> str:
    """Formats and truncates the main message content."""
    formats = message_formats if message_formats is not None else DEFAULT_MESSAGE_FORMATS
    format_string = formats.get(msg_type, formats.get("default", "{message}"))
    try:
        formatted_message = format_string.format(message=message)
    except KeyError as fmt_err:
        log.error(f"{func_name}: Invalid format key {fmt_err}. Using raw.")
        formatted_message = message

    if len(formatted_message) > MAX_LEN:
        log.warning(f"{func_name}: Message length ({len(formatted_message)})" f" exceeds {MAX_LEN}. Truncating.")
        formatted_message = f"{formatted_message[:MAX_LEN - 10]}... [CUT]"
    return formatted_message


def _prepare_request_args(formatted_message: str, attachment: Optional[DiscordAttachment]) -> dict[str, Any]:
    """Prepares arguments for httpx.post based on attachment presence."""
    payload_json = {"content": formatted_message}
    request_args: dict[str, Any] = {"json": payload_json}

    if attachment and attachment.prepare():
        if file_tuple := attachment.get_file_tuple():
            request_args = {
                "data": {"payload_json": json.dumps(payload_json)},
                "files": {"file": file_tuple},
            }
        else:
            payload_json["content"] += "\n\n⚠️ *Failed to attach error log.*"
            if len(payload_json["content"]) > MAX_LEN:
                payload_json["content"] = f"{payload_json['content'][:MAX_LEN - 10]}... [CUT]"
            request_args = {"json": payload_json}
    return request_args


async def _send_request(client: httpx.AsyncClient, webhook_url: str, request_args: dict[str, Any]) -> bool:
    """Sends the HTTP request using httpx."""
    func_name = "send_discord_message._send_request"
    try:
        response = await client.post(webhook_url, **request_args)
        response.raise_for_status()
        log.debug(f"{func_name}: Discord message sent (status" f" {response.status_code}).")
        return True
    except httpx.HTTPStatusError as e:
        log.warning(f"HTTP error in {func_name}: Status {e.response.status_code}" f" for URL {e.request.url}. Response: {e.response.text}")
    except httpx.RequestError as e:
        url_str = str(e.request.url) if e.request else "unknown URL"
        log.error(f"Network error in {func_name} sending to {url_str}:" f" {type(e).__name__} - {e}")
    except Exception as e:  # pylint: disable=broad-except
        log.exception(f"Unexpected error during HTTP request in {func_name}:" f" {type(e).__name__} - {e}")
    return False


# ruff: noqa: PLR0913
# pylint: disable=too-many-arguments, too-many-positional-arguments
async def send_discord_message(
    webhook_url: str,
    message: str,
    msg_type: str = "default",
    message_formats: Optional[dict[str, str]] = None,
    timeout: float = 10.0,
    attachment: Optional[DiscordAttachment] = None,
) -> bool | None:
    """Sends a formatted message asynchronously to Discord.

    Optionally includes a file attachment. Uses httpx.AsyncClient and
    standard try-except blocks for error handling.

    Args:
        webhook_url: The target Discord webhook URL.
        message: The core content of the message (< 2000 chars).
        msg_type: Key for message format in `message_formats`.
        message_formats: Dictionary mapping type keys to format strings.
                         Defaults to DEFAULT_MESSAGE_FORMATS.
        timeout: Request timeout in seconds.
        attachment: A DiscordAttachment object with content and filename.

    Returns:
        True if the message was successfully sent, False otherwise.
    """
    func_name = "send_discord_message"

    if not webhook_url or not isinstance(webhook_url, str):
        log.warning(f"{func_name}: Discord webhook URL invalid.")
        return False
    if not message and not (attachment and attachment.content):
        log.warning(f"{func_name}: Message empty and no attachment. Sending aborted.")
        return False
    if not message:
        message = ""

    formatted_message = _format_discord_message(message, msg_type, message_formats, func_name)
    request_args = _prepare_request_args(formatted_message, attachment)
    success = False

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            success = await _send_request(client, webhook_url, request_args)
    except Exception as client_err:  # pylint: disable=broad-except
        log.exception(f"Unexpected error creating/using httpx client in {func_name}:" f" {client_err}")
        success = False
    finally:
        if attachment:
            attachment.close()

    return success


def handle_return(url: str, message: str, error: Optional[str] = None) -> dict[str, Any]:
    """Handles return value, prepares Discord msg, sends status update.

    Prepares Discord message by potentially truncating the visible error
    and attaching the full error log. Sends the update via Discord.

    Args:
        url: The webhook URL for the status update.
        message: The original message or operation description.
        error: The full error message (potentially including traceback).

    Returns:
        A dictionary containing the status details (with full error).
    """
    is_failure = error is not None
    visible_error_snippet = ""
    attachment: Optional[DiscordAttachment] = None
    _ = ""
    msg_format = "success"

    if is_failure and error is not None:
        attachment = DiscordAttachment(
            content=error,
            filename=f"{os.getenv('K_SERVICE', 'app')}_error.log",
        )
        msg_format = "error"

        if len(error) > MAX_VISIBLE_ERROR_LENGTH:
            visible_error_snippet = error[-MAX_VISIBLE_ERROR_LENGTH:]
            visible_error_snippet = "... (Full log attached)\n```\n" f"{visible_error_snippet}\n```"
        else:
            visible_error_snippet = f"(Full log attached)\n```\n{error}\n```"

    result_status: dict[str, Any] = {
        "status": "failed" if is_failure else "ok",
        "message": message,
        "region": os.getenv("REGION"),
        "service": os.getenv("K_SERVICE"),
        "revision": os.getenv("K_REVISION"),
        "target-function": os.getenv("FUNCTION_TARGET"),
        "error": (visible_error_snippet if is_failure else ""),
    }

    try:
        asyncio.run(
            send_discord_message(
                webhook_url=url,
                message=json.dumps(result_status, ensure_ascii=False),
                msg_type=msg_format,
                attachment=attachment,
            )
        )
    except RuntimeError as re:
        log.error(f"Could not send Discord notification: asyncio error: {re}")
    except Exception as e:  # pylint: disable=broad-except
        log.exception(f"Failed to send Discord notification within handle_return: {e}")

    return result_status
