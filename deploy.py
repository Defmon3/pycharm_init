import os
import subprocess
from typing import NoReturn


def run_command(cmd: str) -> None:
    process = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if process.returncode != 0:
        stderr = process.stderr.strip()
        raise RuntimeError(f"Command failed: {cmd}\n{stderr}")


def create_scheduler_job(job_name: str, uri: str, service_account: str, region: str, schedule: str) -> None:
    check = subprocess.run(
        f"gcloud scheduler jobs describe {job_name} --location={region}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if check.returncode == 0:
        print(f"Scheduler job '{job_name}' already exists. Skipping creation.")
        return

    run_command(
        f"gcloud scheduler jobs create http {job_name} "
        f'--schedule="{schedule}" '
        f'--time-zone="Europe/Stockholm" '
        f'--uri="{uri}" '
        f"--http-method=GET "
        f"--oidc-service-account-email={service_account} "
        f"--location={region}"
    )


def add_invoker_permission(function_name: str, service_account: str, region: str) -> None:
    run_command(
        f"gcloud run services add-iam-policy-binding {function_name.replace('_', '-')} "
        f"--region={region} "
        f"--member=serviceAccount:{service_account} "
        f"--role=roles/run.invoker"
    )


def main(
        function_name: str,
        service_account_email: str,
        region: str,
        python_version: str,
        schedule: str = ""
) -> NoReturn:
    run_command("uv lock")
    run_command("uv export --format requirements-txt --locked > requirements.txt")
    run_command(
        f"gcloud functions deploy {function_name} "
        f"--runtime python{python_version} "
        "--trigger-http "
        f"--region={region} "
        "--gen2 "
        "--source=. "
        "--entry-point=main "
        "--no-allow-unauthenticated "
        "--quiet "
    )
    function_url = f"https://{region}-unit-scraper.cloudfunctions.net/{function_name}"
    os.remove("requirements.txt")

    print(f'''Execute this to run:
    Invoke-WebRequest -Uri "{function_url}" -Headers @{{ Authorization = "Bearer $(gcloud auth print-identity-token)" }} -UseBasicParsing''')
    if schedule:
        add_invoker_permission(function_name, service_account_email, region)

        create_scheduler_job(f"{function_name}-job", function_url, service_account_email, region, schedule)


if __name__ == "__main__":
    main(
        function_name="$",
        service_account_email="$",
        region="$",
        python_version="312",
        schedule="0 * * * *"
    )
