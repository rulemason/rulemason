"""rulemason key 的测试：只在终端里交互输入，写入新位置并设 600，保留其他设置，不打印 key。"""
from __future__ import annotations

import stat

import pytest

from rulemason import key
from rulemason.judge import judge


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    path = tmp_path / "home/.config/rulemason/env"
    monkeypatch.setattr(judge, "USER_ENV", path)
    monkeypatch.setattr(key.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(key.getpass, "getpass", lambda prompt="": "  sk-test-value  ")
    return path


def test_first_write_sets_permissions(env_file, capsys):
    assert key.run() == 0
    assert env_file.read_text(encoding="utf-8") == "TYPESAFE_API_KEY=sk-test-value\n"
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(env_file.parent.stat().st_mode) == 0o700
    assert "sk-test-value" not in capsys.readouterr().out


def test_replaces_key_and_keeps_other_settings(env_file):
    env_file.parent.mkdir(parents=True)
    env_file.write_text("TYPESAFE_API_KEY=old\nJUDGE_PROVIDER=jev\n", encoding="utf-8")
    env_file.chmod(0o644)
    assert key.run() == 0
    assert env_file.read_text(encoding="utf-8") == "JUDGE_PROVIDER=jev\nTYPESAFE_API_KEY=sk-test-value\n"
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600


def test_non_interactive_refuses(env_file, monkeypatch, capsys):
    monkeypatch.setattr(key.sys.stdin, "isatty", lambda: False)
    assert key.run() == 1
    assert not env_file.exists()
    assert "终端" in capsys.readouterr().out


def test_empty_input_writes_nothing(env_file, monkeypatch):
    monkeypatch.setattr(key.getpass, "getpass", lambda prompt="": "   ")
    assert key.run() == 1
    assert not env_file.exists()


def test_existing_open_directory_is_tightened(env_file):
    env_file.parent.mkdir(parents=True, mode=0o755)
    assert key.run() == 0
    assert stat.S_IMODE(env_file.parent.stat().st_mode) == 0o700


def test_writes_without_posix_permissions(env_file, monkeypatch, capsys):
    monkeypatch.delattr(key.os, "O_NOFOLLOW")
    monkeypatch.delattr(key.os, "fchmod")
    monkeypatch.setattr(key.os, "name", "nt")
    assert key.run() == 0
    assert env_file.read_text(encoding="utf-8") == "TYPESAFE_API_KEY=sk-test-value\n"
    out = capsys.readouterr().out
    assert "在当前用户目录下" in out and "权限 600" not in out and "sk-test-value" not in out


@pytest.mark.parametrize(("typed", "reason"), [("\x16", "Ctrl+Shift+V"), ("sk-ab cd", "含空白"), ("sk-密钥", "非 ASCII")])
def test_invalid_key_is_not_written(env_file, monkeypatch, capsys, typed, reason):
    """Windows 旧控制台按 Ctrl+V 只读到 0x16：当场拒绝，不把坏 key 写进文件。"""
    monkeypatch.setattr(key.getpass, "getpass", lambda prompt="": typed)
    assert key.run() == 1
    assert not env_file.exists()
    out = capsys.readouterr().out
    assert reason in out and "未写任何文件" in out


def test_invalid_key_leaves_existing_file_unchanged(env_file, monkeypatch):
    env_file.parent.mkdir(parents=True)
    env_file.write_text("TYPESAFE_API_KEY=sk-old\nJUDGE_PROVIDER=jev\n", encoding="utf-8")
    monkeypatch.setattr(key.getpass, "getpass", lambda prompt="": "\x16")
    assert key.run() == 1
    assert env_file.read_text(encoding="utf-8") == "TYPESAFE_API_KEY=sk-old\nJUDGE_PROVIDER=jev\n"


@pytest.mark.parametrize(("value", "reason"), [
    ("sk-abc123", None), ("\x16", "0x16"), ("sk-ab\tcd", "含空白"), ("sk-ab\u3000cd", "含空白"),
    ("sk-\x00", "不可打印"), ("sk-密钥", "非 ASCII"),
])
def test_key_problem(value, reason):
    problem = judge.key_problem(value)
    assert problem is None if reason is None else reason in problem
