"""
THE REPLAY — Publisher (All Free APIs)
YouTube Data API v3 — free
TikTok Content Posting API — free
Instagram Graph API — free
"""

import os, sys, time, logging, requests, tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *

log = logging.getLogger("publisher")

# ============================================================
#  YOUTUBE SHORTS (free)
# ============================================================

def post_youtube(video_path, caption):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds   = Credentials.from_authorized_user_file("config/youtube_token.json")
    youtube = build("youtube", "v3", credentials=creds)

    title = caption.split("\n")[0][:90] + " #Shorts"
    body  = {
        "snippet": {
            "title":           title,
            "description":     caption,
            "tags":            ["football","soccer","goals","highlights","shorts","thereplay"],
            "categoryId":      "17",
            "defaultLanguage": "en",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    media  = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    req    = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    resp   = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            log.info(f"YouTube upload: {int(status.progress()*100)}%")

    vid = resp.get("id")
    log.info(f"YouTube posted: https://youtube.com/shorts/{vid}")
    return f"https://youtube.com/shorts/{vid}"

# ============================================================
#  TIKTOK (free developer API)
# ============================================================

def post_tiktok(video_path, caption):
    # TikTok requires a public URL — upload to transfer.sh (free, no account)
    video_url = upload_free(video_path)

    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type":  "application/json; charset=UTF-8"
    }
    payload = {
        "post_info": {
            "title":             caption[:150],
            "privacy_level":     "PUBLIC_TO_EVERYONE",
            "disable_duet":      False,
            "disable_comment":   False,
            "disable_stitch":    False,
            "video_cover_timestamp_ms": 2000
        },
        "source_info": {"source": "PULL_FROM_URL", "video_url": video_url}
    }

    r = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers=headers, json=payload, timeout=30
    )
    r.raise_for_status()
    publish_id = r.json().get("data", {}).get("publish_id")
    log.info(f"TikTok initiated: {publish_id}")

    for _ in range(30):
        time.sleep(10)
        s = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
            headers=headers, json={"publish_id": publish_id}, timeout=15
        ).json()
        status = s.get("data", {}).get("status")
        if status == "PUBLISH_COMPLETE":
            log.info("TikTok posted")
            return publish_id
        elif status in ["FAILED","CANCELLED"]:
            raise Exception(f"TikTok failed: {s}")
    raise Exception("TikTok timed out")

# ============================================================
#  INSTAGRAM REELS (free Graph API)
# ============================================================

def post_instagram(video_path, caption):
    video_url = upload_free(video_path)
    base      = "https://graph.facebook.com/v19.0"

    # Create container
    r = requests.post(f"{base}/{INSTAGRAM_ACCOUNT_ID}/media", params={
        "media_type":   "REELS",
        "video_url":    video_url,
        "caption":      caption,
        "share_to_feed":"true",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }, timeout=30)
    r.raise_for_status()
    container_id = r.json().get("id")
    log.info(f"IG container: {container_id}")

    # Wait for processing
    for _ in range(30):
        time.sleep(10)
        s = requests.get(f"{base}/{container_id}", params={
            "fields":       "status_code",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }, timeout=15).json()
        if s.get("status_code") == "FINISHED":
            break
        elif s.get("status_code") == "ERROR":
            raise Exception(f"IG container error: {s}")

    # Publish
    r = requests.post(f"{base}/{INSTAGRAM_ACCOUNT_ID}/media_publish", params={
        "creation_id":  container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }, timeout=30)
    r.raise_for_status()
    media_id = r.json().get("id")
    log.info(f"Instagram posted: {media_id}")
    return media_id

# ============================================================
#  FREE FILE HOST (for TikTok + Instagram which need URLs)
# ============================================================

def upload_free(file_path):
    """
    Upload to 0x0.st — free, anonymous, no account needed.
    Files are available for up to 30 days.
    No size limit for videos under 512MB.
    """
    with open(file_path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f}, timeout=120)
    r.raise_for_status()
    url = r.text.strip()
    log.info(f"Uploaded to free host: {url}")
    return url

# ============================================================
#  ORCHESTRATOR
# ============================================================

def notify(match_data, results):
    if not TELEGRAM_BOT_TOKEN or "YOUR" in TELEGRAM_BOT_TOKEN:
        return
    lines = [
        f"✅ The Replay — Posted!",
        f"{match_data['home_team']} {match_data['home_score']}-{match_data['away_score']} {match_data['away_team']}",
        f"League: {match_data['league_display']}",
        ""
    ]
    for platform, url in results.items():
        status = "✅" if "ERROR" not in str(url) else "❌"
        lines.append(f"{status} {platform}: {url}")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": "\n".join(lines)}, timeout=5)

def publish_all(match_data, result):
    video_path = result["video_path"]
    caption    = result["caption"]
    results    = {}

    for platform, fn in [("youtube", post_youtube), ("tiktok", post_tiktok), ("instagram", post_instagram)]:
        try:
            url = fn(video_path, caption)
            results[platform] = url
            log.info(f"{platform}: posted")
        except Exception as e:
            log.error(f"{platform} error: {e}")
            results[platform] = f"ERROR: {e}"

    notify(match_data, results)
    log.info(f"All publishing complete: {results}")
    return results
