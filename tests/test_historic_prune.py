"""prune_missing_custom_mods: drop historic entries whose custom mod file is gone.

Deleting a mod file used to leave its auto-apply pointer in historic.json forever,
so nimbus kept trying to apply a mod that no longer existed.
"""
import json

import utils.core.historic as h


def _setup(tmp_path, monkeypatch, mapping):
    hist = tmp_path / "historic.json"
    hist.write_text(json.dumps(mapping), encoding="utf-8")
    monkeypatch.setattr(h, "_historic_file_path", lambda: hist)
    mods_root = tmp_path / "mods"
    (mods_root / "skins" / "11000").mkdir(parents=True)
    return hist, mods_root


def test_removes_entry_when_mod_file_missing(tmp_path, monkeypatch):
    hist, mods = _setup(tmp_path, monkeypatch, {"11": "path:skins/11000/Gone.fantome"})
    removed = h.prune_missing_custom_mods(mods)
    assert removed == ["11"]
    assert json.loads(hist.read_text(encoding="utf-8")) == {}


def test_keeps_entry_when_mod_file_exists(tmp_path, monkeypatch):
    hist, mods = _setup(tmp_path, monkeypatch, {"11": "path:skins/11000/Here.fantome"})
    (mods / "skins" / "11000" / "Here.fantome").write_bytes(b"x")
    removed = h.prune_missing_custom_mods(mods)
    assert removed == []
    assert json.loads(hist.read_text(encoding="utf-8")) == {"11": "path:skins/11000/Here.fantome"}


def test_keeps_entry_when_mod_is_a_directory(tmp_path, monkeypatch):
    hist, mods = _setup(tmp_path, monkeypatch, {"11": "path:skins/11000/FolderMod"})
    (mods / "skins" / "11000" / "FolderMod").mkdir()
    assert h.prune_missing_custom_mods(mods) == []


def test_never_touches_plain_skin_ids(tmp_path, monkeypatch):
    hist, mods = _setup(tmp_path, monkeypatch, {"30": 30003, "26": 26014})
    assert h.prune_missing_custom_mods(mods) == []
    assert json.loads(hist.read_text(encoding="utf-8")) == {"30": 30003, "26": 26014}


def test_mixed_map_only_drops_dead_paths(tmp_path, monkeypatch):
    hist, mods = _setup(tmp_path, monkeypatch, {
        "30": 30003,
        "11": "path:skins/11000/Gone.fantome",
        "131": "path:skins/11000/Here.fantome",
    })
    (mods / "skins" / "11000" / "Here.fantome").write_bytes(b"x")
    removed = h.prune_missing_custom_mods(mods)
    assert removed == ["11"]
    assert json.loads(hist.read_text(encoding="utf-8")) == {
        "30": 30003,
        "131": "path:skins/11000/Here.fantome",
    }


def test_missing_historic_file_is_noop(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "_historic_file_path", lambda: tmp_path / "nope.json")
    assert h.prune_missing_custom_mods(tmp_path / "mods") == []


def test_never_raises_on_bad_input(tmp_path, monkeypatch):
    hist = tmp_path / "historic.json"
    hist.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(h, "_historic_file_path", lambda: hist)
    assert h.prune_missing_custom_mods(None) == []
