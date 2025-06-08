import traceback
from typing import Any

import pendulum
from loguru import logger as log

from discord_hook import handle_return
from config import settings


def main(request) -> dict[str, Any]:
    try:
        start = pendulum.now()

        req_json = request.get_json(silent=True) or {}

        end = pendulum.now()

        return handle_return(
            settings.discord_hook_url,
            f"completed in : {end.diff_for_humans(start, absolute=True)}",
        )
    except Exception as e:
        return handle_return(
            settings.discord_hook_url, f"Error {e}", traceback.format_exc()
        )
