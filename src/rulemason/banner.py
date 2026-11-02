"""启动画面：交互运行 init 或不带参数运行 rulemason 时，显示字标、版本、口号与三件事。"""
from __future__ import annotations

import os
import shutil
import sys

from rulemason import __version__

MIN_WIDTH = 60      # 窄于这个宽度不画字标，避免折行
# 配色仿 openspec：一个强调色（天空蓝）点字标、标签、命令与最后的提示；正文与命令说明默认白，版本号与 init 说明用暗色
SKY = "38;5;117"    # 256 色的天空蓝（SkyBlue1）
SKY_BOLD = "1;38;5;117"
DIM = "2"
BOLD = "1"

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
    ("rulemason --help", "查看全部命令"),
)
_CMD_WIDTH = max(len(cmd) for cmd, _ in COMMANDS) + 2     # 最长命令后空两格对齐说明
COMMANDS_FOOTER = (
    (("常用命令：", None),),
    *((("  ", None), (cmd.ljust(_CMD_WIDTH), SKY), (desc, None)) for cmd, desc in COMMANDS),
)


def _paint(text: str, code: str | None, color: bool) -> str:
    if code is None or not color:
        return text
    return f"\033[{code}m{text}\033[0m"


def _word(word: str, row: int) -> str:
    return " ".join(GLYPHS[c][row] for c in word)


def render(version: str, footer: tuple, width: int, color: bool, unicode_ok: bool) -> str:
    """拼出整屏文字；width 不够或写不出块字符时，字标换成一行「rulemason 版本」。"""
    # 1. 字标与版本号，口号紧贴其下
    if width >= MIN_WIDTH and unicode_ok:
        lines = [_paint(_word("RULEMASON", i), SKY, color) for i in range(3)]
        lines[-1] += "  " + _paint(version, DIM, color)
    else:
        lines = [_paint("rulemason", SKY_BOLD, color) + " " + _paint(version, DIM, color)]
    lines.append(_paint(SLOGAN, BOLD, color))
    # 2. 三件事
    lines += ["", "只管三件事："]
    lines += [f"  {_paint(label, SKY_BOLD, color)}  {text}" for label, text in THREE_THINGS]
    # 3. 本次说明或常用命令
    lines.append("")
    lines += ["".join(_paint(text, code, color) for text, code in segments) for segments in footer]
    return "\n".join(lines)


def interactive() -> bool:
    """标准输入与输出都是终端；输出被管道接走时不显示，免得颜色转义进日志。"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _unicode_ok() -> bool:
    try:
        "█▀▄".encode(sys.stdout.encoding or "ascii")
    except UnicodeEncodeError:
        return False
    return True


def show(footer: tuple) -> None:
    """按当前终端的颜色、宽度与编码打印启动画面。"""
    color = not os.environ.get("NO_COLOR")
    width = shutil.get_terminal_size().columns
    print("\n" + render(__version__, footer, width, color, _unicode_ok()) + "\n")     # 上下各留一行，和提示符隔开
