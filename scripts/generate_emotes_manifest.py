#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate emotes.json for a nimbus emote repo.

Scans <repo>/mods for .fantome/.zip mods, pairs each with a <repo>/previews image if
one exists, computes its sha256, and writes <repo>/emotes.json.

Curated fields ("name", "replaces") from an existing manifest are preserved, so this
is safe to re-run whenever you add mods.

This script is intentionally self-contained (no nimbus imports) so you can copy it
into the emote repo itself if you prefer.

Usage:
    python scripts/generate_emotes_manifest.py <path-to-emote-repo> [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional

MOD_EXTENSIONS = (".fantome", ".zip")
PREVIEW_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")  # must match the app's validation


def slugify(stem: str) -> str:
    s = stem.strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def prettify(stem: str) -> str:
    words = [w for w in re.split(r"[\s_-]+", stem.strip()) if w]
    return " ".join(w[:1].upper() + w[1:] for w in words)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_preview(repo: Path, stem: str) -> Optional[str]:
    for ext in PREVIEW_EXTENSIONS:
        if (repo / "previews" / f"{stem}{ext}").is_file():
            return f"previews/{stem}{ext}"
    return None


def load_existing(repo: Path) -> dict:
    """id -> entry from any existing manifest, so curated fields survive a re-run."""
    manifest = repo / "emotes.json"
    if not manifest.is_file():
        return {}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return {
            e["id"]: e
            for e in data.get("emotes", [])
            if isinstance(e, dict) and "id" in e
        }
    except Exception as exc:  # noqa: BLE001
        print(f"  ! existing emotes.json unreadable ({exc}); regenerating from scratch")
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate emotes.json for a nimbus emote repo")
    ap.add_argument("repo", type=Path, help="Path to the emote repo checkout")
    ap.add_argument("--dry-run", action="store_true", help="Print the manifest without writing")
    args = ap.parse_args()

    repo: Path = args.repo
    mods_dir = repo / "mods"
    if not mods_dir.is_dir():
        print(f"error: {mods_dir} not found - expected a 'mods' folder in the repo", file=sys.stderr)
        return 1

    existing = load_existing(repo)
    mods = sorted(
        p for p in mods_dir.iterdir()
        if p.is_file() and p.suffix.lower() in MOD_EXTENSIONS
    )
    if not mods:
        print(f"warning: no {' / '.join(MOD_EXTENSIONS)} files found in {mods_dir}")

    entries = []
    warnings = []
    for mod in mods:
        stem = mod.stem
        emote_id = slugify(stem)
        if not ID_RE.match(emote_id):
            warnings.append(f"  ! skipped {mod.name}: cannot derive a valid id from this filename")
            continue
        if emote_id != stem:
            warnings.append(
                f"  ! {mod.name}: id '{emote_id}' differs from the filename stem. "
                f"Rename the file to '{emote_id}{mod.suffix}' to follow the convention."
            )

        prev = existing.get(emote_id, {})
        entry = {
            "id": emote_id,
            "name": prev.get("name") or prettify(stem),
            "file": f"mods/{mod.name}",
            "sha256": sha256_of(mod),
        }
        preview = find_preview(repo, stem) or prev.get("preview")
        if preview:
            entry["preview"] = preview
        if prev.get("replaces"):
            entry["replaces"] = prev["replaces"]
        else:
            warnings.append(
                f"  ! {mod.name}: no 'replaces' set - add the base emote it swaps so the "
                f"UI can remind you which emote to equip"
            )
        entries.append(entry)

    text = json.dumps({"version": 1, "emotes": entries}, indent=2, ensure_ascii=False) + "\n"

    for w in warnings:
        print(w)
    print(f"\n{len(entries)} emote(s) indexed.")

    if args.dry_run:
        print("\n--- emotes.json (dry run) ---")
        print(text)
        return 0

    (repo / "emotes.json").write_text(text, encoding="utf-8")
    print(f"Wrote {repo / 'emotes.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
