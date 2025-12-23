"""
BigQueryManager class to interact with BigQuery

pip install google-cloud-bigquery google-auth loguru

If run locally, BQM requires a path to the credentials file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

author: github.com/defmon3
"""

import asyncio
from functools import partial
from typing import Any, Generator, Sequence

import google
from google.cloud import bigquery
from loguru import logger as log


def batch_generator(data: list[dict[str, Any]], batch_size: int) -> Generator[list[dict[str, Any]], None, None]:
    """Yield successive batches from data."""
    for start in range(0, len(data), batch_size):
        yield data[start : start + batch_size]


class BigQueryManager:
    """
    Class to handle database operations for BigQuery.
    """

    def __init__(self) -> None:
        credentials, _ = google.auth.default()
        self.client = bigquery.Client(credentials=credentials)

    async def insert_to_bq(
        self, table_name: str, data: list[dict[str, Any]], batch_size: int = 1000
    ) -> Sequence[dict[str, Any]] | None:
        """
        Split data in to batches and stream it to bigquery
        :param table_name:
        :param data:
        :param batch_size:
        :return:
        """
        loop = asyncio.get_running_loop()
        try:
            for batch in batch_generator(data, batch_size):
                errors = await loop.run_in_executor(
                    None, partial(self.client.insert_rows_json, table_name, batch)
                )
                if errors:
                    log.opt(depth=1).error(f"[{table_name}] {errors}")
                    return errors
        except google.api_core.exceptions.BadRequest as e:  # type: ignore
            log.opt(depth=1).error(f"[{table_name}] Insert: {e}")
        return None

    async def query(self, query_str: str) -> list[dict[str, Any]]:
        """
        :param query_str: SQL query
        :return: list of dictionaries with the result
        """
        loop = asyncio.get_running_loop()
        query_job = await loop.run_in_executor(None, self.client.query, query_str)
        result = await loop.run_in_executor(None, query_job.result)
        return [dict(row) for row in result]
