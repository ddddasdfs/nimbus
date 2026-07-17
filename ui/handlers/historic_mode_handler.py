#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historic Mode Handler
Handles historic mode activation and deactivation
"""

from typing import Optional
from state import SharedState
from utils.core.logging import get_logger

log = get_logger()


class HistoricModeHandler:
    """Handles historic mode activation and deactivation"""
    
    def __init__(self, state: SharedState):
        """Initialize historic mode handler
        
        Args:
            state: Shared application state
        """
        self.state = state
    
    def check_and_activate(self, skin_id: int) -> None:
        """Activate the auto-apply override on first skin detection after a champion lock.

        A pinned favorite wins over the client's remembered skin, so it activates no
        matter which skin the client opens on. Historic (last-used) keeps its original
        behavior: it only applies when the client opens on the default skin.
        """
        if self.state.historic_first_detection_done or self.state.locked_champ_id is None:
            return

        try:
            from utils.core.historic import load_historic_map, is_custom_mod_path
            from utils.core.favorites import get_active_pin

            champ = int(self.state.locked_champ_id)
            base_skin_id = champ * 1000

            pin_value = get_active_pin(champ)
            if pin_value is not None:
                activate_value = pin_value
                is_pin = True
            elif skin_id == base_skin_id:
                activate_value = load_historic_map().get(str(champ))
                is_pin = False
            else:
                activate_value = None
                is_pin = False

            if activate_value is not None:
                self.state.historic_mode_active = True
                self.state.historic_skin_id = activate_value
                self.state.pin_mode_active = is_pin
                # For a pin, the current skin is the baseline the pin protects against.
                self.state.pin_baseline_skin_id = skin_id if is_pin else None

                kind = "pinned favorite" if is_pin else "historic skin"
                if is_custom_mod_path(activate_value):
                    log.info(f"[HISTORIC] Auto-apply ACTIVATED for champion {champ} ({kind}, custom mod path: {activate_value})")
                else:
                    log.info(f"[HISTORIC] Auto-apply ACTIVATED for champion {champ} ({kind} ID: {activate_value})")

                try:
                    if self.state and hasattr(self.state, 'ui_skin_thread') and self.state.ui_skin_thread:
                        self.state.ui_skin_thread._broadcast_historic_state()
                        log.debug("[HISTORIC] Broadcasted state to JavaScript")
                except Exception as e:
                    log.debug(f"[UI] Failed to broadcast historic state on activation: {e}")
            else:
                log.debug(f"[HISTORIC] No auto-apply entry for champion {champ} (skin_id={skin_id}, base={base_skin_id})")
        except Exception as e:
            log.debug(f"[HISTORIC] Failed to check auto-apply entry: {e}")

        # Mark first detection as done AFTER processing
        self.state.historic_first_detection_done = True
    
    def check_and_deactivate(self, skin_id: int, new_base_skin_id: Optional[int]) -> None:
        """Back off the auto-apply override when the user picks a different skin."""
        if not self.state.historic_mode_active or self.state.locked_champ_id is None:
            return

        base_skin_id = self.state.locked_champ_id * 1000

        # Pinned-favorite mode: the pin wins over the client's remembered skin, so we do
        # NOT back off just because the shown skin isn't the default. The skin present at
        # lock is the baseline; the pin holds while the user stays on it and only backs
        # off once the user actively selects a different skin.
        if getattr(self.state, 'pin_mode_active', False):
            if self.state.pin_baseline_skin_id is None:
                self.state.pin_baseline_skin_id = skin_id
                return
            if skin_id == self.state.pin_baseline_skin_id:
                return
            self.state.historic_mode_active = False
            self.state.historic_skin_id = None
            self.state.pin_mode_active = False
            self.state.pin_baseline_skin_id = None
            log.info(f"[FAVORITE] Pinned favorite backed off - user selected a different skin ({skin_id})")
            try:
                if self.state and hasattr(self.state, 'ui_skin_thread') and self.state.ui_skin_thread:
                    self.state.ui_skin_thread._broadcast_historic_state()
            except Exception as e:
                log.debug(f"[UI] Failed to broadcast historic state on pin back-off: {e}")
            return

        # Historic (last-used) mode: back off as soon as we leave the default skin.
        if new_base_skin_id != base_skin_id:
            self.state.historic_mode_active = False
            self.state.historic_skin_id = None
            log.info(f"[HISTORIC] Historic mode DEACTIVATED - skin changed from default to {skin_id} (base: {new_base_skin_id})")

            # Broadcast state to JavaScript
            try:
                if self.state and hasattr(self.state, 'ui_skin_thread') and self.state.ui_skin_thread:
                    self.state.ui_skin_thread._broadcast_historic_state()
            except Exception as e:
                log.debug(f"[UI] Failed to broadcast historic state on deactivation: {e}")

