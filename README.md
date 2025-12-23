# Google Cloud Function Template

A Python template for Google Cloud Functions with pre-configured tooling for BigQuery, Cloud Storage, Secret Manager, and Discord notifications.

## Quick Start

1. Click **"Use this template"** → **"Create a new repository"**
2. Clone your new repository
3. Update `pyproject.toml` with your project name
4. Configure `project.env` with your settings
5. Run `uv sync` to install dependencies

## Project Structure

```
├── app/
│   ├── main.py              # Cloud Function entry point
│   ├── config.py            # Pydantic settings configuration
│   ├── custom_exceptions.py # Custom exception definitions
│   ├── discord_hook.py      # Discord webhook notifications
│   └── cloud_tools/
│       ├── google_bigquerymanager.py   # BigQuery operations
│       ├── google_bucketmanager.py     # Cloud Storage operations
│       └── google_secretmanager.py     # Secret Manager operations
├── tests/                   # Test files
├── pyproject.toml           # Project dependencies (uv)
├── project.env              # Environment configuration template
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## Configuration

Copy and edit the environment template:

```bash
cp project.env .env
```

Required variables:
- `PROJECT_ID` - Your GCP project ID
- `REGION` - Deployment region (e.g., `us-central1`)
- `DISCORD_WEBHOOK_URL` - Discord webhook for notifications (optional)

## Development

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run linting
uv run ruff check app/
```

## Included Tools

| Tool | Purpose |
|------|---------|
| **ruff** | Fast Python linter |
| **black** | Code formatter |
| **mypy** | Static type checking |
| **pylint** | Additional linting |
| **pytest** | Testing framework |
| **pre-commit** | Git hooks |

## Cloud Tools

### BigQueryManager
```python
from cloud_tools.google_bigquerymanager import BigQueryManager

bq = BigQueryManager()
await bq.insert_to_bq("dataset.table", data)
results = await bq.query("SELECT * FROM dataset.table")
```

### BucketManager
```python
from cloud_tools.google_bucketmanager import BucketManager

bucket = BucketManager("my-bucket")
bucket.upload_file("local.txt", "remote.txt")
bucket.download_file("remote.txt", "local.txt")
```

### SecretManager
```python
from cloud_tools.google_secretmanager import get_secret, get_secret_env

secret = get_secret("my-secret", "project-id")
env_vars = get_secret_env("my-env-secret", "project-id")
```

## Deployment

Deploy to Google Cloud Functions:

```bash
gcloud functions deploy my-function \
  --gen2 \
  --runtime python312 \
  --region us-central1 \
  --source ./app \
  --entry-point main \
  --trigger-http
```

## License

See individual file headers for licensing information.
