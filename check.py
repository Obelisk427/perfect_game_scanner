#!/usr/bin/env python3
"""Poll a Perfect Game tournament page for the Schedule/Scores link and alert Discord."""

import json
import os
import re
import sys
import urllib.error
import urllib.request

TARGET_EVENT = "149426"  # Virginia Beach, 5/23-24/26
TEST_EVENT = "146167"    # Completed tournament, used for end-to-end test
PAGE_URL = "https://www.perfectgame.org/Events/Default.aspx?event={event}"
SCHEDULE_URL = "https://www.perfectgame.org/Events/TournamentSchedule.aspx?event={event}"
STATE_PATH = "state.json"


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (pg-tournament-alert)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def has_schedule_link(html: str, event: str) -> bool:
    """Return True if the page links to a schedule/bracket page for this event.

    Matches either of:
    - a URL like TournamentSchedule.aspx / TournamentBracket.aspx / *Schedule*.aspx /
      *Bracket*.aspx with ?event=<event>
    - any <a href="...event=<event>..."> whose visible text contains
      "schedule" or "bracket" (case-insensitive)
    """
    ev = re.escape(event)

    url_pattern = re.compile(
        r'href\s*=\s*"[^"]*(?:Schedule|Bracket)[^"]*\.aspx\?[^"]*event=' + ev,
        re.IGNORECASE,
    )
    if url_pattern.search(html):
        return True

    anchor_pattern = re.compile(
        r'<a\b[^>]*href\s*=\s*"[^"]*event=' + ev + r'[^"]*"[^>]*>([^<]+)</a>',
        re.IGNORECASE,
    )
    for match in anchor_pattern.finditer(html):
        text = match.group(1).strip().lower()
        if "schedule" in text or "bracket" in text:
            return True

    return False


def post_discord(webhook: str, content: str) -> None:
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "pg-tournament-alert (github.com/Obelisk427/perfect_game_scanner, 1.0)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Discord webhook returned {resp.status}")


def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def main() -> int:
    test_mode = "--test" in sys.argv
    event = TEST_EVENT if test_mode else TARGET_EVENT
    state_key = "fired_test" if test_mode else "fired"

    webhook = os.environ.get("DISCORD_WEBHOOK")
    if not webhook:
        print("ERROR: DISCORD_WEBHOOK env var not set", file=sys.stderr)
        return 1

    state = load_state()
    if state.get(state_key):
        print(f"Already alerted for event {event}; nothing to do.")
        return 0

    url = PAGE_URL.format(event=event)
    print(f"Checking {url}")
    html = fetch(url)

    if not has_schedule_link(html, event):
        print("Schedule/Scores link not yet present.")
        return 0

    prefix = "[TEST] " if test_mode else ""
    msg = (
        f"{prefix}:baseball: **Perfect Game tournament schedule is posted!**\n"
        f"Event page: {url}\n"
        f"Schedule/Scores: {SCHEDULE_URL.format(event=event)}"
    )
    post_discord(webhook, msg)
    state[state_key] = True
    save_state(state)
    print("Alert sent and state saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
