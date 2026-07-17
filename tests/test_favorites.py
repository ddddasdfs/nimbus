import utils.core.favorites as fav


def _point_to_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(fav, "get_user_data_dir", lambda: tmp_path)


def test_set_get_int(tmp_path, monkeypatch):
    _point_to_tmp(tmp_path, monkeypatch)
    fav.set_favorite(266, 266001)
    assert fav.get_favorite_for_champion(266) == 266001


def test_set_get_custom_path(tmp_path, monkeypatch):
    _point_to_tmp(tmp_path, monkeypatch)
    fav.set_favorite(103, "path:skins/103000/ahri.fantome")
    assert fav.get_favorite_for_champion(103) == "path:skins/103000/ahri.fantome"


def test_clear(tmp_path, monkeypatch):
    _point_to_tmp(tmp_path, monkeypatch)
    fav.set_favorite(266, 266001)
    fav.clear_favorite(266)
    assert fav.get_favorite_for_champion(266) is None


def test_missing_file_returns_empty(tmp_path, monkeypatch):
    _point_to_tmp(tmp_path, monkeypatch)
    assert fav.load_favorites_map() == {}


def test_corrupt_file_returns_empty(tmp_path, monkeypatch):
    _point_to_tmp(tmp_path, monkeypatch)
    (tmp_path / "favorites.json").write_text("{ not json", encoding="utf-8")
    assert fav.load_favorites_map() == {}


def test_get_unknown_champ_is_none(tmp_path, monkeypatch):
    _point_to_tmp(tmp_path, monkeypatch)
    assert fav.get_favorite_for_champion(999) is None


def test_resolver_pin_wins_when_enabled():
    v = fav.resolve_auto_apply_value(266, True, {"266": 266001}, {"266": 266000})
    assert v == 266001


def test_resolver_falls_back_to_historic_when_no_pin():
    v = fav.resolve_auto_apply_value(266, True, {}, {"266": 266000})
    assert v == 266000


def test_resolver_ignores_pin_when_disabled():
    v = fav.resolve_auto_apply_value(266, False, {"266": 266001}, {"266": 266000})
    assert v == 266000


def test_resolver_none_when_nothing():
    assert fav.resolve_auto_apply_value(266, True, {}, {}) is None
