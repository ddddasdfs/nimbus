"""Emote selection state and resolution.

A choice is a PAIR (source you want -> target you own), because you cannot equip an
emote you don't own. Resolution must be inert unless everything lines up, and must
never raise: skin injection rides the same code path.
"""
import utils.core.emotes as em
from utils.core.emote_catalog import GameEmote


def _state(monkeypatch):
    store = {}
    monkeypatch.setattr(em, "get_config_option", lambda s, o, d="": store.get((s, o), d))
    monkeypatch.setattr(em, "set_config_option", lambda s, o, v: store.__setitem__((s, o), v))
    return store


def _emote(eid, name="X"):
    """Selections are keyed by asset base path, so id == base_path here."""
    return GameEmote(
        id=eid, name=name, category="general",
        base_path=eid,
        variants={"vfx": f"{eid}_vfx.tex"},
    )


def _catalog(monkeypatch, emotes):
    by_path = {e.base_path: e for e in emotes}
    monkeypatch.setattr(em, "get_emote_by_base_path", lambda p: by_path.get(p))


def test_state_defaults_and_roundtrip(monkeypatch):
    _state(monkeypatch)
    assert em.is_emote_enabled() is False
    assert em.get_source_emote() is None and em.get_target_emote() is None

    em.set_emote_enabled(True)
    em.set_source_emote("want-this")
    em.set_target_emote("own-this")
    assert em.is_emote_enabled() is True
    assert em.get_source_emote() == "want-this"
    assert em.get_target_emote() == "own-this"


def test_pair_resolves_when_complete(monkeypatch):
    _state(monkeypatch)
    _catalog(monkeypatch, [_emote("want-this", "Want"), _emote("own-this", "Own")])
    em.set_emote_enabled(True)
    em.set_source_emote("want-this")
    em.set_target_emote("own-this")

    pair = em.resolve_emote_pair()
    assert pair is not None
    source, target = pair
    assert (source.id, target.id) == ("want-this", "own-this")


def test_pair_none_when_disabled(monkeypatch):
    _state(monkeypatch)
    _catalog(monkeypatch, [_emote("a"), _emote("b")])
    em.set_source_emote("a")
    em.set_target_emote("b")  # enabled defaults false
    assert em.resolve_emote_pair() is None


def test_pair_none_when_incomplete_or_identical(monkeypatch):
    _state(monkeypatch)
    _catalog(monkeypatch, [_emote("a"), _emote("b")])
    em.set_emote_enabled(True)

    em.set_source_emote("a")
    assert em.resolve_emote_pair() is None  # no target

    em.set_target_emote("a")
    assert em.resolve_emote_pair() is None  # same emote is a no-op


def test_pair_none_when_id_unknown(monkeypatch):
    _state(monkeypatch)
    _catalog(monkeypatch, [_emote("a")])
    em.set_emote_enabled(True)
    em.set_source_emote("a")
    em.set_target_emote("ghost")  # not in catalog
    assert em.resolve_emote_pair() is None


def test_fantome_none_until_assets_harvested(monkeypatch):
    _state(monkeypatch)
    _catalog(monkeypatch, [_emote("a"), _emote("b")])
    em.set_emote_enabled(True)
    em.set_source_emote("a")
    em.set_target_emote("b")

    import utils.core.emote_assets as assets
    monkeypatch.setattr(assets, "is_harvested", lambda: False)
    assert em.resolve_active_emote_fantome() is None


def test_fantome_built_when_ready(monkeypatch, tmp_path):
    _state(monkeypatch)
    _catalog(monkeypatch, [_emote("a"), _emote("b")])
    em.set_emote_enabled(True)
    em.set_source_emote("a")
    em.set_target_emote("b")

    import utils.core.emote_assets as assets
    import utils.core.emote_mod as mod
    built = tmp_path / "a__b.fantome"
    built.write_bytes(b"FANTOME")
    monkeypatch.setattr(assets, "is_harvested", lambda: True)
    monkeypatch.setattr(mod, "build_emote_mod", lambda s, t: built)

    assert em.resolve_active_emote_fantome() == built


def test_resolution_never_raises(monkeypatch):
    _state(monkeypatch)

    def boom(_p):
        raise RuntimeError("catalog exploded")

    monkeypatch.setattr(em, "get_emote_by_base_path", boom)
    em.set_emote_enabled(True)
    em.set_source_emote("a")
    em.set_target_emote("b")
    assert em.resolve_emote_pair() is None
    assert em.resolve_active_emote_fantome() is None
