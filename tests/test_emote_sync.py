"""The emote repo extractor must strip GitHub's top-level folder and refuse to write
outside the target dir (zip-slip)."""
import zipfile

from utils.core.emote_sync import _safe_extract_all


def _make_zip(path, members):
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def test_strips_top_level_folder(tmp_path):
    zip_path = _make_zip(tmp_path / "repo.zip", {
        "nimbus-emotes-main/emotes.json": '{"version": 1, "emotes": []}',
        "nimbus-emotes-main/mods/poro.fantome": "MOD",
    })
    target = tmp_path / "out"
    written = _safe_extract_all(zip_path, target)

    assert written == 2
    assert (target / "emotes.json").is_file()
    assert (target / "mods" / "poro.fantome").read_text() == "MOD"
    # the '<repo>-main' component must not survive
    assert not (target / "nimbus-emotes-main").exists()


def test_rejects_zip_slip_members(tmp_path):
    zip_path = _make_zip(tmp_path / "evil.zip", {
        "repo-main/../../escape.txt": "PWNED",
        "repo-main/ok.txt": "FINE",
    })
    target = tmp_path / "out"
    written = _safe_extract_all(zip_path, target)

    assert written == 1
    assert (target / "ok.txt").is_file()
    assert not (tmp_path.parent / "escape.txt").exists()
    assert not (tmp_path / "escape.txt").exists()
