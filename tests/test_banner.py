"""启动画面的测试：渲染与降级、显示条件、init 与不带参数运行时是否出现。"""
from __future__ import annotations

import io
import re

import pytest
from conftest import run_cli

from rulemason import banner, init

LOGO_CHARS = set("█▀▄")


def _render(width: int = 80, color: bool = True, unicode_ok: bool = True) -> str:
    return banner.render("9.9.9", banner.INIT_FOOTER, width, color, unicode_ok)


def _visible(line: str) -> str:
    """去掉颜色转义后的文字。"""
    return re.sub(r"\033\[[\d;]+m", "", line)


# ---------- 1. 渲染与降级 ----------

def test_full_banner_has_sky_blue_logo_and_three_things():
    text = _render()
    lines = text.splitlines()
    assert lines[0].startswith(f"\033[{banner.SKY}m█▀▀█") and "█▀▄▀█" in lines[0]
    assert _visible(lines[2]).endswith("▀  ▀  9.9.9")
    assert max(len(_visible(s)) for s in lines[:3]) <= banner.MIN_WIDTH
    for word in (banner.SLOGAN, "只管三件事：", "写之前，先读项目的规则", "先列计划，你确认后才写入。"):
        assert word in text


def test_accent_color_marks_labels_commands_and_prompt():
    init_text = _render()
    assert f"\033[{banner.BOLD}m{banner.SLOGAN}" in init_text
    assert f"  \033[{banner.SKY_BOLD}m读\033[0m  写之前" in init_text                # 三件事的说明是正文，不加暗色
    assert f"\033[{banner.DIM}m9.9.9" in init_text
    assert f"\033[{banner.SKY}m先列计划，你确认后才写入。" in init_text
    commands = banner.render("9.9.9", banner.COMMANDS_FOOTER, 80, True, True)
    assert f"\033[{banner.SKY}mrulemason init    \033[0m初始化" in commands


def test_no_color_has_no_escape():
    text = _render(color=False)
    assert "\033" not in text
    assert text.splitlines()[0].startswith("█▀▀█ █  █ █    █▀▀▀ █▀▄▀█")


@pytest.mark.parametrize(("width", "unicode_ok"), [(59, True), (80, False)])
def test_narrow_or_non_unicode_drops_logo(width, unicode_ok):
    text = _render(width, color=False, unicode_ok=unicode_ok)
    assert not LOGO_CHARS & set(text)
    assert text.splitlines()[0] == "rulemason 9.9.9"
    assert banner.SLOGAN in text


# ---------- 2. 显示条件 ----------

class _Tty(io.StringIO):
    def __init__(self, tty: bool, encoding: str = "utf-8"):
        super().__init__()
        self._tty = tty
        self._encoding = encoding

    def isatty(self) -> bool:
        return self._tty

    @property
    def encoding(self) -> str:
        return self._encoding


@pytest.mark.parametrize(("stdin", "stdout", "expected"), [(True, True, True), (True, False, False), (False, True, False)])
def test_interactive_needs_both_ends(monkeypatch, stdin, stdout, expected):
    monkeypatch.setattr(banner.sys, "stdin", _Tty(stdin))
    monkeypatch.setattr(banner.sys, "stdout", _Tty(stdout))
    assert banner.interactive() is expected


@pytest.mark.parametrize(("encoding", "columns"), [("ascii", "120"), ("utf-8", "50")])
def test_show_drops_logo_for_encoding_or_width(monkeypatch, encoding, columns):
    out = _Tty(True, encoding)
    monkeypatch.setattr(banner.sys, "stdout", out)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("COLUMNS", columns)
    banner.show(banner.INIT_FOOTER)
    text = out.getvalue()
    assert "\033" not in text and text.startswith("\nrulemason ")
    assert not LOGO_CHARS & set(text)


def test_show_draws_logo_in_wide_utf8_terminal(monkeypatch):
    out = _Tty(True)
    monkeypatch.setattr(banner.sys, "stdout", out)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("COLUMNS", "120")
    banner.show(banner.INIT_FOOTER)
    assert out.getvalue().startswith(f"\n\033[{banner.SKY}m█▀▀█")     # 字标上方留一行空行


# ---------- 3. init 与不带参数 ----------

@pytest.fixture
def stop_after_banner(monkeypatch):
    """预检一开始就停下，只看启动画面是否出现。"""
    def stop(*_args):
        raise init.Stop("停在预检", 1)
    monkeypatch.setattr(init, "prepare", stop)
    monkeypatch.setattr(init, "interactive", lambda: True)
    monkeypatch.setattr(banner, "interactive", lambda: True)


def test_interactive_init_shows_banner_first(tmp_path, stop_after_banner, capsys):
    assert init.run(tmp_path, None, False) == 1
    out = capsys.readouterr().out
    assert out.index("只管三件事") < out.index("停在预检")


def test_init_with_piped_output_hides_banner(tmp_path, stop_after_banner, monkeypatch, capsys):
    monkeypatch.setattr(banner, "interactive", lambda: False)     # 标准输入是终端，输出被管道接走
    assert init.run(tmp_path, None, False) == 1
    assert "只管三件事" not in capsys.readouterr().out


@pytest.mark.parametrize(("yes", "plan_only"), [(True, False), (False, True)])
def test_init_with_yes_or_plan_hides_banner(tmp_path, stop_after_banner, capsys, yes, plan_only):
    assert init.run(tmp_path, "claude", yes, plan_only) == 1
    assert "只管三件事" not in capsys.readouterr().out


def test_bare_command_in_terminal_shows_commands(monkeypatch, capsys):
    monkeypatch.setattr(banner, "interactive", lambda: True)
    assert run_cli() == 0
    out = capsys.readouterr().out
    assert "只管三件事" in out and "rulemason init" in out and "rulemason --help" in out


def test_bare_command_in_script_keeps_usage_error(monkeypatch, capsys):
    monkeypatch.setattr(banner, "interactive", lambda: False)
    assert run_cli() == 2
    captured = capsys.readouterr()
    assert "required: command" in captured.err and captured.out == ""
