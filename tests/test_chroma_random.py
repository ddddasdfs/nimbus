"""pick_random_chroma: random chroma of a skin, chromas only, never raises.

chroma_id_map shape (from lcu/data/skin_scraper.py): {chroma_id: {'skinId': base_id, ...}}
"""
import utils.core.chroma_random as cr

MAP = {
    30011: {"id": 30011, "skinId": 30003, "name": "Ruby"},
    30012: {"id": 30012, "skinId": 30003, "name": "Sapphire"},
    30021: {"id": 30021, "skinId": 30005, "name": "Emerald"},
}


def test_base_with_chromas_returns_one_of_its_chromas():
    for _ in range(20):
        got = cr.pick_random_chroma(30003, MAP)
        assert got in (30011, 30012)


def test_never_returns_the_base():
    assert all(cr.pick_random_chroma(30003, MAP) != 30003 for _ in range(20))


def test_chroma_input_resolves_to_its_base_pool():
    for _ in range(20):
        assert cr.pick_random_chroma(30011, MAP) in (30011, 30012)


def test_base_without_chromas_returns_none():
    assert cr.pick_random_chroma(30000, MAP) is None


def test_empty_or_none_map_returns_none():
    assert cr.pick_random_chroma(30003, {}) is None
    assert cr.pick_random_chroma(30003, None) is None


def test_garbage_input_never_raises():
    assert cr.pick_random_chroma(None, MAP) is None
    assert cr.pick_random_chroma("nope", MAP) is None
    assert cr.pick_random_chroma(30003, {"bad": "data"}) is None
