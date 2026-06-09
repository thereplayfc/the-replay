"""
THE REPLAY — Match Watcher (Free)
Polls API-Football free tier every 60s.
Fires pipeline the moment a match hits full time.
"""

import requests, time, json, os, sys, logging
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/watcher.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("watcher")

HEADERS  = {"x-apisports-key": API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io"

# Prevent double-processing
processed = set()
PROCESSED_FILE = "logs/processed.json"
try:
    with open(PROCESSED_FILE) as f:
        processed = set(json.load(f))
except FileNotFoundError:
    pass

def save_processed(fid):
    processed.add(fid)
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed), f)

def fetch_live():
    all_matches = []
    for name, lid in MONITORED_LEAGUES.items():
        try:
            r = requests.get(f"{BASE_URL}/fixtures",
                headers=HEADERS,
                params={"league": lid, "season": datetime.now().year, "live": "all"},
                timeout=10)
            for m in r.json().get("response", []):
                m["_league_name"] = name
            all_matches.extend(r.json().get("response", []))
            time.sleep(0.5)
        except Exception as e:
            log.error(f"Fetch error {name}: {e}")
    return all_matches

def fetch_details(fixture_id):
    details = {}
    endpoints = {
        "fixture":    {"id": fixture_id},
        "statistics": {"fixture": fixture_id},
        "events":     {"fixture": fixture_id},
        "players":    {"fixture": fixture_id},
    }
    for key, params in endpoints.items():
        try:
            r = requests.get(f"{BASE_URL}/fixtures/{key if key != 'fixture' else ''}",
                headers=HEADERS, params=params, timeout=10)
            details[key] = r.json().get("response", [])
            time.sleep(0.3)
        except Exception as e:
            log.error(f"Detail fetch error {key}: {e}")
            details[key] = []
    return details

def is_finished(match):
    return match.get("fixture", {}).get("status", {}).get("short") in ["FT","AET","PEN"]

def notify(msg):
    if not TELEGRAM_BOT_TOKEN or "YOUR" in TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except:
        pass

def build_match_summary(match, details):
    fix   = match.get("fixture", {})
    teams = match.get("teams", {})
    goals = match.get("goals", {})
    return {
        "fixture_id":    fix.get("id"),
        "league":        match.get("_league_name", "football"),
        "league_display":match.get("league", {}).get("name", "Football"),
        "home_team":     teams.get("home", {}).get("name", ""),
        "away_team":     teams.get("away", {}).get("name", ""),
        "home_score":    goals.get("home", 0) or 0,
        "away_score":    goals.get("away", 0) or 0,
        "venue":         fix.get("venue", {}).get("name", ""),
        "city":          fix.get("venue", {}).get("city", ""),
        "status":        fix.get("status", {}).get("short", "FT"),
        "date":          fix.get("date", ""),
        "details":       details,
    }

def watch():
    log.info("The Replay — Watcher started")
    while True:
        try:
            matches = fetch_live()
            log.info(f"Polled {len(matches)} active matches")
            for match in matches:
                fid = match.get("fixture", {}).get("id")
                if not fid or fid in processed:
                    continue
                if is_finished(match):
                    log.info(f"Full time: fixture {fid}")
                    save_processed(fid)
                    details = fetch_details(fid)
                    summary = build_match_summary(match, details)
                    log.info(f"Triggering: {summary['home_team']} vs {summary['away_team']}")
                    notify(f"The Replay: processing {summary['home_team']} {summary['home_score']}-{summary['away_score']} {summary['away_team']}")
                    time.sleep(TRIGGER_DELAY_MINUTES * 60)
                    from scripts.content_generator import run_pipeline
                    run_pipeline(summary)
        except Exception as e:
            log.error(f"Watcher error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    watch()
