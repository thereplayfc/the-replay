# The Replay — Setup Guide
## Total cost: ~$23-25/month (Claude Pro $20 + API ~$3-5)

---

## Why two Claude charges?

| What | Cost | What it does |
|---|---|---|
| Claude Pro (claude.ai) | $20/mo | Your chat interface — already paying |
| Claude API | ~$3-5/mo | The automated pipeline calls Claude to write scripts |

They're separate Anthropic products. The API billing is usage-based — at 10 videos/day using claude-haiku, you'll spend roughly $3-5/month. First $5 of API credit is free when you sign up.

---

## Step 1 — Get your Claude API key (5 mins)

1. Go to https://console.anthropic.com
2. Sign in with the same email as your Claude Pro account
3. Go to **API Keys** → **Create Key**
4. Copy the key — save it as `ANTHROPIC_API_KEY`

That's it. You now have API access.

---

## Step 2 — Create your social accounts (20 mins)

| Platform | Handle |
|---|---|
| YouTube | @th3replayfc |
| TikTok | @th3replayfc |
| Instagram | @th3replayfc |

**Bio for all three:**
```
Every goal. Every moment. Replayed.
World Cup | Premier League | La Liga | UCL
New video within minutes of every match ⚽
```

---

## Step 3 — Get your free API keys (30 mins)

### API-Football (match data — free)
1. Go to https://rapidapi.com/api-sports/api/api-football
2. Sign up free → subscribe to free tier
3. Copy API key → `API_FOOTBALL_KEY`

### YouTube Data API (posting — free)
1. Go to https://console.cloud.google.com
2. New project → "TheReplay"
3. Enable "YouTube Data API v3"
4. Credentials → OAuth 2.0 Client ID → Desktop App
5. Copy Client ID + Secret
6. Run: `python scripts/setup_youtube_auth.py` on your laptop
7. Browser opens → log in → Allow → token saved

### TikTok API (posting — free)
1. Go to https://developers.tiktok.com → Register
2. Create app → request "Content Posting API"
3. Approval: 1-3 business days
4. Copy Client Key, Secret + generate Access Token

### Instagram Graph API (posting — free)
1. Go to https://developers.facebook.com
2. Create app → Instagram Graph API
3. Connect @th3replayfc account
4. Generate long-lived access token
5. Copy token + Account ID

### Telegram (notifications — free, optional)
1. Message @BotFather on Telegram → /newbot
2. Copy token → `TELEGRAM_BOT_TOKEN`
3. Message @userinfobot → copy ID → `TELEGRAM_CHAT_ID`

---

## Step 4 — GitHub Setup (15 mins)

1. Create free account at https://github.com
2. New repository → `the-replay` → **Public** (public = 2000 free minutes/month)
3. Upload all project files
4. **Settings → Secrets → Actions** → Add each:

| Secret name | Value |
|---|---|
| ANTHROPIC_API_KEY | your Claude API key |
| API_FOOTBALL_KEY | your key |
| YOUTUBE_CLIENT_ID | your key |
| YOUTUBE_CLIENT_SECRET | your key |
| YOUTUBE_CHANNEL_ID | your channel ID |
| YOUTUBE_TOKEN | paste contents of youtube_token.json |
| TIKTOK_CLIENT_KEY | your key |
| TIKTOK_CLIENT_SECRET | your key |
| TIKTOK_ACCESS_TOKEN | your token |
| INSTAGRAM_ACCESS_TOKEN | your token |
| INSTAGRAM_ACCOUNT_ID | your ID |
| TELEGRAM_BOT_TOKEN | your token |
| TELEGRAM_CHAT_ID | your ID |

5. Go to **Actions** tab → Enable workflows
6. Click "Run workflow" to test immediately

---

## Step 5 — Test it

```bash
# Install dependencies locally
pip install -r requirements.txt
sudo apt install ffmpeg  # or: brew install ffmpeg on Mac

# Run a test with a fake Arsenal vs PSG match
python scripts/test_pipeline.py

# Or trigger manually on GitHub:
# Actions → The Replay Match Watcher → Run workflow
```

---

## How it runs automatically

GitHub Actions polls every 10 minutes between 10:00–23:00 UTC.
- No match found → exits in ~15 seconds
- Match found → runs full pipeline → posts to all 3 platforms → Telegram notification

**You never touch it again after setup.**

---

## Cost breakdown (honest)

| Service | Cost |
|---|---|
| Claude API (haiku model, ~10 videos/day) | ~$3-5/mo |
| API-Football free tier | $0 |
| Edge-TTS voiceover | $0 |
| Python + FFmpeg video rendering | $0 |
| GitHub Actions hosting | $0 |
| YouTube / TikTok / Instagram APIs | $0 |
| 0x0.st file hosting | $0 |
| **API total** | **~$3-5/mo** |
| **+ Claude Pro you already pay** | **$20/mo** |
| **All in** | **~$23-25/mo** |

---

## Upgrade path (when you get traction)

| Milestone | Add | Cost |
|---|---|---|
| 5K followers | ElevenLabs (better voice) | +$5/mo |
| 10K followers | HeyGen (AI avatar face) | +$29/mo |
| First sponsor deal | API-Football Pro (real-time) | +$10/mo |
| 50K followers | Full premium stack | ~$76/mo total |

---

## Troubleshooting

**Claude API key not working?**
Check https://console.anthropic.com → your key is active and has credit

**TikTok API still pending?**
Start with YouTube + Instagram only. Add TikTok once approved.

**Video rendering slow?**
Normal — FFmpeg on GitHub Actions takes 2-3 mins per video. Fine for post-match content.

**YouTube token expired?**
Re-run `setup_youtube_auth.py` → update the YOUTUBE_TOKEN secret on GitHub
