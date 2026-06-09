"""
THE REPLAY — Video Renderer (100% Free)
Pure Python + Pillow + FFmpeg
Generates a professional 1080x1920 animated highlight video
No paid services. No watermarks. No limits.
"""

import os, sys, json, math, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *

W, H   = VIDEO_WIDTH, VIDEO_HEIGHT
FPS    = VIDEO_FPS
FONTS  = {}

def load_fonts():
    """Load fonts — falls back to default if custom not available."""
    sizes = [16, 20, 24, 28, 32, 40, 48, 56, 64, 80, 96, 120]
    for sz in sizes:
        try:
            FONTS[sz] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", sz)
        except:
            try:
                FONTS[sz] = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", sz)
            except:
                FONTS[sz] = ImageFont.load_default()
    return FONTS

def get_font(size):
    closest = min(FONTS.keys(), key=lambda x: abs(x - size))
    return FONTS[closest]

# ============================================================
#  DRAWING UTILITIES
# ============================================================

def make_base():
    img = Image.new("RGB", (W, H), COLOR_BG)
    draw = ImageDraw.Draw(img)
    # Subtle gradient — darker at bottom
    for y in range(H):
        alpha = int(y / H * 30)
        draw.line([(0, y), (W, y)], fill=(max(0, COLOR_BG[0]-alpha//3),
                                           max(0, COLOR_BG[1]-alpha//3),
                                           max(0, COLOR_BG[2]-alpha//3)))
    return img, draw

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=2):
    x1, y1, x2, y2 = xy
    if fill:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=outline, width=width)

def draw_text_centered(draw, text, y, font_size, color=COLOR_WHITE, max_width=None):
    font  = get_font(font_size)
    mw    = max_width or W - 80
    lines = textwrap.wrap(text, width=int(mw / (font_size * 0.55)))
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw   = bbox[2] - bbox[0]
        x    = (W - tw) // 2
        draw.text((x, y + i * (font_size + 8)), line, font=font, fill=color)
    return len(lines) * (font_size + 8)

def draw_topbar(draw):
    draw.rectangle([(0, 0), (W, 110)], fill=(10, 10, 20))
    font = get_font(36)
    draw.text((60, 35), "THE REPLAY", font=font, fill=COLOR_WHITE)
    bx1, by1, bx2, by2 = W-220, 30, W-40, 80
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=8, fill=COLOR_ACCENT)
    bf   = get_font(24)
    draw.text((bx1+16, by1+10), "FULL TIME", font=bf, fill=COLOR_WHITE)

def draw_progress_bar(draw, progress):
    draw.rectangle([(0, 108), (W, 114)], fill=(20, 20, 40))
    draw.rectangle([(0, 108), (int(W * progress), 114)], fill=COLOR_ACCENT)

def easeOutCubic(t):
    return 1 - (1 - t) ** 3

# ============================================================
#  SEGMENT RENDERERS
# ============================================================

def render_hook_frames(gfx, n_frames):
    """0-8s: Dramatic score reveal"""
    frames = []
    total  = n_frames
    for i in range(total):
        t    = i / total
        img, draw = make_base()
        draw_topbar(draw)
        draw_progress_bar(draw, t * 0.13)

        # League badge
        draw_text_centered(draw, gfx["league"].upper(), 200, 28, COLOR_GREY)

        # Score reveal with animation
        prog = easeOutCubic(min(1.0, t * 3))
        score_y  = 300
        score_sz = int(48 + prog * 72)  # 48→120

        # Teams
        font_team = get_font(44)
        draw.text((80, score_y + 40), gfx["home_team"], font=font_team, fill=COLOR_WHITE)
        draw.text((80, score_y + 100), gfx["away_team"], font=font_team, fill=COLOR_GREY)

        # Score
        font_score = get_font(min(120, score_sz))
        alpha = int(prog * 255)
        sc_text = f"{gfx['home_score']} - {gfx['away_score']}"
        draw.text((W-320, score_y + 30), sc_text, font=font_score, fill=COLOR_WHITE)

        # Venue
        if t > 0.5:
            venue_alpha = easeOutCubic((t - 0.5) * 2)
            draw.text((80, score_y + 200), gfx.get("venue", ""), font=get_font(28), fill=COLOR_GREY)

        # Divider line
        if t > 0.3:
            lp = easeOutCubic((t - 0.3) / 0.7)
            draw.rectangle([(80, score_y + 170), (int(80 + 920 * lp), score_y + 173)], fill=COLOR_ACCENT)

        frames.append(img)
    return frames

def render_controversy_frames(gfx, script_lines, n_frames):
    """8-25s: Controversy card + key events"""
    frames = []
    events_to_show = []
    # Find controversial events from goals/cards
    for g in gfx.get("goals", []):
        if "Penalty" in g.get("type", "") or "Own" in g.get("type", ""):
            events_to_show.append(f"PEN · {g['minute']}' · {g['player']}")
    if not events_to_show:
        events_to_show = ["VAR REVIEW", "CONTROVERSIAL DECISION"]

    for i in range(n_frames):
        t    = i / n_frames
        img, draw = make_base()
        draw_topbar(draw)
        draw_progress_bar(draw, 0.13 + t * 0.29)

        # Section label
        lb_prog = easeOutCubic(min(1.0, t * 4))
        lx = int(-300 + lb_prog * 380)
        draw.text((lx, 160), "CONTROVERSY", font=get_font(36), fill=COLOR_ACCENT)

        # Main controversy card slides in
        if t > 0.15:
            cp = easeOutCubic(min(1.0, (t - 0.15) * 3))
            cy = int(820 - cp * 820 + 240)
            draw_rounded_rect(draw, (60, cy, W-60, cy+380), 20,
                fill=(30, 8, 8), outline=COLOR_ACCENT, width=2)
            if cp > 0.5:
                draw.text((90, cy+30), "THE TALKING POINT", font=get_font(26), fill=COLOR_ACCENT)
                inner_p = easeOutCubic((cp-0.5)*2)
                # Score line inside card
                draw.text((90, cy+80), f"{gfx['home_team']}  {gfx['home_score']} — {gfx['away_score']}  {gfx['away_team']}",
                    font=get_font(32), fill=COLOR_WHITE)
                draw.rectangle([(90, cy+130), (int(90 + 860 * inner_p), cy+133)], fill=COLOR_ACCENT)

                if cp > 0.8:
                    tp = easeOutCubic((cp-0.8)*5)
                    draw.text((90, cy+155), events_to_show[0] if events_to_show else "VAR CHAOS",
                        font=get_font(28), fill=COLOR_AMBER)
                    draw.text((90, cy+210),
                        "Were the officials right?", font=get_font(26), fill=COLOR_GREY)

        # Floating opinion bubble
        if t > 0.6:
            bp = easeOutCubic((t-0.6)*2.5)
            bx = int(W + 100 - bp * (W-100))
            draw_rounded_rect(draw, (bx, 700, W-40, 800), 15,
                fill=COLOR_DARK, outline=COLOR_BLUE, width=2)
            if bp > 0.5:
                draw.text((bx+20, 725), "Drop your verdict below 👇",
                    font=get_font(24), fill=COLOR_WHITE)

        frames.append(img)
    return frames

def render_goals_frames(gfx, n_frames):
    """25-42s: Animated goal cards"""
    goals   = gfx.get("goals", [])
    frames  = []
    per_goal = n_frames / max(len(goals), 1)

    for i in range(n_frames):
        t      = i / n_frames
        img, draw = make_base()
        draw_topbar(draw)
        draw_progress_bar(draw, 0.42 + t * 0.29)

        draw.text((80, 160), "GOALS BREAKDOWN", font=get_font(36), fill=COLOR_BLUE)
        draw.rectangle([(80, 205), (400, 208)], fill=COLOR_BLUE)

        # Score bar at top
        draw_rounded_rect(draw, (60, 230, W-60, 320), 15, fill=COLOR_DARK)
        draw.text((100, 255), gfx["home_team"], font=get_font(28), fill=COLOR_WHITE)
        draw.text((W-200, 255), gfx["away_team"], font=get_font(28), fill=COLOR_GREY)
        draw.text((W//2 - 50, 248), f"{gfx['home_score']} — {gfx['away_score']}",
            font=get_font(40), fill=COLOR_WHITE)

        # Goal cards appear one by one
        for gi, goal in enumerate(goals[:5]):
            card_t = max(0, min(1, (t - gi * 0.18) * 5))
            if card_t <= 0:
                continue
            cy = 360 + gi * 200
            cx = int(W + 100 - easeOutCubic(card_t) * (W + 100 - 60))

            # Card colour based on team
            is_home = goal["team"] == gfx["home_team"]
            card_col = (10, 25, 10) if is_home else (25, 10, 10)
            border_col = COLOR_GREEN if is_home else COLOR_ACCENT

            draw_rounded_rect(draw, (cx, cy, W-40, cy+170), 16,
                fill=card_col, outline=border_col, width=2)

            if card_t > 0.4:
                # Minute badge
                draw_rounded_rect(draw, (cx+20, cy+20, cx+110, cy+70), 10, fill=border_col)
                draw.text((cx+28, cy+28), f"{goal['minute']}'", font=get_font(30), fill=COLOR_WHITE)

                # Player name
                draw.text((cx+130, cy+25), goal["player"], font=get_font(32), fill=COLOR_WHITE)
                draw.text((cx+130, cy+68), goal["team"], font=get_font(22), fill=COLOR_GREY)

                # Goal type
                gt = goal.get("type", "")
                gt_col = COLOR_AMBER if "Penalty" in gt else (COLOR_GREEN if is_home else COLOR_ACCENT)
                draw.text((cx+20, cy+100), gt if gt else "Normal Goal", font=get_font(24), fill=gt_col)

                # Assist
                if goal.get("assist"):
                    draw.text((cx+20, cy+135), f"Assist: {goal['assist']}", font=get_font(22), fill=COLOR_GREY)

        frames.append(img)
    return frames

def render_stats_frames(gfx, n_frames):
    """42-50s: Animated stats comparison"""
    frames = []
    for i in range(n_frames):
        t    = i / n_frames
        img, draw = make_base()
        draw_topbar(draw)
        draw_progress_bar(draw, 0.71 + t * 0.14)

        draw.text((80, 160), "MATCH STATS", font=get_font(36), fill=COLOR_BLUE)
        draw.rectangle([(80, 205), (350, 208)], fill=COLOR_BLUE)

        stats_data = [
            ("Possession", gfx.get("poss_home","50"), gfx.get("poss_away","50"), "%"),
            ("Shots on Target", gfx.get("shots_home","0"), gfx.get("shots_away","0"), ""),
            ("xG", gfx.get("xg_home","0"), gfx.get("xg_away","0"), ""),
        ]

        for si, (label, hv, av, unit) in enumerate(stats_data):
            sy = 280 + si * 240
            if t < si * 0.3:
                continue
            sp = easeOutCubic(min(1.0, (t - si * 0.3) * 3))

            # Team names
            draw.text((80, sy), gfx["home_team"], font=get_font(30), fill=COLOR_BLUE)
            draw.text((W-80-len(gfx["away_team"])*18, sy), gfx["away_team"], font=get_font(30), fill=COLOR_ACCENT)

            # Stat label
            draw.text((W//2 - len(label)*8, sy), label, font=get_font(24), fill=COLOR_GREY)

            # Values
            hval = str(hv).replace("%","")
            aval = str(av).replace("%","")
            try: hf = float(hval) ; af = float(aval)
            except: hf = 50.0;     af = 50.0
            total = hf + af if (hf + af) > 0 else 100
            h_pct = hf / total
            a_pct = af / total

            # Bar background
            bar_y = sy + 50
            draw.rounded_rectangle([(80, bar_y), (W-80, bar_y+28)], radius=14, fill=COLOR_DARK)

            # Animated bars
            bar_w = W - 160
            h_bar_w = int(bar_w * h_pct * sp)
            a_bar_w = int(bar_w * a_pct * sp)

            if h_bar_w > 0:
                draw.rounded_rectangle([(80, bar_y), (80+h_bar_w, bar_y+28)],
                    radius=14, fill=COLOR_BLUE)
            if a_bar_w > 0:
                draw.rounded_rectangle([(W-80-a_bar_w, bar_y), (W-80, bar_y+28)],
                    radius=14, fill=COLOR_ACCENT)

            # Values under bars
            draw.text((80, bar_y+36), f"{hval}{unit}", font=get_font(28), fill=COLOR_BLUE)
            draw.text((W-80-60, bar_y+36), f"{aval}{unit}", font=get_font(28), fill=COLOR_ACCENT)

        frames.append(img)
    return frames

def render_motm_frames(gfx, n_frames):
    """50-56s: Player of the match"""
    frames = []
    goals  = gfx.get("goals", [])
    # Pick player with most goal involvement
    scorers = {}
    for g in goals:
        p = g.get("player", "Unknown")
        scorers[p] = scorers.get(p, 0) + 1
    motm = max(scorers, key=scorers.get) if scorers else "Outstanding Performance"

    for i in range(n_frames):
        t    = i / n_frames
        img, draw = make_base()
        draw_topbar(draw)
        draw_progress_bar(draw, 0.85 + t * 0.1)

        cp = easeOutCubic(min(1.0, t * 2))

        draw.text((80, 160), "PLAYER OF THE MATCH", font=get_font(32), fill=COLOR_AMBER)
        draw.rectangle([(80, 205), (560, 208)], fill=COLOR_AMBER)

        # Big circular avatar placeholder
        cx_c, cy_c, r = W//2, 600, 200
        # Outer glow ring
        for ring in range(3):
            ring_alpha = int((0.3 - ring*0.08) * 255 * cp)
            draw.ellipse([(cx_c-r-ring*15, cy_c-r-ring*15),
                          (cx_c+r+ring*15, cy_c+r+ring*15)],
                         outline=COLOR_AMBER, width=max(1, 3-ring))

        draw.ellipse([(cx_c-r, cy_c-r), (cx_c+r, cy_c+r)], fill=COLOR_DARK)
        draw.ellipse([(cx_c-r, cy_c-r), (cx_c+r, cy_c+r)], outline=COLOR_AMBER, width=4)

        # Silhouette
        draw.ellipse([(cx_c-55, cy_c-110), (cx_c+55, cy_c+10)], fill=COLOR_GREY)
        draw.ellipse([(cx_c-100, cy_c+10), (cx_c+100, cy_c+160)], fill=COLOR_GREY)

        if cp > 0.4:
            name_p = easeOutCubic((cp-0.4)*1.67)
            ny = 840
            draw_text_centered(draw, motm, ny, int(40 + name_p*16), COLOR_WHITE)

            goals_count = scorers.get(motm, 0)
            draw_text_centered(draw, f"{goals_count} goal{'s' if goals_count != 1 else ''} · {gfx['league']}", ny+70, 28, COLOR_GREY)

        # Rating ring
        if t > 0.5:
            rp = easeOutCubic((t-0.5)*2)
            rating = 9.1
            angle  = int(rp * rating / 10 * 360)
            ry1, ry2 = 960, 1090
            draw.arc([(W//2-65, ry1), (W//2+65, ry2)], start=-90, end=-90+angle,
                fill=COLOR_AMBER, width=8)
            draw.text((W//2-28, ry1+35), f"{rating:.1f}", font=get_font(40), fill=COLOR_AMBER)
            draw.text((W//2-18, ry1+85), "/10", font=get_font(24), fill=COLOR_GREY)

        frames.append(img)
    return frames

def render_cta_frames(gfx, n_frames):
    """56-58s: Call to action"""
    frames = []
    for i in range(n_frames):
        t    = i / n_frames
        img, draw = make_base()
        draw_topbar(draw)
        draw_progress_bar(draw, 0.95 + t * 0.05)

        # Final score big
        p = easeOutCubic(min(1.0, t * 3))
        draw_text_centered(draw, f"{gfx['home_team']}  {gfx['home_score']} — {gfx['away_score']}  {gfx['away_team']}",
            300, 40, COLOR_WHITE)
        draw.rectangle([(W//2-200, 380), (W//2+200, 383)], fill=COLOR_ACCENT)

        # CTA
        if t > 0.3:
            cp = easeOutCubic((t-0.3)*1.4)
            draw_text_centered(draw, "Drop your take in the comments", 460, int(32*cp+10), COLOR_WHITE)
            draw_text_centered(draw, "Who was YOUR player of the match?", 520, int(28*cp+8), COLOR_GREY)

        # Follow button
        if t > 0.6:
            fp = easeOutCubic((t-0.6)*2.5)
            bw = int(500 * fp)
            bx = W//2 - bw//2
            if bw > 40:
                draw.rounded_rectangle([(bx, 680), (bx+bw, 760)], radius=20, fill=COLOR_ACCENT)
                if fp > 0.8:
                    draw.text((W//2-140, 698), f"Follow {CHANNEL_HANDLE}", font=get_font(30), fill=COLOR_WHITE)

        draw_text_centered(draw, CHANNEL_TAGLINE, 820, 26, COLOR_GREY)
        frames.append(img)
    return frames

# ============================================================
#  VIDEO ASSEMBLY
# ============================================================

def save_frames(frames, folder):
    os.makedirs(folder, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(f"{folder}/frame_{i:05d}.png")

def render_video(gfx, audio_path, output_path):
    import logging
    log = logging.getLogger("video_renderer")
    load_fonts()
    os.makedirs("output/frames", exist_ok=True)

    log.info("Rendering video frames...")

    # Build all frame segments
    all_frames = []
    all_frames += render_hook_frames       (gfx, int(FPS * 8))   # 0-8s
    all_frames += render_controversy_frames(gfx, [], int(FPS * 17)) # 8-25s
    all_frames += render_goals_frames      (gfx, int(FPS * 17)) # 25-42s
    all_frames += render_stats_frames      (gfx, int(FPS * 8))  # 42-50s
    all_frames += render_motm_frames       (gfx, int(FPS * 6))  # 50-56s
    all_frames += render_cta_frames        (gfx, int(FPS * 2))  # 56-58s

    log.info(f"Generated {len(all_frames)} frames")

    # Save frames to disk
    frame_dir = f"output/frames_{int(os.path.getmtime('output')  if os.path.exists('output') else 0)}"
    save_frames(all_frames, frame_dir)

    # Use FFmpeg to assemble video + audio
    frame_pattern = f"{frame_dir}/frame_%05d.png"
    tmp_video     = output_path.replace(".mp4", "_noaudio.mp4")

    # Step 1: frames → video
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", frame_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "23",
        tmp_video
    ], check=True, capture_output=True)

    # Step 2: add audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i", tmp_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ], check=True, capture_output=True)

    # Cleanup
    os.remove(tmp_video)
    for f in os.listdir(frame_dir):
        os.remove(os.path.join(frame_dir, f))
    os.rmdir(frame_dir)

    log.info(f"Video rendered: {output_path} ({os.path.getsize(output_path)//1024}KB)")
    return output_path
