"""rulemason 命令行入口：解析参数，分发到 init / update / check / remove / key；judge 的参数原样交给判断引擎。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rulemason import __version__, banner, check, init, key, remove, update
from rulemason.judge import judge
from rulemason.shared import find_root


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="rulemason", description="在项目里接入、升级、检查 rulemason 共享规则，并判断方案与文案")
    ap.add_argument("--version", action="version", version=f"rulemason {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init", help="在项目根接入 rulemason：选工具、生成 .rulemason/ 副本与入口")
    p_init.add_argument("path", nargs="?", help="项目根，默认当前目录")
    p_init.add_argument("--tools", help="逗号分隔的工具 id：opencode、claude、cursor、codex；传了就不提问")
    p_init.add_argument("--yes", action="store_true", help="不确认，直接按计划写入")
    p_init.add_argument("--plan", action="store_true", help="只列文件计划，不写入、不提问、不运行 openspec init")
    p_init.add_argument("--json", action="store_true", help="配合 --plan 输出 JSON")
    p_update = sub.add_parser("update", help="刷新副本、skill 与标记块；缺的配置列出补齐计划，确认后写入")
    p_update.add_argument("--yes", action="store_true", help="补齐计划不确认，直接写入")
    p_update.add_argument("--dry-run", action="store_true", help="只列管理计划与补齐计划，不写入、不提问")
    p_update.add_argument("--json", action="store_true", help="配合 --dry-run 输出 JSON")
    p_check = sub.add_parser("check", help="只读检查，副本被改或入口缺失时以非 0 退出")
    p_check.add_argument("--json", action="store_true", help="输出 JSON（给 AI 与脚本读），退出码不变")
    p_remove = sub.add_parser("remove", help="从项目卸载 rulemason：删副本、清单与标记块，lint 继承改到项目 lint/；先列计划再确认")
    p_remove.add_argument("--plan", action="store_true", help="只列计划，不写入、不提问")
    p_remove.add_argument("--yes", action="store_true", help="不确认，直接按计划卸载")
    sub.add_parser("key", help="在终端里交互输入 Jev 的 key（不回显），写入 ~/.config/rulemason/env")
    # judge 的参数只在引擎里定义一处，这里不重复声明，原样转交
    sub.add_parser("judge", add_help=False, help="判断 change 产物或界面文案（rulemason judge --help 查看参数）")
    argv = sys.argv[1:] if argv is None else argv
    if not argv and banner.interactive():
        # 终端里不带参数：显示启动画面与常用命令；脚本里交给 argparse 照旧报用法错误
        banner.show(banner.COMMANDS_FOOTER)
        sys.exit(0)
    args, rest = ap.parse_known_args(argv)
    if args.command == "judge":
        judge.cli(rest)
    if rest:
        ap.error(f"无法识别的参数：{' '.join(rest)}")
    if args.command == "init" and args.json and not args.plan:
        # 走到这里说明调用方以为只看计划，实际会写入：直接报错，不碰文件
        ap.error("--json 只能配合 --plan 使用：rulemason init --plan --json")
    if args.command == "update" and args.json and not args.dry_run:
        ap.error("--json 只能配合 --dry-run 使用：rulemason update --dry-run --json")
    try:
        sys.exit(_dispatch(args))
    except (OSError, ValueError) as exc:
        # 命令行最外层：给出可读的错误，不打印 traceback
        sys.exit(f"rulemason {args.command} 失败：{exc}")


def _dispatch(args: argparse.Namespace) -> int:
    # 项目根：往上找最近的清单；init 显式给出路径时以该路径为根，不再往上找
    root = find_root(Path.cwd().resolve())
    if args.command == "init":
        return init.run(Path(args.path).resolve() if args.path else root, args.tools, args.yes, args.plan, args.json)
    if args.command == "remove":
        return remove.run(root, args.yes, args.plan)
    if args.command == "key":
        return key.run()
    if args.command == "update":
        return update.run(root, args.yes, args.dry_run, args.json)
    text, code = check.run(root, args.json)
    print(text)
    return code
