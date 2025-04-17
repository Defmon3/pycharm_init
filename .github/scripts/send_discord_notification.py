# .github/scripts/send_discord_notification.py (Slim)
import sys, os, json, requests

webhook_url = os.getenv("COMMIT_WEBHOOK")
if not webhook_url:
    print("::warning::COMMIT_WEBHOOK not set. Skipping notification.", file=sys.stderr)
    sys.exit(0) # Don't fail build

payload_json_string = sys.argv[1]
try:
    payload_dict = json.loads(payload_json_string)
except json.JSONDecodeError as e:
    print(f"::error::Invalid JSON payload provided: {e}", file=sys.stderr)
    sys.exit(1) # Fail if payload is broken

headers = {'Content-Type': 'application/json'}
max_retries = 3
timeout_seconds = 15

for attempt in range(max_retries):
    try:
        response = requests.post(webhook_url, headers=headers, json=payload_dict, timeout=timeout_seconds)
        response.raise_for_status()
        print(f"Notification sent (Status: {response.status_code}).") # Minimal log
        sys.exit(0) # Success
    except requests.exceptions.RequestException as e:
        print(f"Notification attempt {attempt + 1} failed: {e}", file=sys.stderr)
        if attempt == max_retries - 1:
            print(f"::warning::Failed to send Discord notification after {max_retries} attempts.")
            sys.exit(0) # Don't fail build for notification failure
        # Optional: time.sleep(1)