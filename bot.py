import os
import requests
import time
from atproto import Client, models
from datetime import datetime

# === CONFIG ===
BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_PASS = os.getenv('BLUESKY_PASSWORD')
API_URL = "https://chaturbate.com/affiliates/api/onlinerooms/?format=json&wm=T2CSW"
MAX_POSTS_PER_RUN = 4

def create_facets(text, watch_link, hashtags):
    """Create official facets for clickable link + hashtags"""
    facets = []
    
    # Link facet ("Watch free")
    link_text = "Watch free"
    link_start_char = text.find(link_text)
    if link_start_char != -1:
        link_start_byte = len(text[:link_start_char].encode('utf-8'))
        link_end_byte = link_start_byte + len(link_text.encode('utf-8'))
        index = models.AppBskyRichtextFacet.ByteSlice(byteStart=link_start_byte, byteEnd=link_end_byte)
        feature = models.AppBskyRichtextFacet.Link(uri=watch_link)
        facet = models.AppBskyRichtextFacet.Main(index=index, features=[feature])
        facets.append(facet)
    
    # Hashtag facets
    for tag in hashtags:
        full_tag = f"#{tag}"
        tag_start_char = text.find(full_tag)
        if tag_start_char != -1:
            tag_start_byte = len(text[:tag_start_char].encode('utf-8'))
            tag_end_byte = tag_start_byte + len(full_tag.encode('utf-8'))
            index = models.AppBskyRichtextFacet.ByteSlice(byteStart=tag_start_byte, byteEnd=tag_end_byte)
            feature = models.AppBskyRichtextFacet.Tag(tag=tag)
            facet = models.AppBskyRichtextFacet.Main(index=index, features=[feature])
            facets.append(facet)
    
    return facets

def main():
    print(f"[{datetime.now()}] 🚀 Starting bot run...")

    try:
        client = Client()
        client.login(BLUESKY_HANDLE, BLUESKY_PASS)
        print("✅ Logged into Bluesky")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    try:
        data = requests.get(API_URL, timeout=15).json()
        print(f"✅ Fetched {len(data)} total online rooms")
    except Exception as e:
        print(f"❌ API fetch failed: {e}")
        return

    # Filter: female + public + has "bbw" tag (case-insensitive)
    filtered = [
        room for room in data
        if (
            room.get('gender') == 'f' and
            room.get('current_show') == 'public' and
            "bbw" in [t.lower() for t in room.get('tags', [])]
        )
    ]
    print(f"✅ {len(filtered)} female public BBW rooms available")

    if not filtered:
        print("No BBW rooms found in this run → skipping posts")
        print(f"[{datetime.now()}] Run complete — 0 posts sent\n")
        return

    # Sort by current viewers (most popular first)
    filtered.sort(key=lambda x: int(x.get('num_users', 0)), reverse=True)

    posted = 0
    for i, room in enumerate(filtered[:MAX_POSTS_PER_RUN]):
        try:
            img_resp = requests.get(room['image_url_360x270'], timeout=10)
            img_bytes = img_resp.content

            subject = (room.get('room_subject', '')[:80] + '...') if len(room.get('room_subject', '')) > 80 else room.get('room_subject', '')

            watch_link = room['chat_room_url_revshare']
            hashtags = ["Chaturbate", "BBW", "Curvy", "LiveCams", "Adult", "nsfw", "realnsfw", "bskynsfw", "nsfwsky"]

            text = f"🔥 LIVE NOW BBW ({room['num_users']} watching)\n\n" \
                   f"{room['username']} • {room['age']} • {room['country'] or '??'}\n" \
                   f"{subject}\n\n👉 Watch free\n\n" \
                   f"{' '.join([f'#{tag}' for tag in hashtags])}"

            facets = create_facets(text, watch_link, hashtags)

            client.send_image(
                text=text,
                image=img_bytes,
                image_alt=f"Live BBW cam of {room['username']}",
                facets=facets
            )

            print(f"✅ Posted #{i+1}: {room['username']} ({room['num_users']} viewers) — LINK + HASHTAGS CLICKABLE")
            posted += 1
            time.sleep(12)

        except Exception as e:
            print(f"⚠️  Failed to post {room.get('username')}: {e}")

    print(f"[{datetime.now()}] ✅ Run complete — {posted} posts sent\n")

if __name__ == "__main__":
    main()
