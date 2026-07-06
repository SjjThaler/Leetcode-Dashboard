#!/usr/bin/env python3
"""Fetch solved-problem stats for each friend from LeetCode's public GraphQL API
and write them to docs/data.json for the dashboard to read.

Uses only the Python standard library, so no `pip install` step is needed.
"""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "usernames.json")
OUTPUT_PATH = os.path.join(ROOT, "docs", "data.json")

GRAPHQL_URL = "https://leetcode.com/graphql"

QUERY = """
query stats($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      realName
      ranking
      userAvatar
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
  recentAcSubmissionList(username: $username, limit: 3) {
    title
    titleSlug
    timestamp
  }
}
"""


def fetch_user(leetcode_username):
    """Return the raw GraphQL `data` object for one user, or raise on failure."""
    payload = json.dumps(
        {"query": QUERY, "variables": {"username": leetcode_username}}
    ).encode("utf-8")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            # LeetCode blocks requests without a browser-like UA / referer.
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Referer": f"https://leetcode.com/u/{leetcode_username}/",
            "Origin": "https://leetcode.com",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))

    if body.get("errors"):
        raise ValueError(body["errors"][0].get("message", "GraphQL error"))

    data = body.get("data") or {}
    if not data.get("matchedUser"):
        raise ValueError("user not found")
    return data


def build_entry(config_user):
    leetcode_username = config_user["leetcode"]
    display_name = config_user.get("name") or leetcode_username

    entry = {
        "leetcode": leetcode_username,
        "name": display_name,
        "avatar": None,
        "ranking": None,
        "total": 0,
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "recent": [],
        "error": None,
    }

    try:
        data = fetch_user(leetcode_username)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
        entry["error"] = str(exc)
        print(f"  ! {leetcode_username}: {exc}")
        return entry

    matched = data["matchedUser"]
    profile = matched.get("profile") or {}
    entry["avatar"] = profile.get("userAvatar")
    entry["ranking"] = profile.get("ranking")

    counts = {
        item["difficulty"]: item["count"]
        for item in matched["submitStatsGlobal"]["acSubmissionNum"]
    }
    entry["total"] = counts.get("All", 0)
    entry["easy"] = counts.get("Easy", 0)
    entry["medium"] = counts.get("Medium", 0)
    entry["hard"] = counts.get("Hard", 0)

    for sub in data.get("recentAcSubmissionList") or []:
        entry["recent"].append(
            {
                "title": sub["title"],
                "titleSlug": sub["titleSlug"],
                "timestamp": int(sub["timestamp"]),
            }
        )

    print(f"  ✓ {leetcode_username}: {entry['total']} solved")
    return entry


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    users = config.get("users", [])
    print(f"Fetching stats for {len(users)} user(s)...")

    entries = []
    for i, config_user in enumerate(users):
        entries.append(build_entry(config_user))
        if i < len(users) - 1:
            time.sleep(1)  # be polite to the endpoint

    # Leaderboard order: most problems solved first.
    entries.sort(key=lambda e: e["total"], reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "users": entries,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
