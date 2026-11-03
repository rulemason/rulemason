"""终端里的多选：上下键或 j / k 移动，空格勾选，a 全选，回车确认，q 取消；读不了单键时抛 Unsupported，由调用方退回编号输入。"""
from __future__ import annotations

import importlib.util
import os
import selectors
import sys
from collections.abc import Callable

from rulemason.shared import DIM, SKY, SKY_BOLD, YELLOW, paint


class Unsupported(Exception):
    """不是终端，或平台没有 termios：无法逐键读取。"""


KEY_NAMES = {b" ": "space", b"\r": "enter", b"\n": "enter", b"a": "all", b"q": "quit", b"\x04": "quit",
             b"j": "down", b"k": "up", b"\x1b[A": "up", b"\x1b[B": "down"}
HINT = "上下键移动，空格勾选，a 全选，回车确认，q 取消"


def ensure_supported() -> None:
    """能逐键读取的前提：输入输出都是终端，且平台有 termios；不满足抛 Unsupported。画第一帧之前就要确认，免得转义序列进日志。"""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise Unsupported("标准输入或输出不是终端")
    if importlib.util.find_spec("termios") is None:         # Windows 没有 termios
        raise Unsupported("本平台不支持逐键读取")


def _pending(fd: int, seconds: float) -> bool:
    """在 seconds 内还有字节可读。"""
    with selectors.DefaultSelector() as sel:
        sel.register(fd, selectors.EVENT_READ)
        return bool(sel.select(seconds))


def read_key() -> str:
    """读一个按键，返回 KEY_NAMES 里的名字；不认识的键返回 ""。只在终端里可用。"""
    ensure_supported()
    import termios
    import tty
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        data = os.read(fd, 1)
        if data == b"":
            return "quit"                                     # 输入结束（管道关闭或 Ctrl-D）：当作取消，不能空转
        if data == b"\x1b" and _pending(fd, 0.05):
            data += os.read(fd, 2)                            # 方向键是三字节序列；单独按下 ESC 时没有后续字节，不能等
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)     # 异常也要把终端恢复成回显模式
    return KEY_NAMES.get(data, "")


def render(title: str, labels: list[str], checked: list[bool], notes: list[str], cursor: int, message: str) -> str:
    lines = [paint(title, SKY_BOLD) + "  " + paint(HINT, DIM)]
    for i, (label, on, note) in enumerate(zip(labels, checked, notes, strict=True)):
        pointer = ">" if i == cursor else " "
        line = f"{pointer} [{'x' if on else ' '}] {label}" + (f"  {paint(note, DIM)}" if note else "")
        lines.append(paint(line, SKY) if i == cursor else line)
    lines.append(paint(message, YELLOW) if message else "")
    return "\n".join(lines)


def choose(title: str, labels: list[str], checked: list[bool], notes: list[str],
           key: Callable[[], str] = read_key, out=None) -> list[int] | None:
    """返回勾选项的下标；q、Ctrl-C 或输入结束返回 None。用真实键盘时先确认能逐键读取，不支持就在画帧前抛 Unsupported，由调用方退回别的方式。"""
    if key is read_key:
        ensure_supported()
    out = out or sys.stdout
    checked = list(checked)
    cursor, message, rewind = 0, "", ""
    while True:
        frame = render(title, labels, checked, notes, cursor, message)
        out.write(rewind + "\r" + "\n".join(f"\033[2K{line}" for line in frame.split("\n")) + "\n")
        out.flush()
        rewind = f"\033[{frame.count(chr(10)) + 1}A"                 # 下一帧先把光标移回这一帧的顶端
        try:
            action = key()
        except KeyboardInterrupt:
            return None
        if action == "quit":
            return None
        if action == "enter" and any(checked):
            return [i for i, on in enumerate(checked) if on]
        cursor, message = _apply(action, cursor, checked)


def _apply(action: str, cursor: int, checked: list[bool]) -> tuple[int, str]:
    """按键改状态：移动光标、切换当前项、全选；回车时没选任何项给出提示。返回 (光标, 提示)。"""
    if action == "up":
        return (cursor - 1) % len(checked), ""
    if action == "down":
        return (cursor + 1) % len(checked), ""
    if action == "space":
        checked[cursor] = not checked[cursor]
    elif action == "all":
        checked[:] = [True] * len(checked)
    return cursor, "至少选一个" if action == "enter" else ""
