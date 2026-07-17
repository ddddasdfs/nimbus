"""Tests for pinned-favorite activation/back-off in HistoricModeHandler.

The pin rides the historic-injection path but must win over the client's remembered
skin: it activates regardless of which skin is shown first, holds while the user stays
on that baseline skin, and only backs off once the user picks something different.
"""
import types

import utils.core.favorites as fav
import utils.core.historic as hist
from ui.handlers.historic_mode_handler import HistoricModeHandler


def _make_state(champ=30):
    return types.SimpleNamespace(
        locked_champ_id=champ,
        historic_first_detection_done=False,
        historic_mode_active=False,
        historic_skin_id=None,
        pin_mode_active=False,
        pin_baseline_skin_id=None,
        ui_skin_thread=None,
    )


def test_pin_activates_on_non_default_first_skin(monkeypatch):
    monkeypatch.setattr(fav, "get_active_pin", lambda c: 30003)
    state = _make_state()
    h = HistoricModeHandler(state)

    # Client opens on a remembered NON-default skin (30005).
    h.check_and_activate(30005)

    assert state.historic_mode_active is True
    assert state.historic_skin_id == 30003
    assert state.pin_mode_active is True
    assert state.pin_baseline_skin_id == 30005
    assert state.historic_first_detection_done is True


def test_pin_holds_on_baseline_then_backs_off_on_change(monkeypatch):
    monkeypatch.setattr(fav, "get_active_pin", lambda c: 30003)
    state = _make_state()
    h = HistoricModeHandler(state)
    h.check_and_activate(30005)

    # Still on the baseline skin -> pin stays active.
    h.check_and_deactivate(30005, 30005)
    assert state.historic_mode_active is True
    assert state.historic_skin_id == 30003

    # User actively selects a different skin -> pin backs off.
    h.check_and_deactivate(30010, 30010)
    assert state.historic_mode_active is False
    assert state.historic_skin_id is None
    assert state.pin_mode_active is False


def test_pin_applied_at_lock_holds_over_remembered_skin(monkeypatch):
    # Simulates lock-time apply_pin_to_state: active, first-detection done, baseline None.
    monkeypatch.setattr(fav, "get_active_pin", lambda c: 30003)
    state = _make_state()
    assert fav.apply_pin_to_state(state, 30) is True
    h = HistoricModeHandler(state)

    # First detection is the remembered skin; check_and_activate is skipped (done=True),
    # check_and_deactivate captures the baseline and keeps the pin.
    h.check_and_activate(30005)
    h.check_and_deactivate(30005, 30005)
    assert state.historic_mode_active is True
    assert state.historic_skin_id == 30003
    assert state.pin_baseline_skin_id == 30005


def test_historic_still_requires_default_when_no_pin(monkeypatch):
    monkeypatch.setattr(fav, "get_active_pin", lambda c: None)
    monkeypatch.setattr(hist, "load_historic_map", lambda: {"30": 30001})

    # Non-default first skin -> historic does NOT activate.
    state = _make_state()
    HistoricModeHandler(state).check_and_activate(30005)
    assert state.historic_mode_active is False

    # Default first skin -> historic activates (pin_mode stays off).
    state2 = _make_state()
    HistoricModeHandler(state2).check_and_activate(30000)
    assert state2.historic_mode_active is True
    assert state2.historic_skin_id == 30001
    assert state2.pin_mode_active is False


def test_apply_pin_to_state_no_pin_returns_false(monkeypatch):
    monkeypatch.setattr(fav, "get_active_pin", lambda c: None)
    state = _make_state()
    assert fav.apply_pin_to_state(state, 30) is False
    assert state.historic_mode_active is False
