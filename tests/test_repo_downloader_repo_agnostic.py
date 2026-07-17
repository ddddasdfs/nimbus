"""RepoDownloader must derive its GitHub API/raw bases from repo_url so it can serve
repos other than the skin repo (e.g. the emote repo), without changing skin defaults.
"""
from pathlib import Path

from utils.download.repo_downloader import RepoDownloader


def test_defaults_unchanged_for_skins():
    r = RepoDownloader(target_dir=Path("x"))
    assert r.api_base == "https://api.github.com/repos/Alban1911/LeagueSkins"
    assert r.raw_base == "https://raw.githubusercontent.com/Alban1911/LeagueSkins/main"
    assert r.version_file.name == ".skin_version"


def test_derives_bases_from_repo_url():
    r = RepoDownloader(
        target_dir=Path("x"),
        repo_url="https://github.com/me/nimbus-emotes",
        version_filename=".emote_version",
    )
    assert r.api_base == "https://api.github.com/repos/me/nimbus-emotes"
    assert r.raw_base == "https://raw.githubusercontent.com/me/nimbus-emotes/main"
    assert r.version_file.name == ".emote_version"


def test_trailing_slash_and_git_suffix_tolerated():
    r = RepoDownloader(target_dir=Path("x"), repo_url="https://github.com/me/emotes.git/")
    assert r.api_base == "https://api.github.com/repos/me/emotes"
