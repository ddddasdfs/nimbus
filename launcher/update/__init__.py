#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update management package

nimbus note: the auto-updater has been removed for security. The download/execute
path (update_downloader, update_installer) and the GitHub release client
(github_client) are gone. UpdateSequence remains only as a no-op stub.
"""

from .update_sequence import UpdateSequence

__all__ = ['UpdateSequence']
