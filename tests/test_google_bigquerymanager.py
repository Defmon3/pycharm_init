# tests/test_google_bigquerymanager.py
"""
Unit Tests for the BigQueryManager class (Original Version).

Verifies the interaction patterns with the BigQuery API client
for the version that uses synchronous client calls within async methods,
without using asyncio.to_thread.
"""

import pytest
import google.auth
from google.cloud import bigquery
from google.api_core import exceptions as google_exceptions
from unittest.mock import patch, MagicMock

# Adjust import path as needed
from app.cloud_tools.google_bigquerymanager import BigQueryManager, batch_generator

# --- Test Data ---
TEST_TABLE = "my_project.my_dataset.my_table"
TEST_QUERY = "SELECT col_a, col_b FROM my_table LIMIT 10"
SAMPLE_DATA = [
    {"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}, {"col1": 3, "col2": "c"},
]

# --- Fixtures ---
@pytest.fixture
def mock_bq_client():
    """Mocks google.auth.default and bigquery.Client"""
    auth_patch_target = 'app.cloud_tools.google_bigquerymanager.google.auth.default'
    client_patch_target = 'app.cloud_tools.google_bigquerymanager.bigquery.Client'

    with patch(auth_patch_target) as mock_auth_default, \
         patch(client_patch_target) as MockBQClient:

        # Simulate google.auth.default returning credentials tuple
        mock_credentials = MagicMock(spec=google.auth.credentials.Credentials)
        # The user's code doesn't capture the project_id from default() here
        mock_auth_default.return_value = (mock_credentials, 'mock-project-id')

        mock_client_instance = MockBQClient.return_value

        yield {
            "mock_auth_default": mock_auth_default,
            "MockBQClient": MockBQClient,
            "mock_client_instance": mock_client_instance,
            "mock_credentials": mock_credentials
        }

# --- Test Cases ---

# This is a standard sync function - no asyncio mark needed
def test_bigquerymanager_initialization(mock_bq_client):
    """Tests correct initialization using mocked ADC."""
    manager = BigQueryManager()
    mock_bq_client["mock_auth_default"].assert_called_once_with()
    # The user's code calls Client(credentials=...) - it doesn't pass project here
    mock_bq_client["MockBQClient"].assert_called_once_with(
        credentials=mock_bq_client["mock_credentials"]
    )
    assert manager.client == mock_bq_client["mock_client_instance"]

# Apply mark only to async def tests
@pytest.mark.asyncio
async def test_insert_to_bq_success(mock_bq_client):
    """Tests successful insertion with no errors returned by the client."""
    manager = BigQueryManager()
    mock_client = mock_bq_client["mock_client_instance"]
    mock_client.insert_rows_json.return_value = [] # No errors

    errors = await manager.insert_to_bq(TEST_TABLE, SAMPLE_DATA, batch_size=2)

    assert errors is None
    assert mock_client.insert_rows_json.call_count == 2
    call_args_list = mock_client.insert_rows_json.call_args_list
    assert call_args_list[0][0] == (TEST_TABLE, SAMPLE_DATA[0:2])
    assert call_args_list[1][0] == (TEST_TABLE, SAMPLE_DATA[2:3])

@pytest.mark.asyncio
async def test_insert_to_bq_with_errors(mock_bq_client):
    """Tests insertion where the client returns errors."""
    manager = BigQueryManager()
    mock_client = mock_bq_client["mock_client_instance"]
    returned_errors = [{"index": 0, "errors": ["Some BQ Error"]}]
    mock_client.insert_rows_json.return_value = returned_errors

    errors = await manager.insert_to_bq(TEST_TABLE, SAMPLE_DATA, batch_size=2)

    assert errors == returned_errors
    mock_client.insert_rows_json.assert_called_once_with(TEST_TABLE, SAMPLE_DATA[0:2])

@pytest.mark.asyncio
async def test_insert_to_bq_api_error(mock_bq_client):
    """Tests insertion catching a google.api_core.exceptions.BadRequest."""
    manager = BigQueryManager()
    mock_client = mock_bq_client["mock_client_instance"]
    bq_api_exception = google_exceptions.BadRequest("Invalid request")
    mock_client.insert_rows_json.side_effect = bq_api_exception

    # Call the method - expect it to catch the error and return None
    # Patch the logger used inside the except block to avoid actual logging during test
    with patch('app.cloud_tools.google_bigquerymanager.log') as mock_log:
        errors = await manager.insert_to_bq(TEST_TABLE, SAMPLE_DATA, batch_size=2)

    assert errors is None # Should return None when BadRequest is caught
    mock_client.insert_rows_json.assert_called_once_with(TEST_TABLE, SAMPLE_DATA[0:2])
    # Optionally check log was called
    assert mock_log.opt.call_count == 2 # Called twice in the except block
    assert mock_log.opt().error.call_count == 2


@pytest.mark.asyncio
async def test_query_success(mock_bq_client):
    """Tests a successful query execution."""
    manager = BigQueryManager()
    mock_client = mock_bq_client["mock_client_instance"]
    mock_query_job = MagicMock(spec=bigquery.QueryJob)
    # Simulate rows supporting dict conversion
    mock_result_rows = [
        bigquery.Row(("valueA1", 11), {"col_a": 0, "col_b": 1}),
        bigquery.Row(("valueA2", 22), {"col_a": 0, "col_b": 1}),
    ]
    mock_query_job.result.return_value = mock_result_rows
    mock_client.query.return_value = mock_query_job

    expected_results = [
        {"col_a": "valueA1", "col_b": 11},
        {"col_a": "valueA2", "col_b": 22},
    ]

    results = await manager.query(TEST_QUERY)

    mock_client.query.assert_called_once_with(TEST_QUERY)
    mock_query_job.result.assert_called_once_with()
    assert results == expected_results

@pytest.mark.asyncio
async def test_query_execution_error(mock_bq_client):
    """Tests query execution when job.result() raises an error."""
    manager = BigQueryManager()
    mock_client = mock_bq_client["mock_client_instance"]
    mock_query_job = MagicMock(spec=bigquery.QueryJob)
    query_exception = google_exceptions.Forbidden("Access Denied") # Or any other exception
    mock_query_job.result.side_effect = query_exception
    mock_client.query.return_value = mock_query_job

    # Expect the exception to propagate since the original code doesn't catch it here
    with pytest.raises(google_exceptions.Forbidden):
         await manager.query(TEST_QUERY)

    # Verify calls leading up to the error
    mock_client.query.assert_called_once_with(TEST_QUERY)
    mock_query_job.result.assert_called_once_with()


# This is a standard sync function - no asyncio mark needed
def test_batch_generator():
    """Tests the batch_generator utility function."""
    data = list(range(10))
    assert list(batch_generator(data, 3)) == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    assert list(batch_generator(data, 15)) == [list(range(10))]
    assert list(batch_generator([], 5)) == []
    # Batch generator doesn't check for 0 size in user's code, range(0,10,0) would loop forever
    # Add check if desired:
    # with pytest.raises(ValueError):
    #     list(batch_generator(data, 0))