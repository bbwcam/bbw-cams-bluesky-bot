import os
import sqlite3
import random
import logging
import requests
from datetime import datetime, timedelta
from atproto import Client, client_utils

API_URL = "https://chaturbate.com/api/public/affiliates/onlinerooms/?wm=T2CSW&client_ip=request_ip"

BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_PASS = os.getenv("BLUESKY_PASSWORD")

DB_FILE = "posted_rooms.db"

THREAD_SIZE = 3
MAX_VIEWERS = 100

# ======================
# BBW TAG FILTER
# ======================

BBW_TAGS = [
    "bbw","curvy","thick","chubby","bigass",
    "plussize","voluptuous","bigboobs","bigbooty"
]

# ======================
# LARGE HASHTAG POOL
# ======================

HASHTAG_POOL = [

"BBW","CurvyGirls","ThickGirls","Chubby",
"BBWCam","BBWLive","CurvyCam","ThickCam",
"PlusSize","BigBeautifulWomen",
"BigBooty","BigBoobs",
"LiveCams","Chaturbate",
"CamGirls","NSFW",
"CamModel","AdultTwitter",
"WebcamGirls","CamShow",
"LiveAdult","AdultContent",
"CamStreaming","OnlineModels"

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

    last = datetime.fromisoformat(row[0])

    return datetime.now() - last < timedelta(days=30)

def save_post(username):

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("INSERT INTO posted VALUES (?, ?)",
              (username, datetime.now().isoformat()))

    conn.commit()
    conn.close()

# ======================
# FETCH ROOMS
# ======================

def fetch_rooms():

    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()

    data = r.json()

    if "results" in data:
        rooms = data["results"]
    else:
        rooms = data

    logging.info(f"{len(rooms)} rooms fetched")

    return rooms

# ======================
# FILTER BBW ROOMS
# ======================

def filter_bbw(rooms):

    results = []

    for r in rooms:

        if r.get("gender") != "f":
            continue

        username = r["username"]

        if already_posted(username):
            continue

        tags = [t.lower() for t in r.get("tags", [])]

        if not any(tag in tags for tag in BBW_TAGS):
            continue

        results.append(r)

    results.sort(key=lambda x: int(x.get("num_users",0)), reverse=True)

    return results

# ======================
# BUILD POST
# ======================

def build_post(room):

    username = room["username"]

    subject = room.get("room_subject","")

    if len(subject) > 80:
        subject = subject[:80] + "..."

    url = f"https://chaturbate.com/{username}/?tour=YrCr&campaign=T2CSW"

    builder = client_utils.TextBuilder()

    builder.text(f"🔥 BBW LIVE ({room['num_users']} watching)\n\n")

    builder.text(f"{username} • {room.get('age','?')} • {room.get('country','')}\n\n")

    builder.text(f"{subject}\n\n")

    builder.text("👉 Watch free: ")
    builder.link(url,url)

    builder.text("\n\n")

    tags = random.sample(HASHTAG_POOL,5)

    for i,tag in enumerate(tags):

        if i>0:
            builder.text(" ")

        builder.tag(f"#{tag}",tag)

    return builder

# ======================
# POST THREAD
# ======================

def post_thread(client, rooms):

    parent = None

    for room in rooms:

        builder = build_post(room)

        img = requests.get(room["image_url_360x270"]).content

        post = client.send_image(
            text=builder.build_text(),
            facets=builder.build_facets(),
            image=img,
            image_alt=f"{room['username']} live cam",
            reply_to=parent
        )

        parent = post

        save_post(room["username"])

        logging.info(f"Posted {room['username']}")

# ======================
# RUN BOT
# ======================

def run_bot():

    client = Client()

    client.login(BLUESKY_HANDLE, BLUESKY_PASS)

    logging.info("Logged into Bluesky")

    rooms = fetch_rooms()

    bbw_rooms = filter_bbw(rooms)

    if len(bbw_rooms) < THREAD_SIZE:

        logging.info("Not enough BBW rooms")

        return

    selected = random.sample(bbw_rooms[:MAX_VIEWERS], THREAD_SIZE)

    post_thread(client, selected)

# ======================
# MAIN
# ======================

if __name__ == "__main__":

    init_db()

    run_bot()
