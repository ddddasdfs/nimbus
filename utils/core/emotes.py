#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom emote mods: read a synced, user-hosted emote catalog and resolve the active
emote's .fantome for injection.

Emotes are account-wide (unlike per-champion skins), so there is a single global
active emote plus an enable flag. The resolved .fantome is layered on top of the
champion skin mod at injection time.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from config import get_config_option, set_config_option
from utils.core.paths import get_user_data_dir

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass
class EmoteEntry:
    """One emote from the repo manifest."""
    id: str
    name: str
    file: str
    preview: Optional[str] = None
    replaces: Optional[str] = None
    sha256: Optional[str] = None


def emotes_dir() -> Path:
    return get_user_data_dir() / "emotes"


def _manifest_path() -> Path:
    return emotes_dir() / "emotes.json"


def _is_safe_relative(rel: str) -> bool:
    """Reject absolute paths, drive letters, and any traversal outside the emotes dir."""
    if not rel or rel.startswith(("/", "\\")) or ":" in rel:
        return False
    base = emotes_dir().resolve()
    try:
        target = (base / rel).resolve()
    except Exception:
        return False
    return target != base and base in target.parents


def load_catalog() -> List[EmoteEntry]:
    """Parse emotes/emotes.json. Malformed or unsafe entries are skipped, never fatal.
    Returns [] when the manifest is missing, corrupt, or of an unknown version."""
    p = _manifest_path()
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if not isinstance(data, dict) or data.get("version") != 1:
        return []

    out: List[EmoteEntry] = []
    for raw in data.get("emotes", []) or []:
        try:
            eid = str(raw["id"])
            name = str(raw["name"])
            file = str(raw["file"])
        except Exception:
            continue
        if not _ID_RE.match(eid) or not _is_safe_relative(file):
            continue

        preview = raw.get("preview")
        if not (isinstance(preview, str) and _is_safe_relative(preview)):
            preview = None
        replaces = raw.get("replaces")
        replaces = replaces if isinstance(replaces, str) else None
        sha = raw.get("sha256")
        sha = sha.lower() if isinstance(sha, str) else None

        out.append(EmoteEntry(eid, name, file, preview, replaces, sha))
    return out


def get_catalog_entry(emote_id: str) -> Optional[EmoteEntry]:
    for e in load_catalog():
        if e.id == emote_id:
            return e
    return None


def _sha256_of(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _truthy(value: str) -> bool:
    return (value or "").strip().lower() not in ("0", "false", "no", "off", "")


def is_emote_enabled() -> bool:
    return _truthy(get_config_option("General", "emote_enabled", "false"))


def set_emote_enabled(enabled: bool) -> None:
    set_config_option("General", "emote_enabled", "true" if enabled else "false")


def get_active_emote() -> Optional[str]:
    value = (get_config_option("General", "emote_active_id", "") or "").strip()
    return value or None


def set_active_emote(emote_id: Optional[str]) -> None:
    set_config_option("General", "emote_active_id", emote_id or "")


def resolve_active_emote_fantome() -> Optional[Path]:
    """Path to the active emote's .fantome, or None.

    Returns a path only when the feature is enabled, an emote is selected, it exists
    in the catalog, its file is present, and (if the manifest declares one) its
    sha256 verifies. Never raises - injection must never break because of emotes.
    """
    try:
        if not is_emote_enabled():
            return None
        emote_id = get_active_emote()
        if not emote_id:
            return None
        entry = get_catalog_entry(emote_id)
        if entry is None:
            return None
        fantome = (emotes_dir() / entry.file).resolve()
        if not fantome.is_file():
            return None
        if entry.sha256 and _sha256_of(fantome) != entry.sha256:
            return None
        return fantome
    except Exception:
        return None
