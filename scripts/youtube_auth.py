"""Authorise the America Over Time channel once, by hand, and store the token as a GitHub secret.

    pip install google-auth-oauthlib google-api-python-client
    python scripts/youtube_auth.py client_secret.json    # consent in the browser, pick the channel, shows its name and id
    python scripts/youtube_auth.py --check               # which channel the stored token opens
    python scripts/youtube_auth.py --store               # YT_TOKEN_JSON -> GitHub Secrets, and the channel id -> variable YT_CHANNEL_ID

client_secret.json is the OAuth client (Desktop app) of Google Cloud project hypothetica-511509; it is git-ignored.
The token stays in youtube_token.json (git-ignored) and in the secret; it is never printed.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from automation import youtube  # noqa: E402

REPO = "edbackulin-eng/map-timelapse"
TOKEN_FILE = ROOT / "youtube_token.json"


def authorize(client_secret):
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), youtube.SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    TOKEN_FILE.write_text(json.dumps({"refresh_token": creds.refresh_token, "client_id": creds.client_id,
                                      "client_secret": creds.client_secret, "token_uri": creds.token_uri,
                                      "scopes": youtube.SCOPES}), encoding="utf-8")


def show():
    os.environ["YT_TOKEN_JSON"] = TOKEN_FILE.read_text(encoding="utf-8")
    yt = youtube.service()
    ch = yt.channels().list(part="snippet,statistics", mine=True).execute()["items"][0]
    print(f"channel: {ch['snippet']['title']}")
    print(f"id:      {ch['id']}")
    print(f"handle:  {ch['snippet'].get('customUrl', '-')}")
    print(f"videos:  {ch['statistics'].get('videoCount')}")
    return ch


def main(argv):
    if "--store" in argv:
        ch = show()
        if "america" not in ch["snippet"]["title"].lower():
            print("This is NOT America Over Time - not stored.")
            return 1
        subprocess.run(["gh", "secret", "set", "YT_TOKEN_JSON", "--repo", REPO], input=TOKEN_FILE.read_text(encoding="utf-8"),
                       text=True, check=True)
        subprocess.run(["gh", "variable", "set", "YT_CHANNEL_ID", "--repo", REPO, "--body", ch["id"]], check=True)
        print("YT_TOKEN_JSON (secret) and YT_CHANNEL_ID (variable) stored in", REPO)
        return 0
    if "--check" in argv:
        show()
        return 0
    authorize(Path(argv[0]))
    show()
    print("If this is America Over Time:  python scripts/youtube_auth.py --store")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
