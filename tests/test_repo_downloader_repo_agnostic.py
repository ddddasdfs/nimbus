"""RepoDownloader must derive its GitHub API/raw bases from repo_url.

It previously accepted repo_url but ignored it for API/raw calls, which silently
hardcoded every instance to the skin repo. These lock in the fix without changing
the skin defaults.
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
        repo_url="https://github.com/someone/some-repo",
        version_filename=".other_version",
    )
    assert r.api_base == "https://api.github.com/repos/someone/some-repo"
    assert r.raw_base == "https://raw.githubusercontent.com/someone/some-repo/main"
    assert r.version_file.name == ".other_version"


def test_trailing_slash_and_git_suffix_tolerated():
    r = RepoDownloader(target_dir=Path("x"), repo_url="https://github.com/someone/some-repo.git/")
    assert r.api_base == "https://api.github.com/repos/someone/some-repo"
