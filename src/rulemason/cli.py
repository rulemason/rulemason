"""rulemason 命令行入口：解析参数，分发到 init / update / check / remove / key / result-check；judge 的参数原样交给判断引擎。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rulemason import (
    __version__,
    banner,
    check,
    init,
    key,
    remove,
    result_check,
    update,
)
from rulemason.judge import judge
from rulemason.shared import find_root

_RESULT_CHECK_EPILOG = """\
首个接入场景：产品解读结构化输出（调用方交已发生记录）。
离线可用 fixture 验收；fixture 不等于真实模型会话。
支持 field：一项一路径（. 分隔）；值类型用 value_type（可联合数组）；
optional、minimum/maximum、min_length/max_length（Unicode 码点）、enum、pattern、min_items/max_items。
数组可用 items 约束每个元素；对象元素用 fields（列出的键默认必填，可 optional: true）。
空数组 + items 真空通过；非空靠 min_items。失败解释含下标路径（如 待确认[1].怎么确认）。
支持 cjk_typography：可开关中文排版规则（全角数字/字母、叠标点、中英/中数空格、单位空格、
度百分号、全角标点旁空格、半角标点夹汉字、表意空格等）；检查前剥离围栏（含 ~~~）/缩进代码/
行内代码、链接目标与自动链接、引用式定义、裸 URL、行内 HTML；HTML 注释 rulemason-disable/
enable 可临时关闭规则；可选 allowlist、units、max_hits（默认 50，截断时标明总数）。
支持 prose_hygiene：推荐短名 chatbot_closer / signpost_opener / not_just_contrast；
em_dash 高级可选（默认关闭）。severity=hint（默认）命中为「提示」且单独不导致非零；
severity=strict 命中失败。提示不吞掉其他失败或输入错误。可用 --preset hint|strict
（项目 .rulemason/result-check 种子优先，否则包内模板）。init/update 自动分发规则正文，
并仅在缺失时种入预设；不会自动扫仓或改 check 退出码。
父路径为 null 或键缺失时，子路径项记未检查/不适用。约束由调用方 requirements 提供。
旧 structured_keys 等类型语义不变。本期排除 Skill 出现检查。
模式核对信任调用方提供的模式（本地确定性，无超时沙箱）。
不改 check / update / judge 的既有语义。退出码：0 总体通过（可含提示）；1 失败或无法判断；2 输入错误。
"""


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
    p_result = sub.add_parser(
        "result-check",
        help="对调用方提供的已发生运行记录做确定性检查（本地、不调模型）",
        epilog=_RESULT_CHECK_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_result.add_argument("--record", required=True, help="运行记录 JSON 路径（调用方提供）")
    p_result.add_argument("--requirements", help="检查要求 JSON 路径（与 --preset 二选一）")
    p_result.add_argument(
        "--preset",
        choices=("hint", "strict"),
        help="使用 prose_hygiene 预设（hint 默认提示不阻断；strict 阻断）；与 --requirements 二选一",
    )
    p_result.add_argument("--json", action="store_true", help="只输出机器可读 JSON（schema 自有，不改 check --json）")
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
    # 项目根：往上找最近的清单，找不到就用当前目录（与 openspec init 一致）；init 显式给出路径时以该路径为根
    cwd = Path.cwd().resolve()
    root = find_root(cwd) or cwd
    if args.command == "init":
        target = Path(args.path).resolve() if args.path else root
        return init.run(target, args.tools, args.yes, args.plan, args.json, at_cwd=target == cwd)
    if args.command == "remove":
        return remove.run(root, args.yes, args.plan)
    if args.command == "key":
        return key.run()
    if args.command == "update":
        return update.run(root, args.yes, args.dry_run, args.json)
    if args.command == "result-check":
        return _run_result_check(args)
    text, code = check.run(root, args.json)
    print(text)
    return code


def _run_result_check(args: argparse.Namespace) -> int:
    if bool(args.requirements) == bool(args.preset):
        raise ValueError("result-check 须指定 --requirements 或 --preset 之一（不能同时、不能都缺）")
    record_path = Path(args.record)
    if args.preset:
        from rulemason.shared import find_root, resolve_result_check_preset

        root = find_root(Path.cwd().resolve())
        resolved = resolve_result_check_preset(root, args.preset)
        if isinstance(resolved, Path):
            report = result_check.run_files(record_path, resolved)
        else:
            # 包内模板：无项目种子时直接喂正文，记录文件错误归一为 exit 2
            try:
                report = result_check.run_check(
                    result_check.load_json(record_path),
                    json.loads(resolved),
                )
            except FileNotFoundError as exc:
                report = result_check.CheckReport(
                    schema=result_check.SCHEMA, overall_pass=False,
                    exit_code=result_check.EXIT_INPUT_ERROR, items=[],
                    limits="输入文件缺失，未执行逐项检查",
                    input_errors=[f"文件不存在：{exc.filename or exc}"],
                )
            except (OSError, ValueError) as exc:
                report = result_check.CheckReport(
                    schema=result_check.SCHEMA, overall_pass=False,
                    exit_code=result_check.EXIT_INPUT_ERROR, items=[],
                    limits="输入损坏，未执行逐项检查",
                    input_errors=[str(exc)],
                )
    else:
        report = result_check.run_files(record_path, Path(args.requirements))
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result_check.render_human(report))
    return report.exit_code
