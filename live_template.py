#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["loguru", "jinja2", "markupsafe", "httpx"] # Dependencies installed dynamically
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
File: main_very_simple_uv_add_remove.py
Description: Extremely simplified script attempting install-then-import using uv add/remove.
             *** WARNING: This approach is UNRELIABLE and may fail. ***
             Removes safety checks and uses minimal error handling.
"""

import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path
import httpx  # type: ignore[import]
from loguru import logger as log  # type: ignore[import]

# --- Configuration ---
TEMPLATE_ZIP_URL = "https://github.com/defmon3/pycharm_init/archive/refs/heads/main.zip"
REQUIREMENTS_TO_ADD = []
REQUIREMENTS_TO_REMOVE = ["httpx", "jinja2", "markupsafe"]
TARGET_DIR = Path.cwd()


def run_cmd(args: list[str], check: bool = True):
    """Runs a command using subprocess, minimal error logging."""
    cmd_str = ' '.join(args)
    print(f"Running: {cmd_str}")  # Basic feedback
    try:
        return subprocess.run(
            args,
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
    except subprocess.CalledProcessError as e:
        log.error(f"!!! Command Failed: {cmd_str}", file=sys.stderr)
        raise


def download_zip(url: str, target_zip_path: Path):
    """Downloads a file (requires httpx)."""
    log.info(f"Downloading {url}...")
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        response = client.get(url)
        response.raise_for_status()
        target_zip_path.write_bytes(response.content)
    log.info(f"Download complete ({target_zip_path.stat().st_size} bytes).")


def extract_zip(zip_path: Path, extract_dir: Path):
    """Extracts a zip file."""
    log.info(f"Extracting '{zip_path.name}'...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)
    log.info("Extraction complete.")


def find_content_root(extract_dir: Path) -> Path:
    """Determines the actual root directory of extracted content."""
    log.debug(f"Finding content root in: {extract_dir}")
    extracted_items = list(extract_dir.iterdir())
    if not extracted_items:
        log.error("Zip archive seems empty after extraction.")
        raise RuntimeError("Empty zip archive content.")
    if len(extracted_items) == 1 and extracted_items[0].is_dir():
        content_root = extracted_items[0]
        log.info(f"Found content root directory: {content_root.name}")
        return content_root
    log.warning("Processing content directly from archive root.")
    return extract_dir


def process_file(src_path: Path, relative_path: Path, destination_dir: Path, context: dict):
    """Processes a single file (render or copy)."""
    from jinja2 import Template  # type: ignore[import]
    target_path = destination_dir / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if src_path.suffix == ".j2":
        target_path_rendered = target_path.with_suffix("")
        log.debug(f"  Rendering: {relative_path} -> {target_path_rendered.relative_to(destination_dir)}")
        template_content = src_path.read_text("utf-8")
        template = Template(template_content)
        rendered_content = template.render(**context)
        target_path_rendered.write_text(rendered_content, "utf-8")
    else:
        log.debug(f"  Copying:   {relative_path} -> {target_path.relative_to(destination_dir)}")
        shutil.copy2(src_path, target_path)


def process_extracted_files(content_root: Path, destination_dir: Path, render_context: dict):
    """Iterates through files and calls process_file."""
    log.info(f"Processing files from '{content_root.name}' into '{destination_dir}'...")
    files_processed = 0
    errors = 0
    for src_path in content_root.rglob("*"):
        if not src_path.is_file():
            log.debug(f"Skipping non-file: {src_path}")
            continue
        relative_path = src_path.relative_to(content_root)
        try:
            process_file( src_path, relative_path, destination_dir, render_context)
            files_processed += 1
        except Exception as e:
            log.error(f"Failed processing {relative_path}: {e}")
            errors += 1
    log.info(f"Processed {files_processed} files.")
    if errors > 0:
        log.warning(f"{errors} errors occurred during file processing.")


@contextmanager
def temporary_directory_context(prefix: str ):
    """Context manager for a temporary directory."""
    tmpdir_path = None
    try:
        tmpdir_path = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
        log.info(f"Created temporary directory: {tmpdir_path}")
        yield tmpdir_path
    finally:
        if tmpdir_path and tmpdir_path.exists():
            log.info(f"Cleaning up temporary directory: {tmpdir_path}")
            try:
                shutil.rmtree(tmpdir_path)
            except Exception as e_clean:
                log.warning(f"Could not completely remove temporary directory {tmpdir_path}: {e_clean}")

def remove_live_template():
    lt_file = Path("live_template.py")
    lt_file.unlink(missing_ok=True)

def run():

    try:
        project_name = TARGET_DIR.name
        log.info(f"--- Starting Project Initialization for '{project_name}' ---")
        with temporary_directory_context("init_temp_") as temp_dir:
            zip_file_path = temp_dir / "template.zip"
            extract_dir_path = temp_dir / "unzipped"
            download_zip( TEMPLATE_ZIP_URL, zip_file_path)
            extract_zip( zip_file_path, extract_dir_path)
            remove_live_template()
            content_root_path = find_content_root( extract_dir_path)
            render_context = {'NAME': project_name}
            process_extracted_files( content_root_path, TARGET_DIR, render_context)

        log.success(f"--- Project Initialization for '{project_name}' Finished Successfully ---")

    except Exception as e:
        log.critical(f"!!! An error occurred during the main process: {e}")
        log.opt(exception=True).critical("Traceback:")
        sys.exit(1)
    sys.exit(0)


def run_cleanup_only():
    """Only uninstalls specific dependencies."""
    print("[INFO    ] Running cleanup: Uninstalling specified packages...")
    try:
        run_cmd(["uv", "remove"] + REQUIREMENTS_TO_REMOVE, check=False)
        print("[INFO    ] Cleanup command finished.")
    except Exception as e:
        print(f"[ERROR   ] Error during cleanup: {e}", file=sys.stderr)


def main():
    perform_clean_only = "--clean" in sys.argv

    if perform_clean_only:
        log.info(f" Detected --clean flag. {sys.argv} Running cleanup only...")
        run_cleanup_only()
        log.info("Cleanup finished.")
        sys.exit(0)
    else:
        log.info("No --clean flag detected. Running full initialization...")
        try:
            run()
            sys.exit(0)
        except Exception:
            log.critical(
                "Project Initialization FAILED. See errors above. ---",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
