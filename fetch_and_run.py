#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#    "loguru"
#    "jinja2",
#    "python-dotenv"
# ]
# ///
"""
Downloads the project template zip, extracts it, finds the main setup script
within it, and executes that script using `uv run`. Passes --clean argument along.
Uses only Python built-in libraries.
"""

import sys
import subprocess
import zipfile
import tempfile
from pathlib import Path
import shutil
import urllib.request
import urllib.error
from contextlib import contextmanager
from loguru import logger as log  # type: ignore[import]
# --- Configuration ---
# URL of the template zip file (same as in the main setup script)
TEMPLATE_ZIP_URL = "https://github.com/defmon3/pycharm_init/archive/refs/heads/main.zip"
# The name of the main setup script expected *inside* the zip file's root content folder
SETUP_SCRIPT_NAME = "setup_main.py"
# --- End Configuration ---



@contextmanager
def temporary_directory_context(prefix: str = "fetch_run_"):
    """Context manager for a temporary directory."""
    tmpdir_path = None
    try:
        tmpdir_path = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
        log.debug( f"Created temporary directory: {tmpdir_path}")
        yield tmpdir_path
    finally:
        if tmpdir_path and tmpdir_path.exists():
             log.debug( f"Cleaning up temporary directory: {tmpdir_path}")
             try: shutil.rmtree(tmpdir_path)
             except Exception as e_clean: log.debug("WARNING", f"Could not remove temp dir {tmpdir_path}: {e_clean}")

def download_zip_stdlib(url: str, target_zip_path: Path):
    """Downloads a file using urllib."""
    log.debug( f"Downloading {url} to {target_zip_path}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} # Be polite
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response, open(target_zip_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        log.debug( f"Download complete ({target_zip_path.stat().st_size} bytes).")
    except urllib.error.URLError as e: log.debug("ERROR", f"Download failed: {e.reason}"); raise
    except Exception as e: log.debug("ERROR", f"Download failed unexpectedly: {e}"); raise

def extract_zip_stdlib(zip_path: Path, extract_dir: Path):
    """Extracts a zip file using zipfile."""
    log.debug(f"Extracting '{zip_path.name}' to '{extract_dir}'...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(extract_dir)
        log.debug("Extraction complete.")
    except zipfile.BadZipFile: log.debug("ERROR", "Downloaded file is not a valid zip."); raise
    except Exception as e: log.debug("ERROR", f"Extraction failed: {e}"); raise

def find_setup_script(extract_dir: Path, script_name: str) -> Path | None:
    """Finds the setup script within the extracted directory structure."""
    log.info(  f"Searching for '{script_name}' within '{extract_dir}'...")
    # Check common patterns: directly inside, or inside one subdirectory
    direct_path = extract_dir / script_name
    if direct_path.is_file():
        log.info(  f"Found script at: {direct_path}")
        return direct_path

    if subdirs := [d for d in extract_dir.iterdir() if d.is_dir()]:
        # Check inside the first subdir found
        subdir_path = subdirs[0] / script_name
        if subdir_path.is_file():
            log.info(  f"Found script at: {subdir_path}")
            return subdir_path
    log.debug("ERROR", f"Could not find '{script_name}' in extracted content.")
    return None

def run_uv_command(cmd: list[str]):
    """Runs a command, typically 'uv run ...'."""
    log.debug(f"Executing: {' '.join(cmd)}")
    try:
        # Run and let output stream to terminal, check for errors
        subprocess.run(cmd, check=True)
        log.debug("Command executed successfully.")
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed with return code {e.returncode}")
        raise # Re-raise to signal failure
    except FileNotFoundError:
         log.critical( f"Command '{cmd[0]}' not found. Is 'uv' installed and in PATH?")
         raise
    except Exception as e:
        log.error(f"Unexpected error running command: {e}")
        raise


def main_fetch_and_run():
    log.info(  "--- Fetch and Run Bootstrapper Starting ---")
    passed_args = sys.argv[1:] # Get args passed to this script (like --clean)

    try:
        with temporary_directory_context() as temp_dir:
            extract_run(temp_dir, passed_args)
        log.info(  "--- Fetch and Run Bootstrapper Finished Successfully ---")
        sys.exit(0)

    except Exception as e:
        log.debug("CRITICAL", f"!!! Bootstrapper failed: {e}")

        sys.exit(1)


def extract_run(temp_dir, passed_args):
    zip_file_path = temp_dir / "template.zip"
    extract_dir_path = temp_dir / "extracted"
    extract_dir_path.mkdir()

    download_zip_stdlib(TEMPLATE_ZIP_URL, zip_file_path)

    # 2. Extract
    extract_zip_stdlib(zip_file_path, extract_dir_path)

    setup_script_path = find_setup_script(extract_dir_path, SETUP_SCRIPT_NAME)
    if setup_script_path is None:
        raise RuntimeError("Setup script could not be located in the extracted archive.")

    cmd_to_run = ["uv", "run", str(setup_script_path)] + passed_args
    run_uv_command(cmd_to_run) # This will handle dependencies via header


if __name__ == "__main__":
    main_fetch_and_run()