#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Extract pytest summary line from test output log.

Usage: python extract_pytest_summary.py <log_file_path>
Writes extracted summary to GITHUB_OUTPUT.
"""

import os
import re
import sys
from pathlib import Path

DEFAULT_SUMMARY = "Test summary unavailable"

# Matches pytest summary lines like:
# "======== 1 passed, 1 skipped in 0.06s ========"
# "10 passed in 1.23s"
SUMMARY_PATTERN = re.compile(
    r"=?\s*(\d+\s+(?:passed|failed|skipped|error|warning)[s,]*.*?in\s+[\d.]+s)\s*=?"
)


def extract_summary(log_path: Path) -> str:
    """Extract pytest summary from log file."""
    if not log_path.is_file():
        print(f"Warning: Log file not found at {log_path}", file=sys.stderr)
        return DEFAULT_SUMMARY

    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        # Search from end of file (summary is near the bottom)
        for line in reversed(lines):
            if match := SUMMARY_PATTERN.search(line):
                return match.group(1).strip()
    except OSError as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        return f"Error extracting summary: {e}"

    return DEFAULT_SUMMARY


def write_to_github_output(summary: str) -> None:
    """Write summary to GITHUB_OUTPUT."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        print("Error: GITHUB_OUTPUT not set.", file=sys.stderr)
        sys.exit(1)

    path = Path(github_output)
    delimiter = f"EOF_SUMMARY_{os.urandom(4).hex()}"

    with path.open("a", encoding="utf-8") as f:
        f.write(f"summary_line<<{delimiter}\n{summary}\n{delimiter}\n")

    print("Summary written to GITHUB_OUTPUT.")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <log_file_path>", file=sys.stderr)
        sys.exit(1)

    log_path = Path(sys.argv[1])
    summary = extract_summary(log_path)
    print(f"Extracted summary: {summary}")
    write_to_github_output(summary)


if __name__ == "__main__":
    main()
