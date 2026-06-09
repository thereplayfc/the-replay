"""
THE REPLAY — YouTube One-Time Auth Setup
Run this ONCE on your laptop. It saves a token file.
Upload that token file as a GitHub secret.
Never need to run again.
"""
import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authorize():
    config = {"installed": {
        "client_id":     YOUTUBE_CLIENT_ID,
        "client_secret": YOUTUBE_CLIENT_SECRET,
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob","http://localhost"],
        "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
        "token_uri":     "https://oauth2.googleapis.com/token"
    }}
    flow  = InstalledAppFlow.from_client_config(config, SCOPES)
    creds = flow.run_local_server(port=0)
    token = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "scopes":        list(creds.scopes)
    }
    os.makedirs("config", exist_ok=True)
    with open("config/youtube_token.json", "w") as f:
        json.dump(token, f, indent=2)
    print("\n✅ YouTube authorized!")
    print("Token saved to: config/youtube_token.json")
    print("\nNext step: Add this file's content as a GitHub secret named YOUTUBE_TOKEN")
    print("(Go to your repo → Settings → Secrets → New secret)")

if __name__ == "__main__":
    print("Opening browser... Log in to your YouTube account and click Allow.")
    authorize()
