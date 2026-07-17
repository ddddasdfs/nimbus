"""The emote catalog is built from the local game hash list, so parsing must be
tolerant of the several naming shapes Riot uses and must ignore non-emote assets.
"""
import utils.core.emote_catalog as ec

# Real-world shapes taken from hashes.game.txt
SAMPLE = """\
a44cba745a423b00 assets/loadouts/summoneremotes/4293_in_the_distance_glow.accessories_13_16.dds
a21fd6fce984507f assets/loadouts/summoneremotes/4293_in_the_distance_glow.tex
c80cacf9771b1104 assets/loadouts/summoneremotes/4293_in_the_distance_inventory.tex
32c35424ea15318f assets/loadouts/summoneremotes/4293_in_the_distance_selector.tex
75324ef680bbe551 assets/loadouts/summoneremotes/4293_in_the_distance_vfx.tex
85f00892a1d7e892 assets/loadouts/summoneremotes/championemotes/5103_im_a_locke_star_vfx.accessories_16_13.tex
1ddbd83d94803f71 assets/loadouts/summoneremotes/champions/ahri/em_ahri_love_wink_02_vfx.dds
deadbeefdeadbeef assets/loadouts/summoneremotes/champions/ahri/em_ahri_love_wink_02_selector.dds
0000000000000000 assets/loadouts/summoneremotes/events/onlyglow_glow.tex
fded22410acc03fe assets/characters/aatrox/skins/skin33/particles/aatrox_skin33_emote_music_notes.tex
1111111111111111 assets/loadouts/wardskins/ward_something.tex
"""


def _load(tmp_path, monkeypatch, text=SAMPLE):
    hashes = tmp_path / "hashes.game.txt"
    hashes.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ec, "get_tools_dir", lambda: tmp_path)
    return ec.load_game_emotes(force=True)


def test_parses_emotes_and_ignores_non_emote_assets(tmp_path, monkeypatch):
    emotes = _load(tmp_path, monkeypatch)
    # champion particle + ward skin must not appear; glow-only emote has no _vfx
    names = {e.name for e in emotes}
    assert "In The Distance" in names
    assert "Im A Locke Star" in names
    assert "Ahri Love Wink 02" in names
    assert len(emotes) == 3


def test_requires_vfx_variant(tmp_path, monkeypatch):
    emotes = _load(tmp_path, monkeypatch)
    # 'onlyglow' only has a _glow asset -> unusable for an in-game swap
    assert all("onlyglow" not in e.id for e in emotes)
    assert all(e.vfx_path for e in emotes)


def test_groups_variants_and_extracts_riot_number(tmp_path, monkeypatch):
    emotes = _load(tmp_path, monkeypatch)
    itd = next(e for e in emotes if e.name == "In The Distance")
    assert itd.emote_num == 4293
    assert sorted(itd.variants) == ["glow", "inventory", "selector", "vfx"]
    assert itd.vfx_path.endswith("4293_in_the_distance_vfx.tex")
    assert itd.base_path == "assets/loadouts/summoneremotes/4293_in_the_distance"


def test_category_and_em_prefix_handling(tmp_path, monkeypatch):
    emotes = _load(tmp_path, monkeypatch)
    ahri = next(e for e in emotes if "ahri" in e.id)
    assert ahri.category == "champions/ahri"
    assert ahri.emote_num is None
    assert not ahri.name.lower().startswith("em ")  # 'em_' prefix stripped


def test_ids_unique_and_lookup(tmp_path, monkeypatch):
    emotes = _load(tmp_path, monkeypatch)
    ids = [e.id for e in emotes]
    assert len(ids) == len(set(ids))
    assert ec.get_game_emote(ids[0]).id == ids[0]


def test_missing_hash_file_is_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(ec, "get_tools_dir", lambda: tmp_path / "nope")
    assert ec.load_game_emotes(force=True) == []
