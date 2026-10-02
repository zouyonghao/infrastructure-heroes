#!/usr/bin/env python3
"""
Localize remote images referenced by the site.

- Maintainer avatars without an explicit `avatar` are downloaded from GitHub
  (honouring `avatar_style = "initials"`, which opts out) and stored under
  static/images/maintainers/<slug>.webp at 240 px.
- Existing locally hosted maintainer photos are re-encoded to the same size.
- Project logos stored on remote hosts are downloaded to
  static/images/logos/<slug>.<ext> (SVG kept verbatim, rasters resized and
  converted to WebP).

Self-hosting removes third-party requests (availability, privacy, latency) and
lets the images be pre-sized for their display contexts.

Usage:
  python scripts/localize-images.py                  # dry run (default)
  python scripts/localize-images.py --apply          # write files + front matter
  python scripts/localize-images.py --apply --only avatars
  python scripts/localize-images.py --apply --only logos
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTENT = REPO_ROOT / "content"
STATIC = REPO_ROOT / "static"

AVATAR_DIR = STATIC / "images" / "maintainers"
LOGO_DIR = STATIC / "images" / "logos"
AVATAR_SIZE = 240
LOGO_SIZE = 192
USER_AGENT = "InfrastructureHeroesBot/1.0 (+https://infrastructure-heroes.org)"


def fetch(url: str, attempts: int = 3) -> Tuple[bytes, str]:
    """Download *url*, retrying transient failures. Returns (bytes, content_type)."""
    last_error: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), response.headers.get_content_type()
        except Exception as error:  # noqa: BLE001 - retry any transport error
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"download failed for {url}: {last_error}")


def looks_like_svg(payload: bytes) -> bool:
    head = payload[:4096].decode("utf-8", errors="ignore").lower()
    return "<svg" in head


def is_raster(content_type: str, url: str) -> bool:
    if content_type and content_type.startswith("image/"):
        return "svg" not in content_type
    extension = url.split("?")[0].rsplit(".", 1)[-1].lower()
    return extension in {"png", "jpg", "jpeg", "gif", "webp", "bmp"}


def save_raster(payload: bytes, destination: Path, size: int, quality: int = 88) -> None:
    from PIL import Image  # imported lazily so --help works without Pillow

    image = Image.open(io.BytesIO(payload))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "A" in image.getbands() or image.mode == "P" else "RGB")
    image.thumbnail((size, size), Image.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, "WEBP", quality=quality, method=6)


def set_frontmatter_value(text: str, field: str, value: str) -> str:
    """Replace the top-level `field = ...` line inside the TOML front matter."""
    parts = text.split("+++")
    if len(parts) < 3:
        raise ValueError("file does not contain TOML front matter")
    frontmatter = parts[1]
    pattern = re.compile(rf"^({re.escape(field)}\s*=\s*).*$", re.M)
    if pattern.search(frontmatter):
        frontmatter = pattern.sub(lambda m: f'{m.group(1)}"{value}"', frontmatter, count=1)
    else:
        anchor = re.search(r"^role\s*=.*$", frontmatter, re.M) or re.search(
            r"^title\s*=.*$", frontmatter, re.M
        )
        if not anchor:
            raise ValueError(f"no insertion point for {field}")
        insertion = f'{field} = "{value}"\n'
        frontmatter = frontmatter[: anchor.end()] + "\n" + insertion + frontmatter[anchor.end():]
    result = "+++".join(parts[:1] + [frontmatter] + parts[2:])
    tomllib.loads(frontmatter)
    return result


def process_avatar(path: Path, apply: bool) -> str:
    parts = path.read_text(encoding="utf-8").split("+++")
    data = tomllib.loads(parts[1])
    slug = path.stem
    avatar = data.get("avatar", "")
    target = AVATAR_DIR / f"{slug}.webp"
    local_url = f"/images/maintainers/{slug}.webp"

    if avatar.startswith("/images/"):
        source = REPO_ROOT / "static" / avatar.lstrip("/")
        if source.suffix == ".webp" and source.exists():
            return f"skip {slug}: already local"
        if not source.exists():
            return f"warn {slug}: local avatar missing ({avatar}), skipping"
        try:
            payload, content_type = source.read_bytes(), "image/jpeg"
            if apply:
                save_raster(payload, target, AVATAR_SIZE)
                source.unlink()
                path.write_text(set_frontmatter_value(path.read_text(encoding="utf-8"), "avatar", local_url), encoding="utf-8")
            return f"{'saved' if apply else 'would convert'} {slug}: {avatar} -> {local_url}"
        except Exception as error:  # noqa: BLE001
            return f"warn {slug}: cannot convert {avatar}: {error}"

    if avatar:
        return f"skip {slug}: keeps explicit avatar {avatar}"

    if (data.get("avatar_style") or "") == "initials":
        return f"skip {slug}: initials style"

    github = (data.get("links") or {}).get("github")
    if not github:
        return f"skip {slug}: no source"

    url = f"https://avatars.githubusercontent.com/{github}?s={AVATAR_SIZE * 2}"
    try:
        payload, _ = fetch(url)
        if apply:
            save_raster(payload, target, AVATAR_SIZE, quality=86)
            path.write_text(set_frontmatter_value(path.read_text(encoding="utf-8"), "avatar", local_url), encoding="utf-8")
        return f"{'saved' if apply else 'would save'} {slug}: github:{github} -> {local_url}"
    except Exception as error:  # noqa: BLE001
        return f"warn {slug}: {error}"


def process_logo(path: Path, apply: bool) -> str:
    parts = path.read_text(encoding="utf-8").split("+++")
    data = tomllib.loads(parts[1])
    slug = path.stem
    logo = data.get("logo", "")
    if not logo.startswith("http"):
        return f"skip {slug}: already local" if logo else f"skip {slug}: no logo"

    try:
        payload, content_type = fetch(logo)
    except Exception as error:  # noqa: BLE001
        return f"warn {slug}: {error}"

    if "svg" in content_type or looks_like_svg(payload):
        if not looks_like_svg(payload):
            return f"warn {slug}: content-type svg but body is not SVG"
        target = LOGO_DIR / f"{slug}.svg"
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            path.write_text(set_frontmatter_value(path.read_text(encoding="utf-8"), "logo", f"/images/logos/{target.name}"), encoding="utf-8")
        return f"{'saved' if apply else 'would save'} {slug}: {logo} -> /images/logos/{target.name}"

    if not is_raster(content_type, logo):
        return f"warn {slug}: unsupported content-type {content_type} for {logo}"

    target = LOGO_DIR / f"{slug}.webp"
    if apply:
        try:
            save_raster(payload, target, LOGO_SIZE, quality=90)
        except Exception as error:  # noqa: BLE001
            return f"warn {slug}: cannot convert {logo}: {error}"
        path.write_text(set_frontmatter_value(path.read_text(encoding="utf-8"), "logo", f"/images/logos/{target.name}"), encoding="utf-8")
    return f"{'saved' if apply else 'would save'} {slug}: {logo} -> /images/logos/{target.name}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write files and update front matter (default: dry run)")
    parser.add_argument("--only", choices=["avatars", "logos"], help="limit to one kind of image")
    args = parser.parse_args()

    if not args.apply:
        print("DRY RUN — pass --apply to download and rewrite front matter\n")

    failures = 0
    if args.only in (None, "avatars"):
        print("== Maintainer avatars ==")
        for path in sorted((CONTENT / "maintainers").glob("*.md")):
            if path.name == "_index.md":
                continue
            message = process_avatar(path, args.apply)
            print("  " + message)
            if message.startswith("warn"):
                failures += 1
            time.sleep(0.15 if args.apply else 0)

    if args.only in (None, "logos"):
        print("== Project logos ==")
        for path in sorted((CONTENT / "projects").glob("*.md")):
            if path.name == "_index.md":
                continue
            message = process_logo(path, args.apply)
            print("  " + message)
            if message.startswith("warn"):
                failures += 1
            time.sleep(0.15 if args.apply else 0)

    print(f"\nDone. Warnings: {failures}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
