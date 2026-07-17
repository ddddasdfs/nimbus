#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pinned favorite skins: persist and read a per-champion favorite skin/chroma/mod.

File: favorites.json, shape { "<championId>": <skinOrChromaId:int> | "path:<relPath>" }.
Mirrors historic.py's value format so a favorite can be a skin, chroma, or custom mod.
Separate file from historic.json so Historic Mode data is never touched.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Union

from utils.core.paths import get_user_data_dir


def _favorites_file_path() -> Path:
    return get_user_data_dir() / "favorites.json"


def load_favorites_map() -> Dict[str, Union[int, str]]:
    """Load the favorites mapping. Returns empty dict if missing or invalid."""
    try:
        p = _favorites_file_path()
        if not p.exists():
            return {}
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        result: Dict[str, Union[int, str]] = {}
        for k, v in data.items():
            try:
                key = str(int(k))
                if isinstance(v, int):
                    result[key] = int(v)
                elif isinstance(v, str):
                    result[key] = str(v)
            except Exception:
                continue
        return result
    except Exception:
        return {}


def get_favorite_for_champion(champion_id: int) -> Optional[Union[int, str]]:
    """Return the favorite entry for a champion, or None."""
    return load_favorites_map().get(str(int(champion_id)))


def set_favorite(champion_id: int, value: Union[int, str]) -> None:
    """Write/overwrite the favorite for a champion. Best-effort."""
    p = _favorites_file_path()
    m = load_favorites_map()
    m[str(int(champion_id))] = value
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear_favorite(champion_id: int) -> None:
    """Remove the favorite for a champion if present. Best-effort."""
    try:
        p = _favorites_file_path()
        m = load_favorites_map()
        key = str(int(champion_id))
        if key in m:
            m.pop(key, None)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def resolve_auto_apply_value(champion_id: int, favorites_enabled: bool,
                             favorites_map: Dict[str, Union[int, str]],
                             historic_map: Dict[str, Union[int, str]]) -> Optional[Union[int, str]]:
    """Precedence: pinned favorite (if enabled) -> historic (last-used) -> None."""
    key = str(int(champion_id))
    if favorites_enabled:
        v = favorites_map.get(key)
        if v is not None:
            return v
    return historic_map.get(key)
