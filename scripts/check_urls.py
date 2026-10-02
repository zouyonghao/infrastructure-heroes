#!/usr/bin/env python3
"""
Script to check if logo URLs are accessible.

The slug -> URL mapping is loaded from ``scripts/logo_urls.json`` (the same
single source of truth used by ``update_logos.py``).
"""

import json
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
LOGO_URLS_PATH = SCRIPT_DIR / "logo_urls.json"

# Many CDNs (Cloudflare, Wikimedia, GitHub raw, ...) answer 403 to the default
# python-requests User-Agent even though the asset is publicly available, so
# we present a browser-like UA to avoid those false positives.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def load_logo_urls(path: Path = LOGO_URLS_PATH) -> dict:
    """Load the project slug -> logo URL mapping."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_url(url: str) -> bool:
    if not url:
        return False
    try:
        response = requests.get(
            url,
            timeout=10,
            stream=True,
            headers={"User-Agent": USER_AGENT},
        )
        response.close()
        return response.status_code == 200
    except requests.RequestException as exc:
        print(f"  Error checking {url}: {exc}")
        return False


def main():
    logo_urls = load_logo_urls()
    for project, url in logo_urls.items():
        if url and not check_url(url):
            print(f"Broken: {project} -> {url}")
        elif not url:
            print(f"Empty: {project}")

    print("Done checking.")


if __name__ == "__main__":
    main()
