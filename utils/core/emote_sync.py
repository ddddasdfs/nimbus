#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync the user-hosted emote repo into the local emotes dir.

Reuses the repo-agnostic parts of RepoDownloader (SHA tracking + repo ZIP download),
but extracts generically: the skin extractor is champion/skin-structured and cannot
handle a flat emote repo (emotes.json + mods/ + previews/).

Best-effort throughout - a failed sync leaves any previously synced catalog intact
and never blocks startup.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional

from config import get_config_option
from utils.core.emotes import emotes_dir
from utils.core.logging import get_logger
from utils.download.repo_downloader import RepoDownloader

log = get_logger()

_DEFAULT_EMOTE_REPO = "https://github.com/ddddasdfs/nimbus-emotes"


def emote_repo_url() -> str:
    """Emote repo source. Configurable so the user controls what is trusted."""
    return (
        get_config_option("General", "emote_repo_url", _DEFAULT_EMOTE_REPO)
        or _DEFAULT_EMOTE_REPO
    ).strip()


def is_emote_sync_enabled() -> bool:
    value = get_config_option("General", "emote_sync_enabled", "true") or "true"
    return value.strip().lower() not in ("0", "false", "no", "off")


def _safe_extract_all(zip_path: Path, target: Path) -> int:
    """Extract a GitHub repo ZIP into target, stripping the leading '<repo>-<branch>/'
    component. Members resolving outside target are skipped (zip-slip guard).
    Returns the number of files written."""
    target.mkdir(parents=True, exist_ok=True)
    base = target.resolve()
    written = 0
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            parts = member.filename.split("/", 1)
            rel = parts[1] if len(parts) == 2 else ""
            if not rel:
                continue
            dest = (base / rel).resolve()
            if base not in dest.parents:
                log.warning(f"[EMOTE] Skipped unsafe archive member: {member.filename}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest, "wb") as out:
                out.write(src.read())
            written += 1
    return written


def sync_emotes(progress_callback=None) -> bool:
    """Sync the emote repo. Returns True when up-to-date or successfully updated.
    Never raises."""
    try:
        downloader = RepoDownloader(
            target_dir=emotes_dir(),
            repo_url=emote_repo_url(),
            progress_callback=progress_callback,
            version_filename=".emote_version",
        )

        remote_sha = downloader.fetch_remote_sha()
        manifest = emotes_dir() / "emotes.json"
        if remote_sha and remote_sha == downloader.get_local_sha() and manifest.exists():
            log.info("[EMOTE] Emote repo unchanged")
            return True

        zip_path: Optional[Path] = downloader.download_repo_zip(download_label="emotes")
        if not zip_path:
            log.warning("[EMOTE] Emote repo ZIP download failed - keeping existing catalog")
            return False

        try:
            count = _safe_extract_all(Path(zip_path), emotes_dir())
            log.info(f"[EMOTE] Extracted {count} emote repo files")
        finally:
            try:
                Path(zip_path).unlink(missing_ok=True)
            except Exception:
                pass

        if remote_sha:
            downloader.save_local_sha(remote_sha)
        log.info("[EMOTE] Emote sync complete")
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning(f"[EMOTE] Emote sync error (non-fatal): {exc}")
        return False
