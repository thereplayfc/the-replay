# ============================================================
#  THE REPLAY — Config (Claude API Edition)
# ============================================================

# --- CLAUDE API ---
# Separate from Claude Pro subscription
# Sign up at: https://console.anthropic.com
# Cost at this volume: ~$3-5/month
# Get key: console.anthropic.com → API Keys → Create Key
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"

# --- FOOTBALL DATA (free) ---
# https://rapidapi.com/api-sports/api/api-football
API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"

# --- VOICEOVER (free - no key needed) ---
# Edge-TTS runs locally via Python, no account, no limits
EDGE_TTS_VOICE = "en-US-GuyNeural"
# Alternatives: "en-GB-RyanNeural" | "en-AU-WilliamNeural"

# --- YOUTUBE (free API) ---
YOUTUBE_CLIENT_ID     = "YOUR_YOUTUBE_CLIENT_ID"
YOUTUBE_CLIENT_SECRET = "YOUR_YOUTUBE_CLIENT_SECRET"
YOUTUBE_CHANNEL_ID    = "YOUR_YOUTUBE_CHANNEL_ID"

# --- TIKTOK (free API) ---
TIKTOK_CLIENT_KEY    = "YOUR_TIKTOK_CLIENT_KEY"
TIKTOK_CLIENT_SECRET = "YOUR_TIKTOK_CLIENT_SECRET"
TIKTOK_ACCESS_TOKEN  = "YOUR_TIKTOK_ACCESS_TOKEN"

# --- INSTAGRAM (free API) ---
INSTAGRAM_ACCESS_TOKEN = "YOUR_INSTAGRAM_ACCESS_TOKEN"
INSTAGRAM_ACCOUNT_ID   = "YOUR_INSTAGRAM_ACCOUNT_ID"

# --- TELEGRAM (free, optional) ---
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID   = "YOUR_TELEGRAM_CHAT_ID"

# ============================================================
#  CHANNEL SETTINGS
# ============================================================

CHANNEL_NAME    = "The Replay"
CHANNEL_HANDLE  = "@th3replayfc"
CHANNEL_TAGLINE = "Every goal. Every moment. Replayed."

MONITORED_LEAGUES = {
    "world_cup":        1,
    "premier_league":   39,
    "la_liga":          140,
    "champions_league": 2,
    "serie_a":          135,
    "bundesliga":       78,
}

TRIGGER_DELAY_MINUTES = 3
VIDEO_WIDTH   = 1080
VIDEO_HEIGHT  = 1920
VIDEO_FPS     = 30
VIDEO_DURATION = 58

COLOR_BG     = (6,   6,  12)
COLOR_ACCENT = (226, 75, 74)
COLOR_BLUE   = (55, 138,221)
COLOR_GREEN  = (99, 153, 34)
COLOR_AMBER  = (239,159, 39)
COLOR_WHITE  = (255,255,255)
COLOR_GREY   = (100,100,120)
COLOR_DARK   = (20,  20, 35)
COLOR_CARD   = (14,  14, 28)

HASHTAGS = "#Football #WorldCup #PremierLeague #LaLiga #Goals #TheReplay #Soccer #FootballHighlights #Shorts"
