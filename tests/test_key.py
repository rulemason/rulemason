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
