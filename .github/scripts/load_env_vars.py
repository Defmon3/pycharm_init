#!/usr/bin/env python3

import os
from pathlib import Path
import shlex # Use shlex for potential future quoting needs, though gcloud might handle basic cases

def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parses a .env file into a dictionary."""
    if not env_path.is_file():
        raise FileNotFoundError(f"Missing {env_path}")

    lines = env_path.read_text(encoding="utf-8").splitlines()
    pairs = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                # Basic unquoting (remove surrounding quotes) - adjust if more complex quoting is used
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key: # Ensure key is not empty
                    pairs.append((key, value))
            # Handle lines without '=' if needed, currently ignored
    return dict(pairs)

def write_to_github_env(env_vars: dict[str, str]) -> None:
    """Writes variables to the GITHUB_ENV file for subsequent steps."""
    github_env_path = os.environ.get("GITHUB_ENV")
    if not github_env_path:
        print("Warning: GITHUB_ENV not set. Cannot export variables for subsequent steps.")
        return
    path = Path(github_env_path)
    try:
        with path.open("a", encoding="utf-8") as f:
            for k, v in env_vars.items():
                # Basic check for multiline, use heredoc format for GITHUB_ENV
                if '\n' in v:
                    delimiter = f"EOF_{k}_{os.urandom(4).hex()}"
                    f.write(f"{k}<<{delimiter}\n")
                    f.write(f"{v}\n")
                    f.write(f"{delimiter}\n")
                else:
                    f.write(f"{k}={v}\n")
    except IOError as e:
        print(f"Error writing to GITHUB_ENV {path}: {e}")


def write_gcloud_env_string_to_output(env_vars: dict[str, str]) -> None:
    """Writes a comma-separated KEY=VALUE string for gcloud --set-env-vars to GITHUB_OUTPUT."""
    github_output_path = os.environ.get("GITHUB_OUTPUT")
    if not github_output_path:
        print("Warning: GITHUB_OUTPUT not set. Cannot set gcloud env string output.")
        return

    # Create the comma-separated string
    # Note: This assumes values don't contain commas themselves in a way
    # that would break gcloud parsing. gcloud is usually robust here when
    # the whole string is quoted in the shell command.
    gcloud_env_string = ",".join(f"{k}={v}" for k, v in env_vars.items())

    path = Path(github_output_path)
    try:
        with path.open("a", encoding="utf-8") as f:
            # Use heredoc for the output to avoid issues with the string itself containing special chars
            delimiter = f"EOF_GCLOUD_ENV_{os.urandom(4).hex()}"
            f.write(f"gcloud_env_string<<{delimiter}\n")
            f.write(f"{gcloud_env_string}\n") # Write the actual string
            f.write(f"{delimiter}\n")
            # Also write the legacy output flag if needed by other logic
            f.write("gcloud_vars_generated=true\n") # Keep this if you rely on it elsewhere
    except IOError as e:
        print(f"Error writing to GITHUB_OUTPUT {path}: {e}")


# Remove the old write_output_flag function as it's merged into the new one
# def write_output_flag() -> None:
#     path = Path(os.environ["GITHUB_OUTPUT"])
#     with path.open("a", encoding="utf-8") as f:
#         f.write("gcloud_vars_generated=true\n")

def main() -> None:
    env_path = Path("project.env")
    try:
        env_vars = parse_env_file(env_path)
        if env_vars:
            write_to_github_env(env_vars)
            write_gcloud_env_string_to_output(env_vars)
            print(f"Successfully processed {len(env_vars)} variables from {env_path}.")
        else:
            print(f"No valid environment variables found in {env_path}.")
            # Still write empty output string if needed, or handle appropriately
            write_gcloud_env_string_to_output({}) # Write empty output

    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Decide if you want to exit non-zero here
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Decide if you want to exit non-zero here

if __name__ == "__main__":
    main()