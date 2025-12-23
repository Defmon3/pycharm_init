#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Generate Discord webhook payload for deployment notifications.

Usage: python generate_discord_payload.py <success|failure>
Outputs JSON payload to stdout.
"""

import datetime
import json
import os
import sys


def get_env(name: str, default: str = "N/A") -> str:
    """Get environment variable with default."""
    return os.environ.get(name, default)


def build_success_embed(
    service_name: str,
    project_id: str,
    commit_sha: str,
    commit_msg: str,
    test_summary: str,
    deploy_duration: str,
    github_actor: str,
    github_ref_name: str,
    action_url: str,
    commit_url: str,
    footer_text: str,
    timestamp: str,
) -> dict:
    """Build embed for successful deployment."""
    return {
        "title": f"Deployment Successful: `{service_name}`",
        "description": f"Deployment to project `{project_id}` completed successfully.",
        "color": 3066993,  # Green
        "fields": [
            {"name": "Tests", "value": test_summary, "inline": False},
            {
                "name": "Commit",
                "value": f"[`{commit_sha[:7]}`]({commit_url}) - `{commit_msg}`",
                "inline": False,
            },
            {"name": "Triggered by", "value": github_actor, "inline": True},
            {"name": "Branch", "value": github_ref_name, "inline": True},
            {"name": "Deploy Duration", "value": f"{deploy_duration}s", "inline": True},
            {"name": "Workflow Run", "value": f"[View Logs]({action_url})", "inline": False},
        ],
        "footer": {"text": footer_text},
        "timestamp": timestamp,
    }


def build_failure_embed(
    service_name: str,
    project_id: str,
    commit_sha: str,
    commit_msg: str,
    error_snippet: str,
    github_actor: str,
    github_ref_name: str,
    action_url: str,
    commit_url: str,
    footer_text: str,
    timestamp: str,
) -> dict:
    """Build embed for failed deployment."""
    error_truncated = error_snippet[:1000]
    if len(error_snippet) > 1000:
        error_truncated += "\n... (truncated)"

    return {
        "title": f"Deployment Failed: `{service_name}`",
        "description": f"Deployment to project `{project_id}` **FAILED**.",
        "color": 15158332,  # Red
        "fields": [
            {
                "name": "Commit",
                "value": f"[`{commit_sha[:7]}`]({commit_url}) - `{commit_msg}`",
                "inline": False,
            },
            {"name": "Triggered by", "value": github_actor, "inline": True},
            {"name": "Branch", "value": github_ref_name, "inline": True},
            {"name": "Workflow Run", "value": f"[View Full Logs]({action_url})", "inline": False},
            {"name": "Error Snippet", "value": f"```\n{error_truncated}\n```", "inline": False},
        ],
        "footer": {"text": footer_text},
        "timestamp": timestamp,
    }


def create_payload(status: str) -> str:
    """Generate Discord embed payload based on deployment status."""
    # Gather environment data
    service_name = get_env("SERVICE_NAME", "Unknown Service")
    project_id = get_env("PROJECT_ID", "Unknown Project")
    commit_sha = get_env("COMMIT_SHA", "Unknown SHA")
    commit_msg = get_env("COMMIT_MSG", "No commit message.").split("\n", 1)[0]
    test_summary = get_env("TEST_SUMMARY", "Test summary unavailable")
    deploy_duration = get_env("DEPLOY_DURATION", "N/A")
    error_snippet = get_env("DEPLOY_ERROR_SNIPPET", "Error details unavailable.")

    # GitHub context
    github_actor = get_env("GITHUB_ACTOR", "Unknown")
    github_repo = get_env("GITHUB_REPOSITORY", "Unknown")
    github_ref_name = get_env("GITHUB_REF_NAME", "Unknown")
    github_server_url = get_env("GITHUB_SERVER_URL", "https://github.com")
    github_run_id = get_env("GITHUB_RUN_ID", "Unknown")
    github_workflow = get_env("GITHUB_WORKFLOW", "Unknown")

    # Build URLs
    action_url = f"{github_server_url}/{github_repo}/actions/runs/{github_run_id}"
    commit_url = f"{github_server_url}/{github_repo}/commit/{commit_sha}"
    footer_text = f"{github_repo} | {github_workflow}"
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    # Build embed based on status
    if status == "success":
        embed = build_success_embed(
            service_name=service_name,
            project_id=project_id,
            commit_sha=commit_sha,
            commit_msg=commit_msg,
            test_summary=test_summary,
            deploy_duration=deploy_duration,
            github_actor=github_actor,
            github_ref_name=github_ref_name,
            action_url=action_url,
            commit_url=commit_url,
            footer_text=footer_text,
            timestamp=timestamp,
        )
    elif status == "failure":
        embed = build_failure_embed(
            service_name=service_name,
            project_id=project_id,
            commit_sha=commit_sha,
            commit_msg=commit_msg,
            error_snippet=error_snippet,
            github_actor=github_actor,
            github_ref_name=github_ref_name,
            action_url=action_url,
            commit_url=commit_url,
            footer_text=footer_text,
            timestamp=timestamp,
        )
    else:
        print(f"Error: Unknown status '{status}'", file=sys.stderr)
        sys.exit(1)

    return json.dumps({"content": None, "embeds": [embed]})


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("success", "failure"):
        print("Usage: python generate_discord_payload.py <success|failure>", file=sys.stderr)
        sys.exit(1)

    payload = create_payload(sys.argv[1])
    print(payload)


if __name__ == "__main__":
    main()
