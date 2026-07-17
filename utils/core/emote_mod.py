#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a .fantome that makes one emote render as another.

You can't equip an emote you don't own, so a swap works by overwriting the assets of
an emote you DO own (the target) with the assets of the one you want (the source).
The resulting mod is layered onto the overlay alongside the champion skin.

Pipeline (all bundled tools, verified end-to-end):
    cached source _vfx bytes
      -> written at the TARGET's asset path in a temp tree
      -> wad-make            -> Global.wad.client
      -> zip {WAD/, META/}   -> <source>__<target>.fantome

The .fantome layout mirrors the working skin mods: WAD/Global.wad.client + META/info.json.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from utils.core.emote_assets import asset_for
from utils.core.emote_catalog import GameEmote
from utils.core.logging import get_logger
from utils.core.paths import get_tools_dir, get_user_data_dir

log = get_logger()

_WAD_NAME = "Global.wad.client"  # emote assets live here


def mods_cache_dir() -> Path:
    return get_user_data_dir() / "emotes" / "generated"


def mod_path_for(source: GameEmote, target: GameEmote) -> Path:
    return mods_cache_dir() / f"{source.id}__{target.id}.fantome"


def build_emote_mod(source: GameEmote, target: GameEmote, force: bool = False) -> Optional[Path]:
    """Build (or reuse) the .fantome that shows `source` when `target` is used.

    Returns the .fantome path, or None if it couldn't be built. Never raises.
    """
    try:
        if source.id == target.id:
            log.debug("[EMOTE] Source and target are the same emote - nothing to build")
            return None

        out = mod_path_for(source, target)
        if out.is_file() and not force:
            return out  # already generated

        source_vfx = asset_for(source.base_path, "vfx")
        if not source_vfx:
            log.warning(f"[EMOTE] Source asset not cached for {source.id} - harvest required")
            return None
        if not target.vfx_path:
            log.warning(f"[EMOTE] Target {target.id} has no in-game asset to overwrite")
            return None

        wad_make = get_tools_dir() / "wad-make.exe"
        if not wad_make.is_file():
            log.warning("[EMOTE] wad-make.exe missing")
            return None

        tmp_root = Path(tempfile.mkdtemp(prefix="nimbus-emote-mod-"))
        try:
            # 1. source bytes at the TARGET's path
            tree = tmp_root / "tree"
            dest = tree / target.vfx_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_vfx, dest)

            # 2. build the WAD
            built_wad = tmp_root / _WAD_NAME
            result = subprocess.run(
                [str(wad_make), str(tree), str(built_wad)],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode != 0 or not built_wad.is_file():
                log.warning(f"[EMOTE] wad-make failed ({result.returncode}): {result.stderr[:200]}")
                return None

            # 3. package the .fantome
            out.parent.mkdir(parents=True, exist_ok=True)
            info = {
                "Author": "nimbus",
                "Description": f"Shows '{source.name}' in place of '{target.name}'",
                "Name": f"{source.name} over {target.name}",
                "Version": "1.0",
            }
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(built_wad, f"WAD/{_WAD_NAME}")
                z.writestr("META/info.json", json.dumps(info, indent=2))

            log.info(f"[EMOTE] Built emote mod: {out.name} ({out.stat().st_size} bytes)")
            return out
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
    except subprocess.TimeoutExpired:
        log.warning("[EMOTE] wad-make timed out")
        return None
    except Exception as exc:  # noqa: BLE001
        log.warning(f"[EMOTE] Failed building emote mod: {exc}")
        return None


def clear_generated() -> None:
    """Drop generated mods (e.g. after a game patch invalidates cached assets)."""
    shutil.rmtree(mods_cache_dir(), ignore_errors=True)
