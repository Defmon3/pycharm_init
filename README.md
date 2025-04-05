# Project Name

Brief description of the project, its purpose, and scope.  
Example: Scrapes data from an API and stores it in BigQuery with deduplication. Intended for **non-commercial** use.

## Requirements

- A **Google Cloud** project with **billing enabled**
- A **Google Cloud Service Account** with necessary permissions
- Any required **API tokens** or credentials

Install dependencies using [uv](https://github.com/astral-sh/uv):

```bash
uv venv
uv add package1 package2 ...
```



## Cloud Deployment

Use `deploy.py` to deploy as a Google Cloud Function:

```bash
python deploy.py
```

This will:
- Deploy the function
- Configure IAM
- (Optional) Set up Cloud Scheduler

## Local Testing

To run locally using [Functions Framework](https://cloud.google.com/functions/docs/functions-framework):

Install the framework:

```bash
uv venv
uv add functions-framework
```

Run the local server:

```bash
cd app
functions-framework --target=main --debug
```

Test it:

```bash
curl http://localhost:8080
```

## Internals

- `main.py`: Entrypoint and task loop
- `bigquerymanager.py`: Handles BigQuery inserts and queries
- `util.py`: Loads config, parses tasks, deduplicates
- `discord_hook.py`: Sends logs via Discord
- `deploy.py`: Handles deployment logic

## License

```
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/yourname — Non-commercial use only.
Commercial use requires permission.
```

