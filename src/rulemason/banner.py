"""启动画面：交互运行 init 或不带参数运行 rulemason 时，显示像素图标、字标、版本、口号与三件事。"""
from __future__ import annotations

import shutil
import sys

from rulemason import __version__
from rulemason.shared import (
    BOLD,
    DIM,
    SKY,
    SKY_BOLD,
    SKY_NUM,
    color_enabled,
    legacy_console,
    paint,
)

MIN_WIDTH = 60      # 窄于这个宽度不画图标与字标，避免折行
# 配色仿 openspec：一个强调色（天空蓝）点字标、标签、命令与最后的提示；正文与命令说明默认白，版本号与 init 说明用暗色。颜色常量在 shared

# 半格块字形，每个字母 3 行
GLYPHS = {
    "R": ["█▀▀█", "█▀▀▄", "▀  ▀"],
    "U": ["█  █", "█  █", "▀▀▀▀"],
    "L": ["█   ", "█   ", "▀▀▀▀"],
    "E": ["█▀▀▀", "█▀▀ ", "▀▀▀▀"],
    "M": ["█▀▄▀█", "█   █", "▀   ▀"],
    "A": ["█▀▀█", "█▀▀█", "▀  ▀"],
    "S": ["█▀▀▀", "▀▀▀█", "▀▀▀▀"],
    "O": ["█▀▀█", "█  █", "▀▀▀▀"],
    "N": ["█▀▀▄", "█  █", "▀  ▀"],
}
# 像素图标：一匹向右奔跑的马，背上骑着一只兔，26 列 × 20 行像素，每两行像素合成一行字符
# t 马身、b 鬃尾、d 蹄与眼、w 兔、g 兔的阴影、h 眼睛镂空、. 空
ICON = (
    ".............ww...........",
    "........ww..wgw...........",
    ".........wwwwgw....t.t....",
    ".........wwwww.....tbt....",
    "........wwwwwww.b.btttt...",
    "........whwwwhw.bbbttdtttt",
    "........wwwgwwwbbbtttttttt",
    ".........wwwww.bbbtttttttt",
    "b...bbb.wwwwwww.bbtttt....",
    "bb.bbbbbwwwwwwwbbbttt.....",
    ".bbbbb.bbggtggttttttt.....",
    "..bbb...ttttttttttttt.....",
    "........ttttttttttttt.....",
    "........tttttttttttttd....",
    "........tttttttttttttdd...",
    ".........tt.ttttttttt..d..",
    "........ttt........tt..d..",
    "........t.d..........t.d..",
    "........tt.d.........t....",
    "..........t........tt.....",
)
# 像素字母到 256 色号：马身与字标同色，鬃尾深一档，蹄与眼暗灰，兔身樱粉（白色在浅底终端上看不见），兔的阴影深一档；不在表里的字母不画
ICON_COLORS = {"t": SKY_NUM, "b": "74", "d": "245", "w": "211", "g": "168"}
SLOGAN = "AI 写代码，也讲章法"
THREE_THINGS = (
    ("读", "写之前，先读项目的规则"),
    ("守", "写的时候，方案和代码按规则来"),
    ("查", "写完以后，lint、测试、审查自动跑"),
)
# 结尾两种：每行是若干 (文字, 颜色) 段，颜色为 None 表示默认色
INIT_FOOTER = (
    (("这次会：选你用的 AI 工具，在项目里放好规则和入口，补齐 lint 与方案写法。", DIM),),
    (("先列计划，你确认后才写入。", SKY),),
)
COMMANDS = (
    ("rulemason init", "初始化"),
    ("rulemason check", "检查初始化状态，不改文件"),
    ("rulemason update", "同步新版规则和配置"),
    ("rulemason key", "配置判断用的 Jev key（本机一次）"),
    ("rulemason --help", "查看全部命令"),
)
_CMD_WIDTH = max(len(cmd) for cmd, _ in COMMANDS) + 2     # 最长命令后空两格对齐说明
COMMANDS_FOOTER = (
    (("常用命令：", None),),
    *((("  ", None), (cmd.ljust(_CMD_WIDTH), SKY), (desc, None)) for cmd, desc in COMMANDS),
)


def _word(word: str, row: int) -> str:
    return " ".join(GLYPHS[c][row] for c in word)


def _cell(top: str | None, bottom: str | None, color: bool) -> str:
    """上下两个像素合成一个字符：上有下无 ▀、上无下有 ▄、都有 █；两种颜色时上像素做前景、下像素做背景。"""
    if top is None and bottom is None:
        return " "
    if bottom is None:
        return paint("▀", f"38;5;{top}", color)
    if top is None:
        return paint("▄", f"38;5;{bottom}", color)
    if top == bottom or not color:
        return paint("█", f"38;5;{top}", color)
    return paint("▀", f"38;5;{top};48;5;{bottom}", color)


def _icon_lines(color: bool) -> list[str]:
    """把 20 行像素合成 10 行字符，去掉行尾空格。"""
    return [
        "".join(_cell(ICON_COLORS.get(t), ICON_COLORS.get(b), color) for t, b in zip(top, bottom, strict=True)).rstrip()
        for top, bottom in zip(ICON[::2], ICON[1::2], strict=True)
    ]


def render(version: str, footer: tuple, width: int, color: bool, unicode_ok: bool) -> str:
    """拼出整屏文字；width 不够或写不出块字符时，图标与字标换成一行「rulemason 版本」。"""
    # 1. 图标、空一行、字标与版本号，口号紧贴其下
    if width >= MIN_WIDTH and unicode_ok:
        lines = [*_icon_lines(color), ""]
        lines += [paint(_word("RULEMASON", i), SKY, color) for i in range(3)]
        lines[-1] += "  " + paint(version, DIM, color)
    else:
        lines = [paint("rulemason", SKY_BOLD, color) + " " + paint(version, DIM, color)]
    lines.append(paint(SLOGAN, BOLD, color))
    # 2. 三件事
    lines += ["", "只管三件事："]
    lines += [f"  {paint(label, SKY_BOLD, color)}  {text}" for label, text in THREE_THINGS]
    # 3. 本次说明或常用命令
    lines.append("")
    lines += ["".join(paint(text, code, color) for text, code in segments) for segments in footer]
    return "\n".join(lines)


def interactive() -> bool:
    """标准输入与输出都是终端；输出被管道接走时不显示，免得颜色转义进日志。"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _can_draw_blocks() -> bool:
    """能画块字符：Windows 旧控制台缺半格字形、又按两格宽画，不画；其余只看标准输出编码能否写出块字符。"""
    if legacy_console():
        return False
    try:
        "█▀▄".encode(sys.stdout.encoding or "ascii")
    except UnicodeEncodeError:
        return False
    return True


def show(footer: tuple) -> None:
    """按当前终端的颜色、宽度与编码打印启动画面。"""
    color = color_enabled()
    width = shutil.get_terminal_size().columns
    print("\n" + render(__version__, footer, width, color, _can_draw_blocks()) + "\n")     # 上下各留一行，和提示符隔开
