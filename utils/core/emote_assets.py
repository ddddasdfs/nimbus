#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-time harvest of Riot's emote assets out of the game's Global.wad.client.

`wad-extract` can only unpack a whole WAD, so harvesting is expensive (a ~56MB WAD
expands to ~2.8GB). We pay that once: extract to a temp dir, copy out only the
summoneremotes assets we need (`_vfx` for the swap, `_selector` for UI previews),
then delete the rest. Everything after that is instant.

The cache is keyed to the game WAD's size+mtime, so a game patch triggers a re-harvest.
Nothing is downloaded and nothing leaves the machine - these are the user's own files.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from utils.core.logging import get_logger
from utils.core.paths import get_tools_dir, get_user_data_dir

log = get_logger()

# Variants worth keeping: vfx is what renders in-game, selector is the UI thumbnail.
KEEP_VARIANTS = ("_vfx", "_selector")
_SUBPATH = "assets/loadouts/summoneremotes"

ProgressCallback = Callable[[int, str], None]


def cache_dir() -> Path:
    return get_user_data_dir() / "emotes" / "assets"


def _marker_file() -> Path:
    return get_user_data_dir() / "emotes" / ".harvest_version"


def game_wad() -> Optional[Path]:
    """Path to Global.wad.client, which holds the summoner emote assets."""
    try:
        from injection.config.config_manager import ConfigManager
        league = ConfigManager().load_league_path()
        if not league:
            return None
        wad = Path(league) / "DATA" / "FINAL" / "Global.wad.client"
        return wad if wad.is_file() else None
    except Exception as exc:  # noqa: BLE001
        log.debug(f"[EMOTE] Could not resolve game WAD: {exc}")
        return None


def _wad_signature() -> Optional[str]:
    wad = game_wad()
    if not wad:
        return None
    st = wad.stat()
    return f"{st.st_size}-{int(st.st_mtime)}"


def is_harvested() -> bool:
    """True when the cache matches the current game files."""
    try:
        sig = _wad_signature()
        if not sig:
            return False
        marker = _marker_file()
        if not marker.is_file():
            return False
        if marker.read_text(encoding="utf-8").strip() != sig:
            return False  # game patched -> stale
        return any(cache_dir().rglob("*_vfx.*"))
    except Exception:
        return False


def cached_asset(rel_path: str) -> Optional[Path]:
    """Look up a harvested asset by its path relative to summoneremotes/."""
    try:
        p = (cache_dir() / rel_path).resolve()
        base = cache_dir().resolve()
        if base not in p.parents:
            return None  # traversal guard
        return p if p.is_file() else None
    except Exception:
        return None


def asset_for(base_path: str, variant: str = "vfx") -> Optional[Path]:
    """Resolve a GameEmote.base_path (full asset path) + variant to a cached file.

    Extensions vary (.tex/.dds), so match on the stem.
    """
    try:
        prefix = _SUBPATH + "/"
        rel = base_path[len(prefix):] if base_path.startswith(prefix) else base_path
        target_dir = (cache_dir() / rel).parent
        stem = Path(rel).name + f"_{variant}"
        if not target_dir.is_dir():
            return None
        for candidate in target_dir.iterdir():
            if candidate.is_file() and candidate.name.split(".", 1)[0] == stem:
                return candidate
        return None
    except Exception:
        return None


def harvest(progress_callback: Optional[ProgressCallback] = None) -> bool:
    """Extract the game WAD once and cache the emote assets. Returns True on success.

    Slow (~1-2 min) and disk-hungry while running; the temp extraction is always
    removed. Never raises.
    """
    def _progress(pct: int, msg: str) -> None:
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception:
                pass
        log.info(f"[EMOTE] harvest {pct}% - {msg}")

    wad = game_wad()
    if not wad:
        log.warning("[EMOTE] Cannot harvest: Global.wad.client not found (is the game path set?)")
        return False

    extractor = get_tools_dir() / "wad-extract.exe"
    hashes = get_tools_dir() / "hashes.game.txt"
    if not extractor.is_file() or not hashes.is_file():
        log.warning("[EMOTE] Cannot harvest: wad-extract.exe / hashes.game.txt missing")
        return False

    tmp_root = Path(tempfile.mkdtemp(prefix="nimbus-emote-harvest-"))
    try:
        _progress(5, "Extracting game emote assets (one-time, may take a minute)…")
        result = subprocess.run(
            [str(extractor), str(wad), str(tmp_root), str(hashes)],
            capture_output=True, text=True, timeout=900,
        )
        if result.returncode != 0:
            log.warning(f"[EMOTE] wad-extract failed ({result.returncode}): {result.stderr[:200]}")
            return False

        src_root = tmp_root / Path(_SUBPATH)
        if not src_root.is_dir():
            log.warning("[EMOTE] Extraction produced no summoneremotes assets")
            return False

        _progress(70, "Caching emote assets…")
        dest_root = cache_dir()
        if dest_root.exists():
            shutil.rmtree(dest_root, ignore_errors=True)
        dest_root.mkdir(parents=True, exist_ok=True)

        kept = 0
        for src in src_root.rglob("*"):
            if not src.is_file():
                continue
            stem = src.name.split(".", 1)[0]
            if not stem.endswith(KEEP_VARIANTS):
                continue
            rel = src.relative_to(src_root)
            dst = dest_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            kept += 1

        if kept == 0:
            log.warning("[EMOTE] No emote assets matched the keep-list")
            return False

        sig = _wad_signature()
        if sig:
            _marker_file().parent.mkdir(parents=True, exist_ok=True)
            _marker_file().write_text(sig, encoding="utf-8")

        _progress(100, f"Cached {kept} emote assets")
        return True
    except subprocess.TimeoutExpired:
        log.warning("[EMOTE] wad-extract timed out")
        return False
    except Exception as exc:  # noqa: BLE001
        log.warning(f"[EMOTE] Harvest failed: {exc}")
        return False
    finally:
        # Always drop the multi-GB extraction, success or not.
        shutil.rmtree(tmp_root, ignore_errors=True)
