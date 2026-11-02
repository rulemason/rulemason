"""rulemason key：在终端里交互输入 Jev 的 key（不回显），写进 ~/.config/rulemason/env，其他设置原样保留。"""
from __future__ import annotations

import getpass
import os
import sys

from rulemason.judge import judge


def run() -> int:
    # 1. 只在终端里运行：key 不经命令行参数或管道传入，也就不会进历史、进程列表或 AI 会话
    if not sys.stdin.isatty():
        print("✗ 请在终端里运行 rulemason key，交互输入 key；未写任何文件")
        return 1
    value = getpass.getpass(f"{judge.KEY_NAME}（输入不显示）: ").strip()
    if not value:
        print("没有输入 key，未写任何文件")
        return 1

    # 2. 替换或追加 key 那一行，其他设置原样保留
    path = judge.USER_ENV
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    kept = [line for line in lines if line.partition("=")[0].strip() != judge.KEY_NAME]
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)                             # 目录若是指向别处的链接，收紧的是链接目标；key 文件本身不跟随链接
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    os.fchmod(descriptor, 0o600)                             # 已有文件可能是 644：写入 key 之前先收紧
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write("\n".join([*kept, f"{judge.KEY_NAME}={value}"]) + "\n")
    print(f"已写入 {path}（权限 600）；rulemason judge 会自动用 Jev 判断")
    return 0
