#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catalog of League's own summoner emotes, read from the local game files.

Riot's emotes already ship inside the game WADs under
`assets/loadouts/summoneremotes/`, and the bundled `hashes.game.txt` maps every
hashed WAD entry back to its readable path. So the catalog is built entirely from
what's already on disk - no repo, no download, no redistribution.

Each emote has up to four asset variants:
  _vfx        the in-game bubble (what actually renders)
  _selector   the emote wheel image
  _inventory  the collection image
  _glow       glow overlay
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from utils.core.logging import get_logger
from utils.core.paths import get_tools_dir

log = get_logger()

_PREFIX = "assets/loadouts/summoneremotes/"
_VARIANTS = ("vfx", "selector", "inventory", "glow")
_VARIANT_RE = re.compile(r"^(?P<base>.+?)_(?P<variant>vfx|selector|inventory|glow)$", re.I)
_NUM_PREFIX_RE = re.compile(r"^(?P<num>\d+)_(?P<rest>.+)$")

_cache: Optional[List["GameEmote"]] = None


@dataclass
class GameEmote:
    """One of Riot's emotes, as found in the local game files."""
    id: str                      # stable slug, unique within the catalog
    name: str                    # display name
    category: str                # e.g. "champions/ahri", "esports/worlds2018", "tft"
    base_path: str               # full path minus _<variant>.<ext>
    emote_num: Optional[int] = None   # Riot's numeric emote id, when present
    variants: Dict[str, str] = field(default_factory=dict)  # variant -> full asset path

    @property
    def vfx_path(self) -> Optional[str]:
        """The in-game asset - the one that matters for a swap."""
        return self.variants.get("vfx")


def hashes_file() -> Path:
    return get_tools_dir() / "hashes.game.txt"


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def _prettify(text: str) -> str:
    words = [w for w in re.split(r"[\s_-]+", text.strip()) if w]
    return " ".join(w[:1].upper() + w[1:] for w in words)


def _strip_extensions(filename: str) -> str:
    """'4293_in_the_distance_vfx.accessories_13_16.dds' -> '4293_in_the_distance_vfx'"""
    return filename.split(".", 1)[0]


def load_game_emotes(force: bool = False) -> List[GameEmote]:
    """Parse hashes.game.txt into the emote catalog. Cached after the first call.

    Never raises - a missing/unreadable hash file yields an empty catalog.
    """
    global _cache
    if _cache is not None and not force:
        return _cache

    path = hashes_file()
    if not path.is_file():
        log.warning(f"[EMOTE] Game hash list not found: {path}")
        _cache = []
        return _cache

    grouped: Dict[str, GameEmote] = {}
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # format: "<hash> <path>"
                sep = line.find(" ")
                if sep == -1:
                    continue
                asset = line[sep + 1:].strip()
                if not asset.startswith(_PREFIX):
                    continue

                rel = asset[len(_PREFIX):]           # e.g. champions/ahri/ahri_love_wink_02_glow.dds
                folder, _, filename = rel.rpartition("/")
                stem = _strip_extensions(filename)   # ahri_love_wink_02_glow

                m = _VARIANT_RE.match(stem)
                if not m:
                    continue                          # not an emote asset variant
                base, variant = m.group("base"), m.group("variant").lower()

                base_path = f"{_PREFIX}{folder + '/' if folder else ''}{base}"
                emote = grouped.get(base_path)
                if emote is None:
                    num = None
                    label = base
                    nm = _NUM_PREFIX_RE.match(base)
                    if nm:
                        num = int(nm.group("num"))
                        label = nm.group("rest")
                    label = re.sub(r"^em_", "", label, flags=re.I)

                    slug = _slugify(f"{folder}-{base}" if folder else base)
                    emote = GameEmote(
                        id=slug,
                        name=_prettify(label),
                        category=folder or "general",
                        base_path=base_path,
                        emote_num=num,
                    )
                    grouped[base_path] = emote
                # Keep the first path seen per variant (plain .tex/.dds before locale variants)
                emote.variants.setdefault(variant, asset)
    except Exception as exc:  # noqa: BLE001
        log.warning(f"[EMOTE] Failed parsing game hash list: {exc}")
        _cache = []
        return _cache

    # Only emotes that actually render in-game are usable for a swap.
    emotes = [e for e in grouped.values() if e.vfx_path]
    emotes.sort(key=lambda e: (e.category, e.name))
    log.info(f"[EMOTE] Catalog: {len(emotes)} emotes from game files")
    _cache = emotes
    return _cache


def get_game_emote(emote_id: str) -> Optional[GameEmote]:
    for e in load_game_emotes():
        if e.id == emote_id:
            return e
    return None


def base_path_from_icon(icon: str) -> Optional[str]:
    """Map Riot's inventoryIcon to the asset base path used by this catalog.

    Riot's summoner-emotes.json is the authoritative id/name index, and its icon
    path points at the same assets we harvest, e.g.

      /lol-game-data/assets/ASSETS/Loadouts/SummonerEmotes/Flairs/Thumb_Happy_Up_Inventory.png
        -> assets/loadouts/summoneremotes/flairs/thumb_happy_up

    Joining on this is exact, unlike guessing ids out of filenames.
    """
    if not icon or not isinstance(icon, str):
        return None
    lowered = icon.strip().lower()
    marker = "/lol-game-data/assets/"
    if lowered.startswith(marker):
        lowered = lowered[len(marker):]
    lowered = lowered.lstrip("/")
    if not lowered.startswith(_PREFIX):
        return None
    lowered = lowered.split("?", 1)[0]
    stem = lowered.rsplit("/", 1)[-1].split(".", 1)[0]
    m = _VARIANT_RE.match(stem)
    if m:
        stem = m.group("base")
    folder = lowered.rsplit("/", 1)[0]
    return f"{folder}/{stem}"


def get_emote_by_base_path(base_path: str) -> Optional[GameEmote]:
    if not base_path:
        return None
    for e in load_game_emotes():
        if e.base_path == base_path:
            return e
    return None
