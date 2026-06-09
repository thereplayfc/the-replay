"""
THE REPLAY — Content Generator
Uses Claude API (claude-haiku) for scripts + captions
Uses Edge-TTS (free, no limits) for voiceover
~$3-5/month API cost at full World Cup volume
"""

import os, sys, json, time, logging, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *

log = logging.getLogger("content_generator")

# ============================================================
#  CLAUDE API CLIENT
# ============================================================

def claude(prompt, system=None, max_tokens=600):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msgs   = [{"role": "user", "content": prompt}]
    kwargs = {
        "model":      "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "messages":   msgs,
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return resp.content[0].text.strip()

# ============================================================
#  STEP 1 — SCRIPT
# ============================================================

SYSTEM_SCRIPT = """You are the AI presenter for "The Replay" — a viral football short-form channel.
Your style: high energy, opinionated, controversial, punchy. Short sentences. No filler.
You take sides. You spark debate. Every word earns its place."""

def build_match_json(match_data):
    events = match_data.get("details", {}).get("events", [])
    goals  = [e for e in events if e.get("type") == "Goal"]
    cards  = [e for e in events if e.get("type") == "Card"]
    stats  = match_data.get("details", {}).get("statistics", [])

    def get_stat(team_name, stat_name):
        for s in stats:
            if s.get("team", {}).get("name") == team_name:
                for st in s.get("statistics", []):
                    if st["type"] == stat_name:
                        return str(st.get("value", "N/A") or "N/A")
        return "N/A"

    return json.dumps({
        "home_team":  match_data["home_team"],
        "away_team":  match_data["away_team"],
        "score":      f"{match_data['home_score']}-{match_data['away_score']}",
        "league":     match_data["league_display"],
        "venue":      match_data.get("venue", ""),
        "status":     match_data.get("status", "FT"),
        "goals": [{
            "team":   g.get("team",   {}).get("name", ""),
            "player": g.get("player", {}).get("name", ""),
            "minute": g.get("time",   {}).get("elapsed", ""),
            "type":   g.get("detail", ""),
            "assist": g.get("assist", {}).get("name", ""),
        } for g in goals],
        "red_cards": [{
            "team":   c.get("team",   {}).get("name", ""),
            "player": c.get("player", {}).get("name", ""),
            "minute": c.get("time",   {}).get("elapsed", ""),
        } for c in cards if "Red" in c.get("detail", "")],
        "possession_home": get_stat(match_data["home_team"], "Ball Possession"),
        "possession_away": get_stat(match_data["away_team"], "Ball Possession"),
        "shots_home":      get_stat(match_data["home_team"], "Shots on Goal"),
        "shots_away":      get_stat(match_data["away_team"], "Shots on Goal"),
        "xg_home":         get_stat(match_data["home_team"], "expected_goals"),
        "xg_away":         get_stat(match_data["away_team"], "expected_goals"),
    }, ensure_ascii=False, indent=2)

def write_script(match_data):
    match_json = build_match_json(match_data)
    prompt = f"""Write a 58-second spoken script for this match highlight video.

Match data:
{match_json}

STRUCTURE (follow exactly, no headers needed in output):
1. HOOK (0-7s): Open mid-action on the most dramatic moment. No "welcome" or intros.
2. SCORE (7-12s): Drop the final result with energy.  
3. CONTROVERSY (12-26s): The most debatable moment — VAR, penalty shout, red card, referee howler. Take a strong side. Be opinionated.
4. GOALS (26-43s): Each goal in one sentence. Player, minute, why it was special or why it shouldn't have counted.
5. MOTM (43-53s): Name the player of the match. Add one spicy alternative take.
6. CTA (53-58s): One polarising question. End with: "This is The Replay."

RULES:
- 130-145 words total
- Punchy short sentences
- Be controversial — safe takes get no comments
- No stage directions, no timestamps, no headers
- Return the spoken script ONLY"""

    script = claude(prompt, system=SYSTEM_SCRIPT, max_tokens=500)
    log.info(f"Script: {len(script.split())} words")
    return script

# ============================================================
#  STEP 2 — CONTROVERSY ANGLE (feeds into video graphics)
# ============================================================

def extract_controversy(match_data, script):
    """Extract the main controversy for the overlay graphic."""
    events = match_data.get("details", {}).get("events", [])
    red_cards = [e for e in events if "Red" in e.get("detail", "")]
    goals = [e for e in events if e.get("type") == "Goal"]
    penalties = [g for g in goals if "Penalty" in g.get("detail", "")]

    prompt = f"""Given this match and script, write ONE controversy headline (max 8 words) and ONE body line (max 15 words).

Match: {match_data['home_team']} {match_data['home_score']}-{match_data['away_score']} {match_data['away_team']}
Red cards: {len(red_cards)}
Penalties scored: {len(penalties)}
Script excerpt: {script[:300]}

Return JSON only:
{{"headline": "...", "body": "..."}}"""

    try:
        result = claude(prompt, max_tokens=100)
        # Strip any markdown
        result = result.replace("```json","").replace("```","").strip()
        return json.loads(result)
    except:
        return {
            "headline": "TALKING POINT",
            "body": f"{match_data['home_team']} vs {match_data['away_team']} — what did you think?"
        }

# ============================================================
#  STEP 3 — CAPTION
# ============================================================

def write_caption(match_data, script):
    prompt = f"""Write a viral caption for this football video on Instagram, TikTok and YouTube.

Match: {match_data['home_team']} {match_data['home_score']}-{match_data['away_score']} {match_data['away_team']}
League: {match_data['league_display']}
Script tone: {script[:150]}

RULES:
- Line 1: Scroll-stopping hook. Max 2 emojis. Brutally short.
- Line 2: The result
- Line 3: One question that splits opinions and drives comments
- Line 4 (new line): {HASHTAGS}
- Max 120 words. No fluff. Return caption only."""

    return claude(prompt, max_tokens=250)

# ============================================================
#  STEP 4 — VOICEOVER (Edge-TTS, completely free)
# ============================================================

async def _tts(script, path):
    import edge_tts
    tts = edge_tts.Communicate(script, EDGE_TTS_VOICE)
    await tts.save(path)

def generate_voiceover(script, output_path):
    asyncio.run(_tts(script, output_path))
    size = os.path.getsize(output_path)
    log.info(f"Voiceover: {output_path} ({size//1024}KB)")
    return output_path

# ============================================================
#  STEP 5 — GRAPHIC DATA
# ============================================================

def build_graphic_data(match_data, controversy):
    events = match_data.get("details", {}).get("events", [])
    goals  = [e for e in events if e.get("type") == "Goal"]
    stats  = match_data.get("details", {}).get("statistics", [])

    def get_stat(team_name, stat_name):
        for s in stats:
            if s.get("team", {}).get("name") == team_name:
                for st in s.get("statistics", []):
                    if st["type"] == stat_name:
                        val = st.get("value", "0") or "0"
                        return str(val).replace("%","")
        return "0"

    # Find MOTM — player with most goals, or assist + goal
    scorers = {}
    for g in goals:
        p = g.get("player", {}).get("name", "")
        if p:
            scorers[p] = scorers.get(p, 0) + 1
    motm_name = max(scorers, key=scorers.get) if scorers else "Outstanding Performance"
    motm_goals = scorers.get(motm_name, 0)

    return {
        "home_team":    match_data["home_team"],
        "away_team":    match_data["away_team"],
        "home_score":   match_data["home_score"],
        "away_score":   match_data["away_score"],
        "league":       match_data["league_display"],
        "venue":        match_data.get("venue", ""),
        "status":       match_data.get("status", "FT"),
        "controversy":  controversy,
        "goals": [{
            "player": g.get("player", {}).get("name", "Unknown"),
            "team":   g.get("team",   {}).get("name", ""),
            "minute": g.get("time",   {}).get("elapsed", 0),
            "type":   g.get("detail", "Normal Goal"),
            "assist": g.get("assist", {}).get("name", ""),
        } for g in goals[:6]],
        "poss_home":  get_stat(match_data["home_team"], "Ball Possession"),
        "poss_away":  get_stat(match_data["away_team"], "Ball Possession"),
        "shots_home": get_stat(match_data["home_team"], "Shots on Goal"),
        "shots_away": get_stat(match_data["away_team"], "Shots on Goal"),
        "xg_home":    get_stat(match_data["home_team"], "expected_goals"),
        "xg_away":    get_stat(match_data["away_team"], "expected_goals"),
        "motm_name":  motm_name,
        "motm_goals": motm_goals,
    }

# ============================================================
#  MAIN PIPELINE
# ============================================================

def run_pipeline(match_data):
    log.info(f"Pipeline: {match_data['home_team']} vs {match_data['away_team']}")
    os.makedirs("output", exist_ok=True)
    ts = int(time.time())

    try:
        # 1. Script (Claude API)
        script = write_script(match_data)
        with open(f"output/script_{ts}.txt", "w") as f:
            f.write(script)

        # 2. Controversy angle (Claude API)
        controversy = extract_controversy(match_data, script)

        # 3. Caption (Claude API)
        caption = write_caption(match_data, script)
        with open(f"output/caption_{ts}.txt", "w") as f:
            f.write(caption)

        # 4. Voiceover (Edge-TTS — free)
        audio_path = generate_voiceover(script, f"output/vo_{ts}.mp3")

        # 5. Graphic data
        gfx = build_graphic_data(match_data, controversy)

        # 6. Render video (Python + FFmpeg — free)
        from scripts.video_renderer import render_video
        video_path = render_video(gfx, audio_path, f"output/video_{ts}.mp4")

        result = {
            "status":     "success",
            "video_path": video_path,
            "caption":    caption,
            "script":     script,
        }
        log.info(f"Pipeline complete: {video_path}")

    except Exception as e:
        log.error(f"Pipeline error: {e}", exc_info=True)
        result = {"status": "error", "error": str(e)}

    with open(f"output/manifest_{ts}.json", "w") as f:
        json.dump({"match": match_data, "result": result, "ts": ts}, f, indent=2)

    if result["status"] == "success":
        from scripts.publisher import publish_all
        publish_all(match_data, result)

    return result
