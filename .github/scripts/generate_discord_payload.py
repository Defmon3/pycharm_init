#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.9"
# dependencies = []
# ///

"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: generate_discord_payload.py

"""

import os
import json
import sys
import datetime

def get_env_var(name, default="N/A"):
    """Gets an environment variable, returning a default if not found."""
    return os.environ.get(name, default)

def create_payload(status):
    """Generates the Discord embed payload."""
    # --- Gather data ---
    service_name = get_env_var("SERVICE_NAME", "Unknown Service")
    project_id = get_env_var("PROJECT_ID", "Unknown Project")
    commit_sha = get_env_var("COMMIT_SHA", "Unknown SHA")
    commit_msg_full = get_env_var("COMMIT_MSG", "No commit message.")
    test_summary = get_env_var("TEST_SUMMARY", "Test summary unavailable")
    deploy_duration = get_env_var("DEPLOY_DURATION", "N/A")
    github_actor = get_env_var("GITHUB_ACTOR", "Unknown Actor")
    github_repo = get_env_var("GITHUB_REPOSITORY", "Unknown Repo")
    github_ref_name = get_env_var("GITHUB_REF_NAME", "Unknown Branch")
    github_server_url = get_env_var("GITHUB_SERVER_URL", "https://github.com")
    github_run_id = get_env_var("GITHUB_RUN_ID", "Unknown Run")
    github_workflow = get_env_var("GITHUB_WORKFLOW", "Unknown Workflow")
    deploy_error_snippet = get_env_var("DEPLOY_ERROR_SNIPPET", "Error details unavailable. Check logs.")

    # --- Prepare common elements ---
    commit_sha_short = commit_sha[:7]
    commit_msg_first_line = commit_msg_full.split('\n', 1)[0]
    action_url = f"{github_server_url}/{github_repo}/actions/runs/{github_run_id}"
    commit_url = f"{github_server_url}/{github_repo}/commit/{commit_sha}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    footer_text = f"{github_repo} | {github_workflow}"

    # --- Build payload ---
    if status == "success":
        payload = { "content": None, "embeds": [ { "title": f"✅ Deployment Successful: `{service_name}`", "description": f"Deployment to project `{project_id}` completed successfully.", "color": 3066993, "fields": [ {"name": "🧪 Tests", "value": test_summary, "inline": False}, {"name": "⚙️ Commit", "value": f"[`{commit_sha_short}`]({commit_url}) - `{commit_msg_first_line}`", "inline": False}, {"name": "👤 Triggered by", "value": github_actor, "inline": True}, {"name": "🌿 Branch", "value": github_ref_name, "inline": True}, {"name": "⏱️ Deploy Duration", "value": f"{deploy_duration}s", "inline": True}, {"name": "📄 Workflow Run", "value": f"[View Logs]({action_url})", "inline": False} ], "footer": {"text": footer_text}, "timestamp": timestamp } ] }
    elif status == "failure":
        error_details_limited = deploy_error_snippet[:1000]
        if len(deploy_error_snippet) > 1000: error_details_limited += "\n... (truncated)"
        payload = { "content": None, "embeds": [ { "title": f"❌ Deployment Failed: `{service_name}`", "description": f"Deployment to project `{project_id}` **FAILED**.", "color": 15158332, "fields": [ {"name": "⚙️ Commit", "value": f"[`{commit_sha_short}`]({commit_url}) - `{commit_msg_first_line}`", "inline": False}, {"name": "👤 Triggered by", "value": github_actor, "inline": True}, {"name": "🌿 Branch", "value": github_ref_name, "inline": True}, {"name": "📄 Workflow Run", "value": f"[View Full Logs]({action_url})", "inline": False}, {"name": "❗ Error Snippet", "value": f"```\n{error_details_limited}\n```", "inline": False} ], "footer": {"text": footer_text}, "timestamp": timestamp } ] }
    else:
        print(f"Error: Unknown status '{status}' provided.", file=sys.stderr)
        sys.exit(1)
    return json.dumps(payload)

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["success", "failure"]:
        print("Usage: python generate_discord_payload.py <success|failure>", file=sys.stderr)
        sys.exit(1)
    status_arg = sys.argv[1]
    json_payload = create_payload(status_arg)
    print(json_payload)