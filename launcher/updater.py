"""Launcher auto-update logic for 2SDAY — DISABLED in 2SDAY.

Upstream 2SDAY downloaded the latest release ZIP from GitHub and executed it with
no signature/hash verification while running as administrator. 2SDAY removes that
path. `auto_update` is kept as a no-op for backward compatibility and never
performs any network access or executes anything.
"""

from __future__ import annotations

from typing import Callable, Optional

from utils.core.logging import get_logger

log = get_logger()


def auto_update(
    status_callback: Callable[[str], None],
    progress_callback: Callable[[int], None],
    bytes_callback: Optional[Callable[[int, Optional[int]], None]] = None,
) -> bool:
    """No-op. Auto-update was removed from 2SDAY for security.

    Always returns False (no update installed).
    """
    log.info("auto_update() called but auto-update is disabled in 2SDAY; doing nothing.")
    try:
        status_callback("Auto-update disabled")
    except Exception:
        pass
    return False
