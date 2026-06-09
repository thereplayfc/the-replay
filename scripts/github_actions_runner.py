"""
THE REPLAY — GitHub Actions Runner
Designed for single-execution (GitHub Actions cron job).
Checks for finished matches ONCE, processes any found, then exits.
This keeps us well within GitHub's free 2000 min/month limit.
"""

import os, sys, json, requests, time, logging
from datetime import datetime

# Inject env vars into config at runtime
import config.config as cfg
for key in ["API_FOOTBALL_KEY","ANTHROPIC_API_KEY","YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_CHANNEL_ID","TIKTOK_CLIENT_KEY","TIKTOK_CLIENT_SECRET","TIKTOK_ACCESS_TOKEN",
            "INSTAGRAM_ACCESS_TOKEN","INSTAGRAM_ACCOUNT_ID","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID"]:
    val = os.environ.get(key)
    if val:
        setattr(cfg, key, val)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
log = logging.getLogger("runner")

HEADERS  = {"x-apisports-key": cfg.API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io"
PROCESSED_FILE = "logs/processed.json"

os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

try:
    with open(PROCESSED_FILE) as f:
        processed = set(json.load(f))
except:
    processed = set()

def save_processed():
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed), f)

def fetch_finished():
    finished = []
    for name, lid in cfg.MONITORED_LEAGUES.items():
        try:
            r = requests.get(f"{BASE_URL}/fixtures",
                headers=HEADERS,
                params={"league": lid, "season": datetime.now().year, "live": "all"},
                timeout=10)
            for m in r.json().get("response", []):
                status = m.get("fixture", {}).get("status", {}).get("short")
                if status in ["FT","AET","PEN"]:
                    m["_league_name"] = name
                    fid = m.get("fixture", {}).get("id")
                    if fid and fid not in processed:
                        finished.append(m)
            time.sleep(0.5)
        except Exception as e:
            log.error(f"Fetch error {name}: {e}")
    return finished

def fetch_details(fixture_id):
    details = {}
    for key, params in [
        ("fixture",    {"id": fixture_id}),
        ("statistics", {"fixture": fixture_id}),
        ("events",     {"fixture": fixture_id}),
        ("players",    {"fixture": fixture_id}),
    ]:
        try:
            endpoint = "" if key == "fixture" else f"/{key}"
            r = requests.get(f"{BASE_URL}/fixtures{endpoint}",
                headers=HEADERS, params=params, timeout=10)
            details[key] = r.json().get("response", [])
            time.sleep(0.3)
        except Exception as e:
            log.error(f"Detail error {key}: {e}")
            details[key] = []
    return details

def run():
    log.info(f"The Replay runner started — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    finished = fetch_finished()

    if not finished:
        log.info("No new finished matches. Exiting.")
        return

    log.info(f"Found {len(finished)} new finished matches")

    for match in finished:
        fid   = match.get("fixture", {}).get("id")
        teams = match.get("teams", {})
        goals = match.get("goals", {})
        home  = teams.get("home", {}).get("name", "")
        away  = teams.get("away", {}).get("name", "")
        log.info(f"Processing: {home} vs {away} (fixture {fid})")

        processed.add(fid)
        save_processed()

        try:
            details = fetch_details(fid)
            fix     = match.get("fixture", {})
            summary = {
                "fixture_id":    fid,
                "league":        match.get("_league_name", "football"),
                "league_display":match.get("league", {}).get("name", "Football"),
                "home_team":     home,
                "away_team":     away,
                "home_score":    goals.get("home", 0) or 0,
                "away_score":    goals.get("away", 0) or 0,
                "venue":         fix.get("venue", {}).get("name", ""),
                "city":          fix.get("venue", {}).get("city", ""),
                "status":        fix.get("status", {}).get("short", "FT"),
                "date":          fix.get("date", ""),
                "details":       details,
            }

            from scripts.content_generator import run_pipeline
            result = run_pipeline(summary)
            log.info(f"Pipeline result: {result.get('status')}")

        except Exception as e:
            log.error(f"Pipeline error for {fid}: {e}")

    log.info("Runner complete")

if __name__ == "__main__":
    run()
