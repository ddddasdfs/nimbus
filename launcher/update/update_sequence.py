"""
Update Sequence — DISABLED in nimbus.

Upstream nimbus's auto-updater downloaded the latest GitHub release ZIP and
executed it with NO signature or hash verification, with no user consent, while
the application was running as administrator. A compromise of the upstream
GitHub account (or a malicious release) would therefore have meant silent,
admin-level arbitrary code execution on every user's machine at next launch.

nimbus removes that download-and-execute path entirely. This module is kept only
so existing imports keep resolving; `perform_update` performs no network access
and never downloads or runs anything. Update nimbus by re-downloading a build
from a source you trust and verifying it yourself.
"""

from __future__ import annotations

from typing import Callable, Optional

from utils.core.logging import get_logger

log = get_logger()


class UpdateSequence:
    """No-op update sequence. Auto-update was removed in nimbus for security."""

    def perform_update(
        self,
        status_callback: Callable[[str], None],
        progress_callback: Callable[[int], None],
        bytes_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        dev_mode: bool = False,
    ) -> bool:
        """Do nothing. Auto-update is intentionally disabled in nimbus."""
        log.info("Auto-update is disabled in nimbus; skipping update check.")
        try:
            status_callback("Auto-update disabled")
        except Exception:
            pass
        return False
