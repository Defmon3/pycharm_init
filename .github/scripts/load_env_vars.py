#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Load environment variables from project.env for GitHub Actions.

Writes variables to GITHUB_ENV and generates gcloud --set-env-vars string.
"""

import os
from pathlib import Path


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a .env file into a dictionary."""
    if not env_path.is_file():
        raise FileNotFoundError(f"Missing {env_path}")

    env_vars: dict[str, str] = {}
    content = env_path.read_text(encoding="utf-8")

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Remove surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        if key:
            env_vars[key] = value

    return env_vars


def write_to_github_env(env_vars: dict[str, str]) -> None:
    """Write variables to GITHUB_ENV for subsequent steps."""
    github_env = os.environ.get("GITHUB_ENV")
    if not github_env:
        print("Warning: GITHUB_ENV not set.")
        return

    path = Path(github_env)
    with path.open("a", encoding="utf-8") as f:
        for key, value in env_vars.items():
            if "\n" in value:
                # Use heredoc format for multiline values
                delimiter = f"EOF_{key}_{os.urandom(4).hex()}"
                f.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{key}={value}\n")


def write_gcloud_env_to_output(env_vars: dict[str, str]) -> None:
    """Write gcloud --set-env-vars string to GITHUB_OUTPUT."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        print("Warning: GITHUB_OUTPUT not set.")
        return

    gcloud_env_string = ",".join(f"{k}={v}" for k, v in env_vars.items())

    path = Path(github_output)
    with path.open("a", encoding="utf-8") as f:
        delimiter = f"EOF_GCLOUD_ENV_{os.urandom(4).hex()}"
        f.write(f"gcloud_env_string<<{delimiter}\n{gcloud_env_string}\n{delimiter}\n")
        f.write("gcloud_vars_generated=true\n")


def main() -> None:
    env_path = Path("project.env")

    try:
        env_vars = parse_env_file(env_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    if not env_vars:
        print(f"No valid environment variables found in {env_path}.")
        write_gcloud_env_to_output({})
        return

    write_to_github_env(env_vars)
    write_gcloud_env_to_output(env_vars)
    print(f"Processed {len(env_vars)} variables from {env_path}.")


if __name__ == "__main__":
    main()
