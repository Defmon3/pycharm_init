# test_google_bucketmanager_parametrized_no_log.py

from unittest.mock import patch

import pytest

# Adjust this import path to where your BucketManager class actually resides
from app.cloud_tools.google_bucketmanager import BucketManager

# Define the bucket name used across tests for consistency
TEST_BUCKET_NAME = "test-bucket"

# Define dummy file paths and names
LOCAL_FILE_PATH = "/fake/local/path/file.txt"
REMOTE_DIR = "remote/folder"
FILE_BASENAME = "file.txt"
FULL_REMOTE_PATH = f"{REMOTE_DIR}/{FILE_BASENAME}"


# Use pytest fixtures to set up the mock environment for multiple tests
@pytest.fixture
def mock_gcs_client():
    """Fixture to mock google.cloud.storage.Client"""
    # Patch only the Client constructor within the google_bucketmanager module
    # Removed patching for 'google_bucketmanager.log'
    with patch('app.cloud_tools.google_bucketmanager.storage.Client') as MockClient:
        # Configure the mock hierarchy
        mock_client_instance = MockClient.return_value
        mock_bucket_instance = mock_client_instance.bucket.return_value
        mock_blob_instance = mock_bucket_instance.blob.return_value

        # Yield the relevant mocks to the tests (excluding MockLog)
        yield {
            "MockClient": MockClient,
            "mock_client_instance": mock_client_instance,
            "mock_bucket_instance": mock_bucket_instance,
            "mock_blob_instance": mock_blob_instance
        }
        # Teardown happens automatically when the 'with' block exits


# --- Test Cases ---

def test_bucketmanager_initialization(mock_gcs_client):
    """Tests if the BucketManager initializes the client and bucket correctly."""
    manager = BucketManager(TEST_BUCKET_NAME)

    mock_gcs_client["MockClient"].assert_called_once_with()
    mock_gcs_client["mock_client_instance"].bucket.assert_called_once_with(TEST_BUCKET_NAME)
    assert manager.bucket == mock_gcs_client["mock_bucket_instance"]
    # Removed assertion for log.debug


@pytest.mark.parametrize(
    "local_path_input, remote_name_input, expected_blob_arg",
    [
        # Case 1: Standard usage with full remote path
        (LOCAL_FILE_PATH, FULL_REMOTE_PATH, FULL_REMOTE_PATH),

        # Case 2: remote_file_name is None (as per current code behaviour)
        # The code currently passes None to blob()
        (LOCAL_FILE_PATH, None, None),

        # Case 3: Different paths
        ("/another/local.zip", "backup/archive.zip", "backup/archive.zip"),
    ],
    ids=[
        "standard_upload",
        "remote_name_is_none",
        "different_paths",
    ]
)
def test_upload_file_scenarios(mock_gcs_client, local_path_input, remote_name_input, expected_blob_arg):
    """Tests various successful upload_file scenarios using parametrization."""
    manager = BucketManager(TEST_BUCKET_NAME)
    manager.upload_file(local_path_input, remote_name_input)

    # Verify interactions based on parameters
    mock_gcs_client["mock_bucket_instance"].blob.assert_called_once_with(expected_blob_arg)
    mock_gcs_client["mock_blob_instance"].upload_from_filename.assert_called_once_with(local_path_input)
    # Removed assertion for log.info
    # Removed assertion for log.warning not called


@pytest.mark.parametrize(
    "exception_to_raise",
    [
        Exception("Generic GCS failure!"),
        ConnectionError("Network unreachable"),
        FileNotFoundError(f"Local file {LOCAL_FILE_PATH} not found"),
        ValueError("Invalid upload argument")
    ],
    ids=[
        "generic_exception",
        "connection_error",
        "file_not_found_error",
        "value_error"
    ]
)
def test_upload_file_exception_handling(mock_gcs_client, exception_to_raise):
    """Tests behavior during upload_file for various exceptions (without checking logs)."""
    # Simulate different errors during the upload call
    mock_gcs_client["mock_blob_instance"].upload_from_filename.side_effect = exception_to_raise

    manager = BucketManager(TEST_BUCKET_NAME)

    # Call the method - we expect it to catch the exception internally and not re-raise
    # If it *did* re-raise, this call would fail the test unless wrapped in pytest.raises
    try:
        manager.upload_file(LOCAL_FILE_PATH, FULL_REMOTE_PATH)
    except Exception as e:
        pytest.fail(f"BucketManager.upload_file unexpectedly raised an exception: {e}")

    # Verify interactions (that the expected methods were still called before the exception)
    mock_gcs_client["mock_bucket_instance"].blob.assert_called_once_with(FULL_REMOTE_PATH)
    mock_gcs_client["mock_blob_instance"].upload_from_filename.assert_called_once_with(LOCAL_FILE_PATH)
    # Removed assertions checking log.warning or lack of log.info


def test_download_file_success(mock_gcs_client):
    """Tests the successful download_file path."""
    manager = BucketManager(TEST_BUCKET_NAME)
    manager.download_file(FULL_REMOTE_PATH, LOCAL_FILE_PATH)

    # Verify interactions
    mock_gcs_client["mock_bucket_instance"].blob.assert_called_once_with(FULL_REMOTE_PATH)
    mock_gcs_client["mock_blob_instance"].download_to_filename.assert_called_once_with(LOCAL_FILE_PATH)
    # Removed assertion for log.debug


def test_delete_file_success(mock_gcs_client):
    """Tests the successful delete_file path."""
    manager = BucketManager(TEST_BUCKET_NAME)
    manager.delete_file(FULL_REMOTE_PATH)

    # Verify interactions
    mock_gcs_client["mock_bucket_instance"].blob.assert_called_once_with(FULL_REMOTE_PATH)
    mock_gcs_client["mock_blob_instance"].delete.assert_called_once_with()
    # Removed assertion for log.debug
