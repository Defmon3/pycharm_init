📦 **Main dependencies (with pinned versions):**

* httpx==0.27.0
* python-dotenv==1.0.1
* loguru==0.7.3
* pendulum==3.1.0
* google-cloud-bigquery==3.34.0
* google-cloud-secret-manager==2.24.0
* google-cloud-storage==3.1.0
* pydantic==2.7.1
* pydantic-settings==2.2.1
* pydantic\[email]

```bash

uv add httpx==0.27.0 python-dotenv==1.0.1 loguru==0.7.3 pendulum==3.1.0 google-cloud-bigquery==3.34.0 google-cloud-secret-manager==2.24.0 google-cloud-storage==3.1.0 pydantic==2.7.1 pydantic-settings==2.2.1 "pydantic[email]" --no-cache-dir
```

🛠️ **Dev dependencies (with pinned versions):**

* pre-commit==4.2.0
* pylint==3.3.6
* pyright==1.1.398
* pytest==8.3.5
* pytest-asyncio==0.26.0
* pytest-cov==6.1.0
* pytest-mock==3.14.0
* ruff==0.11.2

```bash

uv add pre-commit==4.2.0 pylint==3.3.6 pyright==1.1.398 pytest==8.3.5 pytest-asyncio==0.26.0 pytest-cov==6.1.0 pytest-mock==3.14.0 ruff==0.11.2 --group=dev --no-cache-dir
```

🚀 **Optional ASGI server (for local or container runs):**

* uvicorn==0.34.3

```bash

uv add uvicorn==0.34.3 --dev --no-cache-dir
```

🐘 **Optional WSGI server (for Flask/Django/Gunicorn-based containers):**

* gunicorn==22.0.0

```bash

uv add gunicorn==22.0.0 --dev --no-cache-dir
```
