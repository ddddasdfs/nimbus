#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selection state for custom emotes, and resolution to an injectable .fantome.

Emotes are account-wide, so there is a single global choice rather than a per-champion
one. Because you cannot equip an emote you don't own, a choice is a PAIR:

    source  - the emote you want to see (any of Riot's, from the game files)
    target  - an emote you own and equip, whose assets get overwritten

State lives in config.ini [General] (single scalars, no JSON map needed).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from config import get_config_option, set_config_option
from utils.core.emote_catalog import GameEmote, get_emote_by_base_path
from utils.core.logging import get_logger

log = get_logger()


def _truthy(value: str) -> bool:
    return (value or "").strip().lower() not in ("0", "false", "no", "off", "")


def is_emote_enabled() -> bool:
    return _truthy(get_config_option("General", "emote_enabled", "false"))


def set_emote_enabled(enabled: bool) -> None:
    set_config_option("General", "emote_enabled", "true" if enabled else "false")


def get_source_emote() -> Optional[str]:
    """Id of the emote the user wants to see."""
    value = (get_config_option("General", "emote_source_id", "") or "").strip()
    return value or None


def set_source_emote(emote_id: Optional[str]) -> None:
    set_config_option("General", "emote_source_id", emote_id or "")


def get_target_emote() -> Optional[str]:
    """Id of the owned emote whose assets get overwritten."""
    value = (get_config_option("General", "emote_target_id", "") or "").strip()
    return value or None


def set_target_emote(emote_id: Optional[str]) -> None:
    set_config_option("General", "emote_target_id", emote_id or "")


def resolve_emote_pair() -> Optional[Tuple[GameEmote, GameEmote]]:
    """(source, target) iff enabled and both are set and known. Never raises."""
    try:
        if not is_emote_enabled():
            return None
        source_id, target_id = get_source_emote(), get_target_emote()
        if not source_id or not target_id or source_id == target_id:
            return None
        # Selections are stored as asset base paths, so resolution never needs the client.
        source = get_emote_by_base_path(source_id)
        target = get_emote_by_base_path(target_id)
        if source is None or target is None:
            return None
        return source, target
    except Exception:
        return None


def resolve_active_emote_fantome() -> Optional[Path]:
    """The .fantome to layer onto the overlay, or None.

    Returns a path only when the feature is enabled, a source+target are chosen, and
    the emote assets have been harvested. Builds the mod on first use and reuses it
    afterwards. Never raises - injection must never break because of emotes.
    """
    try:
        pair = resolve_emote_pair()
        if pair is None:
            return None
        source, target = pair

        from utils.core.emote_assets import is_harvested
        if not is_harvested():
            log.debug("[EMOTE] Emote assets not harvested yet - skipping emote injection")
            return None

        from utils.core.emote_mod import build_emote_mod
        return build_emote_mod(source, target)
    except Exception:
        return None
