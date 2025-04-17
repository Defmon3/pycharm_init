# tests/test_google_secretmanager.py

from unittest.mock import patch, MagicMock

import pytest

# Adjust this import path to where your functions actually reside
from app.cloud_tools.google_secretmanager import get_secret, get_secret_env

# --- Constants for Tests ---
TEST_SECRET_ID = "my-test-secret"
TEST_PROJECT_ID = "my-test-project"
DEFAULT_VERSION = "latest"
SPECIFIC_VERSION = "5"


# --- Fixture for mocking SecretManagerServiceClient ---
@pytest.fixture
def mock_sm_client():
    """Mocks the SecretManagerServiceClient and its response."""
    # Patch the client where it's looked up in the target module
    patch_target = 'app.cloud_tools.google_secretmanager.secretmanager.SecretManagerServiceClient'
    with patch(patch_target) as MockSecretClient:
        # Configure the mock client instance
        mock_client_instance = MockSecretClient.return_value

        # Configure the response object structure
        mock_response = MagicMock()
        mock_payload = MagicMock()
        # Important: payload.data needs to be bytes
        mock_payload.data = b"RAW_SECRET_DATA"
        mock_response.payload = mock_payload

        # Make the client's method return the configured response
        mock_client_instance.access_secret_version.return_value = mock_response

        yield {
            "MockSecretClient": MockSecretClient,
            "mock_client_instance": mock_client_instance,
            "mock_response": mock_response,
            "mock_payload": mock_payload
        }


# --- Fixture for mocking the internal get_secret call ---
@pytest.fixture
def mock_get_secret_call():
    """Mocks the call to get_secret within the same module."""
    patch_target = 'app.cloud_tools.google_secretmanager.get_secret'
    with patch(patch_target) as MockGetSecret:
        yield MockGetSecret


# --- Tests for get_secret ---

def test_get_secret_success_latest(mock_sm_client):
    """Tests get_secret retrieving the latest version successfully."""
    expected_name = f"projects/{TEST_PROJECT_ID}/secrets/{TEST_SECRET_ID}/versions/{DEFAULT_VERSION}"
    expected_result = "RAW_SECRET_DATA"  # Result of decode("UTF-8")

    # Set the bytes payload for this test
    mock_sm_client["mock_payload"].data = expected_result.encode('utf-8')

    result = get_secret(TEST_SECRET_ID, TEST_PROJECT_ID)  # Version defaults to latest

    # Assertions
    mock_sm_client["MockSecretClient"].assert_called_once_with()  # Client initialized
    mock_sm_client["mock_client_instance"].access_secret_version.assert_called_once_with(
        name=expected_name
    )
    assert result == expected_result


def test_get_secret_success_specific_version(mock_sm_client):
    """Tests get_secret retrieving a specific version successfully."""
    expected_name = f"projects/{TEST_PROJECT_ID}/secrets/{TEST_SECRET_ID}/versions/{SPECIFIC_VERSION}"
    expected_result = "SPECIFIC_VERSION_DATA"

    # Set the bytes payload for this test
    mock_sm_client["mock_payload"].data = expected_result.encode('utf-8')

    result = get_secret(TEST_SECRET_ID, TEST_PROJECT_ID, version=SPECIFIC_VERSION)

    # Assertions
    mock_sm_client["MockSecretClient"].assert_called_once_with()
    mock_sm_client["mock_client_instance"].access_secret_version.assert_called_once_with(
        name=expected_name
    )
    assert result == expected_result


# --- Tests for get_secret_env ---

def test_get_secret_env_success(mock_get_secret_call):
    """Tests get_secret_env successfully parsing a valid dotenv string."""
    secret_content = "KEY1=VALUE1\nKEY2=VALUE2\n#COMMENT\nKEY3='VALUE 3'"
    expected_dict = {"KEY1": "VALUE1", "KEY2": "VALUE2", "KEY3": "VALUE 3"}

    # Configure the mock get_secret to return the fake content
    mock_get_secret_call.return_value = secret_content

    result = get_secret_env(TEST_SECRET_ID, TEST_PROJECT_ID, version=DEFAULT_VERSION)

    # Assertions
    mock_get_secret_call.assert_called_once_with(
        TEST_SECRET_ID, TEST_PROJECT_ID, DEFAULT_VERSION
    )
    assert result == expected_dict


@pytest.mark.parametrize(
    "invalid_secret_content",
    [
        "",  # Empty string
        "# JUST A COMMENT",  # Only comments
        "\n   \n",  # Whitespace only
    ],
    ids=[
        "empty_string",
        "comment_only",
        "whitespace_only",
    ]
)
def test_get_secret_env_parsing_failure(mock_get_secret_call, invalid_secret_content):
    """Tests get_secret_env raising ValueError for non-parsable content."""
    # Configure the mock get_secret to return the invalid content
    mock_get_secret_call.return_value = invalid_secret_content

    with pytest.raises(ValueError) as excinfo:
        get_secret_env(TEST_SECRET_ID, TEST_PROJECT_ID)

    # Assertions
    mock_get_secret_call.assert_called_once_with(
        TEST_SECRET_ID, TEST_PROJECT_ID, DEFAULT_VERSION  # Checks default version is used
    )
    # Check if the exception message is as expected (optional but good)
    assert "Failed to parse secret as dotenv format" in str(excinfo.value)


def test_get_secret_env_passes_version(mock_get_secret_call):
    """Tests that get_secret_env passes the version argument correctly."""
    mock_get_secret_call.return_value = "KEY=VALUE"  # Need some valid return value

    get_secret_env(TEST_SECRET_ID, TEST_PROJECT_ID, version=SPECIFIC_VERSION)

    # Assertion
    mock_get_secret_call.assert_called_once_with(
        TEST_SECRET_ID, TEST_PROJECT_ID, SPECIFIC_VERSION  # Check specific version was passed
    )
