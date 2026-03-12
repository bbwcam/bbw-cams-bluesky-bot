# BBW Cams Bluesky Bot

Automated Chaturbate → Bluesky poster. Posts one live female public show per run from your chosen niches (BBW first by default).

## Features
- Posts image + text + direct Chaturbate link
- Rotates niches (BBW, MILF, Asian, Latina, Ebony, Couple)
- 30-day cooldown per room (works on a server; resets on GitHub Actions)
- Runs on GitHub Actions cron (free)

## Setup

1. **Bluesky App Password** (IMPORTANT!)
   - Go to https://bsky.app/settings/app-passwords
   - Create a new one (never use your main password)

2. **GitHub Secrets**
   - Repo → Settings → Secrets and variables → Actions
   - Add two secrets:
     - `BLUESKY_HANDLE` → yourhandle.bsky.social
     - `BLUESKY_PASSWORD` → the app password

3. **Enable the workflow**
   - The `.github/workflows/bluesky-bot.yml` is already set to run every hour.

## Local / Server run (for full 30-day cooldown)
```bash
pip install atproto requests
export BLUESKY_HANDLE=...
export BLUESKY_PASSWORD=...
python bot.py
