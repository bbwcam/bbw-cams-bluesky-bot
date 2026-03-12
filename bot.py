import os
import sqlite3
import random
import logging
import requests
from datetime import datetime, timedelta
from atproto import Client, client_utils

# ======================
# CONFIG
# ======================

API_URL = "https://chaturbate.com/api/public/affiliates/onlinerooms/?wm=T2CSW&client_ip=request_ip"

BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_PASS = os.getenv("BLUESKY_PASSWORD")

DB_FILE = "posted_rooms.db"
MAX_VIEWERS_CACHE = 30

NICHES = {
    "bbw": ["bbw"]
}

HASHTAGS = [
    "LiveCams",
    "Chaturbate",
    "NSFW",
    "CamGirls"
]

logging.basicConfig(level=logging.INFO)

# ======================
# DATABASE
# ======================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posted (
            username TEXT,
            posted_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def already_posted(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT posted_at FROM posted WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    last_post = datetime.fromisoformat(row[0])
    return datetime.now() - last_post < timedelta(days=30)

def save_post(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO posted VALUES (?, ?)", (username, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ======================
# FETCH ROOMS
# ======================

def fetch_rooms():
    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()
    return r.json()["results"]

# ======================
# FILTER ROOMS
# ======================

def filter_niche(rooms, niche):

    tags = NICHES[niche]
    results = []

    for r in rooms:

        if r.get("gender") != "f":
            continue

        room_tags = [t.lower() for t in r.get("tags", [])]

        if not any(t in room_tags for t in tags):
            continue

        if already_posted(r["username"]):
            continue

        results.append(r)

    results.sort(key=lambda x: int(x.get("num_users", 0)), reverse=True)

    return results

# ======================
# BUILD POST
# ======================

def build_rich_text(room):

    subject = room.get("room_subject", "")

    if len(subject) > 80:
        subject = subject[:80] + "..."

    username = room["username"]

    # Affiliate tracking link
    url = f"https://chaturbate.com/{username}/?tour=YrCr&campaign=T2CSW"

    builder = client_utils.TextBuilder()

    builder.text(f"🔥 LIVE NOW ({room['num_users']} watching)\n\n")

    builder.text(f"{username} • {room.get('age','?')} • {room.get('country','')}\n\n")

    builder.text(f"{subject}\n\n")

    builder.text("👉 Watch free: ")
    builder.link(url, url)
    builder.text("\n\n")

    # FIXED HASHTAGS
    for i, tag in enumerate(HASHTAGS):

        if i > 0:
            builder.text(" ")

        builder.tag(f"#{tag}", tag)

    return builder

# ======================
# POST
# ======================

def post_room(client, room):

    img = requests.get(room["image_url_360x270"]).content
    text_builder = build_rich_text(room)

    client.send_image(
        text=text_builder.build_text(),
        facets=text_builder.build_facets(),
        image=img,
        image_alt=f"{room['username']} live cam"
    )

    save_post(room["username"])
    logging.info(f"Posted {room['username']} ({room['num_users']} viewers)")

# ======================
# RUN BOT
# ======================

def run_bot():

    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_PASS)

    logging.info("Logged into Bluesky")

    try:

        rooms = fetch_rooms()

        niche = random.choice(list(NICHES.keys()))
        logging.info(f"Scanning niche: {niche}")

        filtered = filter_niche(rooms, niche)

        if filtered:

            room = random.choice(filtered[:MAX_VIEWERS_CACHE])

try:
    post_room(client, room)
    logging.info("POST SUCCESS")
except Exception as e:
    logging.error(f"POST FAILED: {e}")

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    init_db()
    run_bot()
