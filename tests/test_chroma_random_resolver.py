"""Resolver post-processing: armed chroma dice rerolls the final injection name.

Covers all three id-based branches (historic/pin, random mode, hovered) and the
must-not-touch cases (disarmed, no chromas, custom-mod pin, roll failure).
"""
from types import SimpleNamespace

import utils.core.chroma_random as cr
from threads.utilities.skin_name_resolver import SkinNameResolver

MAP = {
    30011: {"id": 30011, "skinId": 30003},
    30012: {"id": 30012, "skinId": 30003},
}


def _resolver(state_kwargs, chroma_map=MAP):
    state = SimpleNamespace(
        historic_mode_active=False, historic_skin_id=None,
        random_mode_active=False, random_skin_name=None, random_skin_id=None,
        last_hovered_skin_id=None, locked_champ_id=30, hovered_champ_id=None,
        chroma_random_armed=False, last_hovered_skin_key=None, last_hovered_skin_slug=None,
    )
    for k, v in state_kwargs.items():
        setattr(state, k, v)
    cache = SimpleNamespace(chroma_id_map=chroma_map)
    scraper = SimpleNamespace(cache=cache)
    return SkinNameResolver(state, scraper)


def test_armed_hovered_base_becomes_chroma():
    r = _resolver({"last_hovered_skin_id": 30003, "chroma_random_armed": True})
    assert r.resolve_injection_name() in ("chroma_30011", "chroma_30012")


def test_disarmed_unchanged():
    r = _resolver({"last_hovered_skin_id": 30003})
    assert r.resolve_injection_name() == "skin_30003"


def test_armed_no_chromas_unchanged():
    r = _resolver({"last_hovered_skin_id": 30000, "chroma_random_armed": True})
    assert r.resolve_injection_name() == "skin_30000"


def test_armed_pin_becomes_chroma():
    r = _resolver({"historic_mode_active": True, "historic_skin_id": 30003,
                   "chroma_random_armed": True})
    assert r.resolve_injection_name() in ("chroma_30011", "chroma_30012")


def test_armed_custom_mod_pin_untouched():
    r = _resolver({"historic_mode_active": True,
                   "historic_skin_id": "path:skins/30003/mod.fantome",
                   "chroma_random_armed": True})
    # custom-mod branch returns skin_<base> extracted from the path - must not reroll
    assert r.resolve_injection_name() == "skin_30003"


def test_armed_random_mode_rerolls_within_base():
    r = _resolver({"random_mode_active": True, "random_skin_name": "X",
                   "random_skin_id": 30003, "chroma_random_armed": True})
    assert r.resolve_injection_name() in ("chroma_30011", "chroma_30012")


def test_roll_failure_falls_back(monkeypatch):
    def boom(*a):
        raise RuntimeError("roll exploded")
    monkeypatch.setattr(cr, "pick_random_chroma", boom)
    r = _resolver({"last_hovered_skin_id": 30003, "chroma_random_armed": True})
    assert r.resolve_injection_name() == "skin_30003"
