#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#    "loguru",
#    "jinja2",
#    "markupsafe",
#    "httpx",
#    "tomlkit",
#    "python-dotenv"
#    ]
#
# ///
import os
import shutil
import subprocess
import sys
from pathlib import Path
from jinja2 import Template  # type: ignore[import]
import httpx  # type: ignore[import]
import tomlkit  # type: ignore[import]
from loguru import logger as log  # type: ignore[import]
from dotenv import dotenv_values  # type: ignore[import]
REQUIREMENTS_TO_REMOVE = ["httpx", "jinja2", "markupsafe", "tomlkit","python-dotenv"]
TARGET_DIR = Path.cwd()
DEV_REQUIREMENTS_TO_ADD = ["pre-commit", "pytest", "pytest-cov", "pytest-asyncio", "pytest-mock", "ruff"]
TOOL_CONFIG = {
    "black": {"line-length": 120, "target-version": ["py312"]},
    "mypy": {"python_version": "3.12"},
    "ruff": {"target-version": "py312", "line-length": 120},
}
DEFAULT_CONFIG_FILENAME = "project.env" # Default config file name

def run_cmd(args: list[str], check: bool = True):
    cmd_str = ' '.join(args)
    log.debug(f"Running: {cmd_str}")
    try:
        res = subprocess.run(
            args, check=check, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if res.stdout.strip(): log.info(f"Command output: {res.stdout.strip()}")
        if res.stderr.strip(): log.warning(f"Command STDERR: {res.stderr.strip()}")
        return res
    except subprocess.CalledProcessError as e:
        log.error(f"!!! Command Failed: {cmd_str}")
        log.error(f"Return Code: {e.returncode}")
        log.error(f"STDOUT:\n{e.stdout}")
        log.error(f"STDERR:\n{e.stderr}")
        raise
    except Exception as e:
        log.error(f"!!! Unexpected error running command '{cmd_str}': {e}", exception=True)
        raise


def get_content_root() -> Path:
    content_root = Path(__file__).resolve().parent
    log.info(f"Determined content root (relative to script): {content_root}")
    log.debug(f"Determined content root: {content_root}") # DEBUG
    return content_root


def process_file(src_path: Path, relative_path: Path, destination_dir: Path, context: dict):

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
    log.info(f"Processing files from '{content_root.name}' into '{destination_dir}'...")
    files_processed = 0
    errors = 0
    script_name = Path(__file__).name

    for src_path in content_root.rglob("*"):
        if not src_path.is_file():
            continue
        if src_path.name in [script_name, DEFAULT_CONFIG_FILENAME]:
            log.debug(f"Skipping self ({script_name})")
            continue

        relative_path = src_path.relative_to(content_root)
        try:
            process_file(src_path, relative_path, destination_dir, render_context)
            files_processed += 1
        except Exception as e:
            log.error(f"Failed processing {relative_path}: {e}", exception=True)
            errors += 1
    log.info(f"Processed {files_processed} files.")
    if errors > 0:
        log.warning(f"{errors} errors occurred during file processing.")


def remove_live_template(target_directory: Path):
    lt_file = target_directory / "live_template.py"
    if lt_file.exists():
        log.info(f"Removing '{lt_file.name}' from target directory...")
        try:
            lt_file.unlink()
            log.debug(f"Successfully removed '{lt_file.name}'.")
        except OSError as e:
            log.warning(f"Could not remove '{lt_file.name}': {e}")
    else:
        log.debug(f"'{lt_file.name}' does not exist in target directory, skipping removal.")


def update_pyproject_toml_unsafe(target_dir: Path):
    toml_path = target_dir / "pyproject.toml"
    log.info(f"Updating '{toml_path.name}' (unsafe)...")

    if toml_path.exists():
        log.debug(f"Attempting to read '{toml_path.name}'")
        with open(toml_path, 'r', encoding='utf-8') as f:
            data = tomlkit.load(f)
    else:
        log.warning(f"'{toml_path.name}' not found. Creating new document.")
        data = tomlkit.document()
        data.add('project', tomlkit.table())
        data['project']['name'] = target_dir.name
        data['project']['version'] = "0.1.0"

    if 'tool' not in data: data['tool'] = tomlkit.table()
    tool_table = data['tool']
    log.debug("Setting [tool.*] configurations")
    for tool_name, config_dict in TOOL_CONFIG.items():
        if tool_name not in tool_table: tool_table[tool_name] = tomlkit.table()
        log.debug(f"Setting tool '{tool_name}' with config: {config_dict}")
        for key, value in config_dict.items():
            tool_table[tool_name][key] = value

    log.info(f"Writing configuration to '{toml_path.name}'...")
    with open(toml_path, 'w', encoding='utf-8') as f:
        tomlkit.dump(data, f)
    log.info(f"Finished updating '{toml_path.name}'.")


def install_dev():
    log.info("Updating pyproject.toml with tool configurations...")
    update_pyproject_toml_unsafe(TARGET_DIR)
    log.info("pyproject.toml update complete.")

def load_context_from_toml(_config_path: Path, default_config_path: Path) -> dict:
    """Loads template context variables from a TOML file."""
    config_path = default_config_path if default_config_path.is_file() else  _config_path
    context = {}
    if not config_path.is_file():
        log.warning(f"Configuration file not found: {config_path}. Skipping context loading from TOML.")
        return context

    log.info(f"Loading template context from: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:

            config_data = dotenv_values("project.env")
    except FileNotFoundError:
        log.warning(f"Configuration file not found during read attempt: {config_path}")
    except tomlkit.exceptions.ParseError as e:
        log.error(f"Error parsing TOML file {config_path}: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred loading {config_path}: {e}", exception=True)

    return context

def run():
    try:
        install_dev()
        project_name = TARGET_DIR.name
        log.info(f"--- Starting Project File Processing for '{project_name}' ---")
        content_root = get_content_root()
        render_context = load_context_from_toml(content_root, Path(DEFAULT_CONFIG_FILENAME))
        process_extracted_files(content_root, TARGET_DIR, render_context)
        remove_live_template(TARGET_DIR)
        log.success(f"--- Project Initialization Logic for '{project_name}' Finished Successfully ---")
    except Exception as e:
        log.critical(f"!!! An error occurred during the main process: {e}")
        log.opt(exception=True).critical("Traceback:")
        raise


def run_cleanup_only():
    log.info("Running cleanup: Uninstalling specified packages...")
    try:
        run_cmd(["uv", "remove"] + REQUIREMENTS_TO_REMOVE, check=False)
        log.info("Cleanup command finished.")
    except Exception as e:
        log.error(f"Error during cleanup: {e}", exception=True)


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
            log.critical("--- Project Initialization FAILED. See errors above. ---")
            sys.exit(1)


if __name__ == "__main__":
    main()
