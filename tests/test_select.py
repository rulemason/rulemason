"""终端多选器的测试：用假的按键序列驱动，覆盖移动、勾选、全选、空选提示、取消，以及不支持时抛 Unsupported。"""
from __future__ import annotations

import io
import os

import pytest

from rulemason import select

LABELS = ["甲", "乙", "丙"]


def _run(keys: list[str], checked=(False, False, False), notes=("", "检测到", "")):
    queue = list(keys)
    out = io.StringIO()
    result = select.choose("选工具", LABELS, list(checked), list(notes), key=lambda: queue.pop(0), out=out)
    return result, out.getvalue()


@pytest.mark.parametrize(("keys", "expected"), [
    (["down", "space", "enter"], [1]),
    (["up", "space", "enter"], [2]),                          # 向上越过第一项绕到最后一项
    (["space", "down", "down", "space", "enter"], [0, 2]),
    (["space", "space", "down", "space", "enter"], [1]),      # 再按一次空格取消勾选
    (["all", "enter"], [0, 1, 2]),
    (["", "down", "space", "enter"], [1]),                    # 不认识的键忽略
])
def test_keys_move_toggle_and_confirm(keys, expected):
    result, _ = _run(keys)
    assert result == expected


def test_enter_with_nothing_checked_asks_again():
    result, out = _run(["enter", "space", "enter"])
    assert result == [0]
    assert "至少选一个" in out


def test_quit_returns_none():
    result, _ = _run(["quit"])
    assert result is None


def test_prechecked_and_notes_are_shown():
    result, out = _run(["enter"], checked=(True, False, False))
    assert result == [0]
    assert "[x] 甲" in out and "[ ] 乙" in out and "检测到" in out and select.HINT in out


def test_read_key_outside_terminal_is_unsupported(monkeypatch):
    monkeypatch.setattr(select.sys, "stdin", io.StringIO())
    with pytest.raises(select.Unsupported):
        select.read_key()


class _Tty:
    """假终端：stdin 是一条管道的读端（真实 fd，能被 select 与 os.read），isatty 为真。"""

    def __init__(self, fd: int):
        self._fd = fd

    def isatty(self):
        return True

    def fileno(self):
        return self._fd


@pytest.fixture
def keyboard():
    """一条管道当键盘：返回 arm(monkeypatch)，在测试体里调用才打补丁——pytest 在 setup 与 call 之间会重装自己的 sys.stdout，
    fixture 里打的补丁活不到测试体。fixture 只负责最后关掉管道。"""
    termios = pytest.importorskip("termios")
    tty = pytest.importorskip("tty")
    read_fd, write_fd = os.pipe()
    restored: list = []

    def arm(monkeypatch):
        monkeypatch.setattr(select.sys, "stdin", _Tty(read_fd))
        monkeypatch.setattr(select.sys, "stdout", _Tty(1))
        monkeypatch.setattr(termios, "tcgetattr", lambda fd: "saved")
        monkeypatch.setattr(termios, "tcsetattr", lambda fd, when, attrs: restored.append(attrs))
        monkeypatch.setattr(tty, "setcbreak", lambda fd: None)
        return (lambda data: os.write(write_fd, data)), restored

    yield arm
    os.close(read_fd)
    os.close(write_fd)


def _raise_oserror(fd, n):
    raise OSError("断开")


@pytest.mark.parametrize(("data", "expected"), [(b"\x1b[A", "up"), (b"\x1b[B", "down"), (b" ", "space"), (b"\r", "enter"), (b"x", "")])
def test_read_key_parses_escape_sequences(keyboard, monkeypatch, data, expected):
    write, restored = keyboard(monkeypatch)
    write(data)
    assert select.read_key() == expected
    assert restored == ["saved"]                               # 读完把终端设置恢复


def test_bare_escape_does_not_block(keyboard, monkeypatch):
    write, _ = keyboard(monkeypatch)
    write(b"\x1b")
    assert select.read_key() == ""


def test_terminal_is_restored_when_read_fails(keyboard, monkeypatch):
    _, restored = keyboard(monkeypatch)
    monkeypatch.setattr(select.os, "read", _raise_oserror)
    with pytest.raises(OSError):
        select.read_key()
    assert restored == ["saved"]


def test_eof_on_stdin_cancels(keyboard, monkeypatch):
    """输入结束时不能空转：当作取消。"""
    keyboard(monkeypatch)
    monkeypatch.setattr(select.os, "read", lambda fd, n: b"")
    assert select.read_key() == "quit"


def test_choose_checks_support_before_drawing(monkeypatch):
    monkeypatch.setattr(select.sys, "stdin", io.StringIO())
    out = io.StringIO()
    with pytest.raises(select.Unsupported):
        select.choose("t", LABELS, [False] * 3, [""] * 3, out=out)
    assert out.getvalue() == ""
