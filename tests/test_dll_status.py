"""_dll_status + _check_dll_hash: the pure DLL-gate decision (no dialogs)."""
import hashlib

import main as m


def _write(path, data: bytes):
    path.write_bytes(data)
    return path


def test_missing_when_no_file(tmp_path):
    assert m._dll_status(tmp_path) == "missing"


def test_ok_when_present_and_hash_matches(tmp_path, monkeypatch):
    dll = _write(tmp_path / "cslol-dll.dll", b"good-bytes")
    good = hashlib.sha256(b"good-bytes").hexdigest()
    monkeypatch.setattr(m, "_VALID_DLL_HASHES", {good})
    assert m._dll_status(tmp_path) == "ok"


def test_invalid_when_present_but_hash_differs(tmp_path, monkeypatch):
    _write(tmp_path / "cslol-dll.dll", b"tampered")
    monkeypatch.setattr(m, "_VALID_DLL_HASHES", {"0" * 64})
    assert m._dll_status(tmp_path) == "invalid"


def test_check_dll_hash_true_for_known_hash(tmp_path, monkeypatch):
    dll = _write(tmp_path / "cslol-dll.dll", b"abc123")
    good = hashlib.sha256(b"abc123").hexdigest()
    monkeypatch.setattr(m, "_VALID_DLL_HASHES", {good})
    assert m._check_dll_hash(dll) is True


def test_check_dll_hash_false_for_unknown(tmp_path, monkeypatch):
    dll = _write(tmp_path / "cslol-dll.dll", b"xyz")
    monkeypatch.setattr(m, "_VALID_DLL_HASHES", {"0" * 64})
    assert m._check_dll_hash(dll) is False
