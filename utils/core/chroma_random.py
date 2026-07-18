#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random chroma roll for the chroma-dice feature.

Given a skin (or chroma) id, pick a random chroma of that skin from the scraper's
chroma_id_map. Chromas only - the base id is never returned. Never raises: injection
falls back to the plain skin on any failure.
"""
from __future__ import annotations

import random
from typing import Optional

from utils.core.utilities import get_base_skin_id_for_chroma, is_chroma_id


def pick_random_chroma(skin_or_chroma_id, chroma_id_map: Optional[dict]) -> Optional[int]:
    """Random chroma id for the given skin, or None (no chromas / no map / bad input)."""
    try:
        if not chroma_id_map:
            return None
        skin_id = int(skin_or_chroma_id)

        # Resolve a chroma input to its base skin first.
        if is_chroma_id(skin_id, chroma_id_map):
            base = get_base_skin_id_for_chroma(skin_id, chroma_id_map)
            if base is None:
                return None
            skin_id = base

        pool = [
            cid for cid, info in chroma_id_map.items()
            if isinstance(info, dict) and info.get("skinId") == skin_id and cid != skin_id
        ]
        if not pool:
            return None
        return random.choice(pool)
    except Exception:
        return None
