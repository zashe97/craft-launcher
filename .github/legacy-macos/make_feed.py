#!/usr/bin/env python3
"""Writes the launcher's release feed (the format of crates/core/src/feed.rs) for the forks.

The patched launcher reads this one file instead of asking GitHub's API about every app, which
allows only 60 unauthenticated requests an hour ("GitHub limit hit").
Usage: make_feed.py <owner> <out.json>   (GH_TOKEN in the environment)
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

# App id (as in crates/core/src/catalog.rs) -> repository name.
APPS = {
    "artcraft-launcher": "craft-launcher",
    "photocraft": "photocraft", "vectorcraft": "vectorcraft", "filmcraft": "filmcraft",
    "lightcraft": "lightcraft", "pdfcraft": "pdfcraft", "effectcraft": "effectcraft",
    "designcraft": "designcraft", "wordcraft": "wordcraft", "deckcraft": "deckcraft",
    "gridcraft": "gridcraft", "cadcraft": "cadcraft", "soundcraft": "soundcraft", "figcraft": "figcraft",
}


def latest(owner, repo, token):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/releases/latest",
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:  # no fork, or no release yet
            return None
        raise LookupError(f"HTTP {e.code}") from e


def main():
    owner, out = sys.argv[1], sys.argv[2]
    token = os.environ["GH_TOKEN"]
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    apps = {}
    for app_id, repo in APPS.items():
        try:
            r = latest(owner, repo, token)
        except (LookupError, OSError) as e:
            # Left out of the feed: the launcher asks GitHub about this one app instead.
            print(f"{app_id}: skipped ({e})")
            continue
        release = None
        if r:
            release = {
                "tag": r["tag_name"],
                "name": r.get("name") or r["tag_name"],
                "published_at": r.get("published_at"),
                "html_url": r.get("html_url"),
                "prerelease": bool(r.get("prerelease")),
                "notes_markdown": r.get("body") or "",
                "assets": [
                    {
                        "name": a["name"],
                        "size_bytes": a["size"],
                        "download_url": a["browser_download_url"],
                        "sha256": (a.get("digest") or "").removeprefix("sha256:") or None,
                    }
                    for a in r.get("assets", [])
                ],
            }
        apps[app_id] = {"repo": f"{owner}/{repo}", "latest_release": release, "app_last_fetched": now}
        print(f"{app_id}: {release['tag'] if release else 'no release'}")
    feed = {"release_info": {"apps": apps, "last_fetched": now}, "app_renames": [], "repo_renames": [],
            "important_notices": {"announcements": [], "alerts": []}}
    with open(out, "w") as f:
        json.dump(feed, f, indent=1)


if __name__ == "__main__":
    main()
