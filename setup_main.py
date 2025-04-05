#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#    # Dependencies for this script's functionality:
#    "loguru",
#    "jinja2",
#    "markupsafe",
#    "httpx",  # Still needed if template processing involves HTTP? If not, remove.
#    "tomlkit",
#    # Add your dev dependencies HERE:
#    "pre-commit>=4.2.0",
#    "pytest>=8.3.5",
#    "pytest-cov>=6.1.0",
#    "pytest-asyncio", # Added from your last example
#    "pytest-mock>=3.14.0",
#    "ruff>=0.11.2",
# ]
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
File: setup_main.py (This script lives INSIDE the template zip)
Description: Performs the actual project setup (file processing, pyproject.toml update).
             Assumes it's run via `uv run` which handles dependencies from the header.
             Accepts optional --clean flag.
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
import tomlkit # type: ignore[import]
import httpx   # type: ignore[import] # Only needed if processing step uses it
from loguru import logger as log
from jinja2 import Template # type: ignore[import]

# --- Configuration ---
# Define paths relative to *this script's execution* (which is inside extracted folder)
# We assume the target directory is the parent of where this setup script runs
# Or more reliably, assume TARGET_DIR is passed or is CWD where uv run was invoked.
TARGET_DIR = Path.cwd() # Assumes uv run is invoked from the target project directory

# Requirements to remove *only* when --clean is specified
REQUIREMENTS_TO_REMOVE = ["httpx", "jinja2", "markupsafe", "tomlkit", "pre-commit", "pytest", "pytest-cov", "pytest-asyncio", "pytest-mock", "ruff"] # Include dev deps if clean should remove them too

# Tool settings to add/update in pyproject.toml
TOOL_CONFIG = {
    "black": {"line-length": 120, "target-version": ["py312"]},
    "mypy": {"python_version": "3.12"},
    "ruff": {"target-version": "py312", "line-length": 120},
}
# --- End Configuration ---

# Configure Loguru
log.remove()
log.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
log.info("Setup script starting, Loguru configured.")

# --- Minimal Subprocess Runner (Only needed for --clean) ---
def run_cmd(args: list[str], check: bool = True):
    cmd_str = ' '.join(args)
    log.info(f"Running command: {cmd_str}")
    try:
        result = subprocess.run(args, check=check, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.stderr: log.warning(f"Command STDERR:\n{result.stderr}")
        return result
    except subprocess.CalledProcessError as e: log.error(f"!!! Command Failed: {cmd_str}", exception=True); raise
    except Exception as e: log.error(f"!!! Unexpected error running command '{cmd_str}': {e}", exception=True); raise

# --- Core Logic Functions (process_file, process_extracted_files) ---
# (Keep these functions as they were in your working script - they use log, Template)
def process_file(src_path: Path, relative_path: Path, destination_dir: Path, context: dict):
    target_path = destination_dir / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if src_path.suffix == ".j2":
        target_path_rendered = target_path.with_suffix("")
        log.debug(f"  Rendering: {relative_path} -> {target_path_rendered.relative_to(destination_dir)}")
        template = Template(src_path.read_text("utf-8"))
        rendered = template.render(**context)
        target_path_rendered.write_text(rendered, "utf-8")
    else:
        log.debug(f"  Copying:   {relative_path} -> {target_path.relative_to(destination_dir)}")
        shutil.copy2(src_path, target_path)

def process_extracted_files(content_root: Path, destination_dir: Path, render_context: dict):
    log.info(f"Processing files from '{content_root.name}' into '{destination_dir}'...")
    files_processed, errors = 0, 0
    for src_path in content_root.rglob("*"):
        if not src_path.is_file(): continue
        relative_path = src_path.relative_to(content_root)
        # --- Add skip logic here if needed ---
        if relative_path.name == "setup_main.py": # Don't copy self
             log.debug(f"Skipping self ({relative_path.name})")
             continue
        if relative_path.name == "fetch_and_run.py": # Don't copy trigger
             log.debug(f"Skipping trigger script ({relative_path.name})")
             continue
        # --- End skip logic ---
        try:
            process_file( src_path, relative_path, destination_dir, render_context)
            files_processed += 1
        except Exception as e: log.error(f"Failed processing {relative_path}: {e}", exception=True); errors += 1
    log.info(f"Processed {files_processed} files.")
    if errors > 0: log.warning(f"{errors} errors occurred during file processing.")


# --- Function to Update pyproject.toml (Unsafe version) ---
def update_pyproject_toml_unsafe(target_dir: Path, tool_config: dict):
    """UNSAFE version. Directly attempts read/modify/write."""
    toml_path = target_dir / "pyproject.toml"
    log.info(f"Updating '{toml_path.name}' (unsafe)...")
    if not toml_path.exists():
        log.error(f"'{toml_path.name}' not found. Cannot update tool settings.")
        # Decide if creating it is desired, or if this is an error.
        # Creating a basic one:
        log.warning(f"Creating new '{toml_path.name}'")
        data = tomlkit.document()
        data.add('project', tomlkit.table())
        data['project']['name'] = target_dir.name
        data['project']['version'] = "0.1.0"
        data['project']['requires-python'] = ">=3.8" # Example
    else:
        with open(toml_path, 'r', encoding='utf-8') as f:
            data = tomlkit.load(f)

    # Set Tool Configurations
    log.debug("Setting [tool.*] configurations")
    if 'tool' not in data: data['tool'] = tomlkit.table() # Minimal structure
    tool_table = data['tool']
    for tool_name, config_dict in tool_config.items():
        log.debug(f"Processing [tool.{tool_name}]")
        if tool_name not in tool_table: tool_table[tool_name] = tomlkit.table() # Create if needed
        for key, value in config_dict.items():
            tool_table[tool_name][key] = value # Assigns/updates keys

    # Write Updated File
    log.info(f"Writing configuration to '{toml_path.name}'...")
    with open(toml_path, 'w', encoding='utf-8') as f: tomlkit.dump(data, f)
    log.info(f"Finished updating '{toml_path.name}'.")

# --- Main Initialization Function ---
def run_initialization():
    """Processes template files and updates pyproject.toml."""
    # Assumes the script is running from *within* the extracted template directory
    # The parent directory is the temporary extraction location.
    # The TARGET_DIR (CWD where uv run was invoked) is where files should go.
    script_path = Path(__file__).resolve()
    # Assumes the structure like temp_extract/pycharm_init-main/setup_main.py
    # content_root might be the directory containing this script
    content_root = script_path.parent
    log.info(f"Running setup logic from: {content_root}")
    log.info(f"Target directory for output: {TARGET_DIR}")

    try:
        project_name = TARGET_DIR.name # Use the name of the target directory
        render_context = {'NAME': project_name}

        # Process template files from content_root into TARGET_DIR
        process_extracted_files(content_root, TARGET_DIR, render_context)

        # Update pyproject.toml in the TARGET_DIR
        update_pyproject_toml_unsafe(TARGET_DIR, TOOL_CONFIG)

        # --- Dev Dependencies are NOT installed here anymore ---
        # `uv run` already ensured they were present based on the header.
        log.info("--- Dev dependencies assumed present via uv run header ---")

        log.success(f"--- Project Setup for '{project_name}' Finished Successfully ---")

    except Exception as e:
        log.critical(f"!!! An error occurred during setup: {e}", exception=True)
        raise # Re-raise exception

# --- Cleanup Function ---
def run_cleanup_only():
    """Only uninstalls specific dependencies."""
    log.info(f"Running cleanup: Uninstalling {len(REQUIREMENTS_TO_REMOVE)} packages...")
    try:
        run_cmd(["uv", "remove"] + REQUIREMENTS_TO_REMOVE, check=False)
        log.info("Cleanup command finished.")
    except Exception as e:
        log.error(f"Error during cleanup: {e}", exception=True)


# --- Main Entry Point for setup_main.py ---
if __name__ == "__main__":
    perform_clean_only = "--clean" in sys.argv

    if perform_clean_only:
        log.info("Detected --clean flag. Running cleanup only...")
        run_cleanup_only()
        log.info("Cleanup finished.")
        sys.exit(0)
    else:
        log.info("No --clean flag detected. Running setup...")
        try:
            run_initialization()
            sys.exit(0) # Exit successfully
        except Exception:
            log.critical("--- Project Setup FAILED. See errors above. ---")
            sys.exit(1) # Exit with failure code