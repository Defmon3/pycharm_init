"""
BigQueryManager class to interact with BigQuery

pip install google-cloud-bigquery google-auth loguru

If run locally, BQM requires a path to the credentials file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

author: github.com/defmon3
"""

from typing import Dict, Any, List, Sequence, Generator

import google
from google.cloud import bigquery
from loguru import logger as log


def batch_generator(data: List[Dict[str, Any]], batch_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """Yield successive batches from data."""
    for start in range(0, len(data), batch_size):
        yield data[start : start + batch_size]


class BigQueryManager:
    """
    Class to handle database operations for BigQuery.
    """

    def __init__(self):
        credentials, _ = google.auth.default()
        self.client = bigquery.Client(credentials=credentials)

    async def insert_to_bq(self, table_name: str, data: List[Dict[str, Any]], batch_size: int = 1000) -> Sequence[dict] | None:
        """
        Split data in to batches and stream it to bigquery
        :param table_name:
        :param data:
        :param batch_size:
        :return:
        """
        try:
            for batch in batch_generator(data, batch_size):
                if errors := self.client.insert_rows_json(table_name, batch):
                    log.opt(depth=1).error(f"[{table_name}] {errors}")
                    return errors
        except google.api_core.exceptions.BadRequest as e:  # type: ignore
            log.opt(depth=1).error(f"[{table_name}] Insert: {e}")
            log.opt(depth=2).error(f"[{table_name}] Insert: {e}")
        return None

    async def query(self, query: str) -> list[dict]:
        """
        :param query: SQL query
        :return: list of dictionaries with the result
        """
        query_job = self.client.query(query)
        return [dict(row) for row in query_job.result()]
