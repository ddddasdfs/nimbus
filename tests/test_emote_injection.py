"""The injector layers the active emote mod on top of the champion skin.

Critical invariant: emote injection is best-effort - any failure must leave the skin
mod list untouched so skin injection is never broken by emotes.
"""
from types import SimpleNamespace

import utils.core.emotes as em
from injection.core.injector import SkinInjector


def _injector(tmp_path):
    return SkinInjector(None, tmp_path / "mods", tmp_path / "zips", tmp_path / "game")


def test_appends_emote_when_resolved(tmp_path, monkeypatch):
    inj = _injector(tmp_path)
    monkeypatch.setattr(em, "resolve_active_emote_fantome", lambda: tmp_path / "poro.fantome")
    monkeypatch.setattr(inj, "_extract_zip_to_mod", lambda p: SimpleNamespace(name="poro"))

    names = ["30003"]
    inj._append_emote_mods(names)
    assert names == ["30003", "poro"]


def test_no_append_when_unresolved(tmp_path, monkeypatch):
    inj = _injector(tmp_path)
    monkeypatch.setattr(em, "resolve_active_emote_fantome", lambda: None)

    names = ["30003"]
    inj._append_emote_mods(names)
    assert names == ["30003"]


def test_extract_failure_leaves_skin_untouched(tmp_path, monkeypatch):
    inj = _injector(tmp_path)
    monkeypatch.setattr(em, "resolve_active_emote_fantome", lambda: tmp_path / "poro.fantome")

    def boom(_p):
        raise RuntimeError("extract failed")

    monkeypatch.setattr(inj, "_extract_zip_to_mod", boom)

    names = ["30003"]
    inj._append_emote_mods(names)  # must not raise
    assert names == ["30003"]


def test_resolver_failure_leaves_skin_untouched(tmp_path, monkeypatch):
    inj = _injector(tmp_path)

    def boom():
        raise RuntimeError("resolver exploded")

    monkeypatch.setattr(em, "resolve_active_emote_fantome", boom)

    names = ["30003"]
    inj._append_emote_mods(names)  # must not raise
    assert names == ["30003"]
