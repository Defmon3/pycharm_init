#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = []
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: extract_pytest_summary.py

"""

import os
import re
import sys
from pathlib import Path

DEFAULT_SUMMARY = "Test summary unavailable"
GITHUB_OUTPUT_FILE = os.getenv("GITHUB_OUTPUT")

if len(sys.argv) < 2:
    print(f"Usage: python {sys.argv[0]} <log_file_path>", file=sys.stderr)
    sys.exit(1)

if not GITHUB_OUTPUT_FILE:
    print("ERROR: GITHUB_OUTPUT environment variable not set.", file=sys.stderr)
    sys.exit(1)

log_file_path = Path(sys.argv[1])
summary_line = DEFAULT_SUMMARY

if not log_file_path.is_file():
    print(f"Warning: Log file not found at {log_file_path}", file=sys.stderr)
else:
    try:
        # Regex to find the typical pytest summary line (adjust if needed)
        # Example: "======== 1 passed, 1 skipped, 1 warning in 0.06s ========="
        # Or: "10 passed in 1.23s"
        summary_regex = re.compile(r'=?\s*(\d+\s+(?:passed|failed|skipped|error|warning)[s,]*.*?in\s+[\d.]+s)\s*=?')

        # Read lines in reverse to find the summary near the end faster
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines):
                match = summary_regex.search(line)
                if match:
                    summary_line = match.group(1).strip()
                    break  # Found the last matching summary line
    except Exception as e:
        print(f"Error reading or processing log file {log_file_path}: {e}", file=sys.stderr)
        summary_line = f"Error extracting summary: {e}"

print(f"Extracted summary: {summary_line}")

# Write to GitHub Actions output
try:
    with open(GITHUB_OUTPUT_FILE, "a", encoding="utf-8") as f_out:
        # Use multiline output format for safety, though summary is usually single line
        delimiter = f"EOF_SUMMARY_{os.urandom(4).hex()}"
        f_out.write(f"summary_line<<{delimiter}\n")
        f_out.write(f"{summary_line}\n")
        f_out.write(f"{delimiter}\n")
    print("Summary written to GITHUB_OUTPUT.")
except IOError as e:
    print(f"Error writing summary to GITHUB_OUTPUT file {GITHUB_OUTPUT_FILE}: {e}", file=sys.stderr)
    sys.exit(1)
