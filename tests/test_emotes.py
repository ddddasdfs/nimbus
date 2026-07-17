"""Tests for the emote catalog, state, and active-emote resolver.

Emotes are account-wide: one global active emote + an enable flag, resolved to a
.fantome path that the injector layers on top of the champion skin.
"""
import hashlib
import json

import utils.core.emotes as em


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(em, "get_user_data_dir", lambda: tmp_path)
    store = {}
    monkeypatch.setattr(em, "get_config_option", lambda s, o, d="": store.get((s, o), d))
    monkeypatch.setattr(em, "set_config_option", lambda s, o, v: store.__setitem__((s, o), v))
    (tmp_path / "emotes" / "mods").mkdir(parents=True)
    return store


def _manifest(tmp_path, emotes):
    (tmp_path / "emotes" / "emotes.json").write_text(
        json.dumps({"version": 1, "emotes": emotes}), encoding="utf-8"
    )


def _fantome(tmp_path, rel, data=b"MOD"):
    p = tmp_path / "emotes" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_catalog_parses_valid(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _manifest(tmp_path, [{"id": "poro-party", "name": "Poro Party", "file": "mods/poro-party.fantome"}])
    cat = em.load_catalog()
    assert len(cat) == 1
    assert cat[0].id == "poro-party" and cat[0].name == "Poro Party"


def test_catalog_skips_bad_id_and_unsafe_path(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _manifest(tmp_path, [
        {"id": "Bad_ID", "name": "x", "file": "mods/x.fantome"},
        {"id": "esc", "name": "y", "file": "../escape.fantome"},
        {"id": "good", "name": "z", "file": "mods/z.fantome"},
    ])
    assert [e.id for e in em.load_catalog()] == ["good"]


def test_catalog_missing_or_wrong_version_empty(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert em.load_catalog() == []
    (tmp_path / "emotes" / "emotes.json").write_text(
        json.dumps({"version": 2, "emotes": []}), encoding="utf-8"
    )
    assert em.load_catalog() == []


def test_catalog_corrupt_json_empty(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    (tmp_path / "emotes" / "emotes.json").write_text("{ not json", encoding="utf-8")
    assert em.load_catalog() == []


def test_state_roundtrip(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert em.is_emote_enabled() is False
    assert em.get_active_emote() is None
    em.set_emote_enabled(True)
    em.set_active_emote("poro-party")
    assert em.is_emote_enabled() is True
    assert em.get_active_emote() == "poro-party"


def test_resolve_disabled_returns_none(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _manifest(tmp_path, [{"id": "poro", "name": "P", "file": "mods/poro.fantome"}])
    _fantome(tmp_path, "mods/poro.fantome")
    em.set_active_emote("poro")  # enabled still false
    assert em.resolve_active_emote_fantome() is None


def test_resolve_enabled_present(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _manifest(tmp_path, [{"id": "poro", "name": "P", "file": "mods/poro.fantome"}])
    p = _fantome(tmp_path, "mods/poro.fantome")
    em.set_emote_enabled(True)
    em.set_active_emote("poro")
    assert em.resolve_active_emote_fantome() == p.resolve()


def test_resolve_missing_file_none(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _manifest(tmp_path, [{"id": "poro", "name": "P", "file": "mods/poro.fantome"}])
    em.set_emote_enabled(True)
    em.set_active_emote("poro")
    assert em.resolve_active_emote_fantome() is None


def test_resolve_unknown_active_id_none(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _manifest(tmp_path, [{"id": "poro", "name": "P", "file": "mods/poro.fantome"}])
    _fantome(tmp_path, "mods/poro.fantome")
    em.set_emote_enabled(True)
    em.set_active_emote("does-not-exist")
    assert em.resolve_active_emote_fantome() is None


def test_resolve_sha_mismatch_then_match(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    data = b"MOD"
    good = hashlib.sha256(data).hexdigest()
    _manifest(tmp_path, [{"id": "poro", "name": "P", "file": "mods/poro.fantome", "sha256": "deadbeef"}])
    _fantome(tmp_path, "mods/poro.fantome", data)
    em.set_emote_enabled(True)
    em.set_active_emote("poro")
    assert em.resolve_active_emote_fantome() is None
    _manifest(tmp_path, [{"id": "poro", "name": "P", "file": "mods/poro.fantome", "sha256": good}])
    assert em.resolve_active_emote_fantome() is not None
