```bash

# Main dependencies from pyproject.toml
uv add 
httpx
python-dotenv
loguru
pendulum 

google-cloud-bigquery 
google-cloud-secret-manager 
google-cloud-storage

pydantic 
pydantic-settings 
"pydantic[email]" 

--no-cache-dir
```
```bash

# Development dependencies from pyproject.toml
uv add pre-commit pylint pyright pytest pytest-asyncio pytest-cov pytest-mock ruff --group=dev --no-cache-dir
```
