"""rulemason update：刷新 rulemason 自己管的副本、标记块与清单；用户自己的配置缺了就列出补齐计划，确认或 --yes 才写。"""
from __future__ import annotations

from pathlib import Path

from rulemason import check
from rulemason.init import (
    TIPS_TITLE,
    Plan,
    Stop,
    apply,
    ask_yes,
    interactive,
    plan_blocks,
    plan_copies,
    plan_fill,
    plan_manifest,
    plan_stale_copies,
    preflight,
    print_notes,
    unsafe_targets,
)
from rulemason.shared import (
    CHECKPOINTS_OFF,
    MANIFEST,
    NAME,
    bullets,
    dump_json,
    has_openspec,
    list_files,
    repo_root_hint,
)

FILL_TITLE = "补齐计划（写进项目文件的 rulemason 基础配置，升级时与副本一起提交）："


def plan_update(root: Path, manifest: dict) -> tuple[Plan, Plan, dict[str, str]]:
    """返回 (管理计划, 补齐计划, 补齐计划里真正要写的文件)。管理计划直接写；补齐计划碰的是用户自己的文件。"""
    files = list_files(root)
    tools = manifest["tools"]

    # 1. 管理计划：副本、过时副本、已有标记块与清单
    managed = Plan()
    record = manifest.get("files") or {}
    new_record = plan_copies(root, tools, check.copied_rules(root, files), record, managed)
    plan_stale_copies(root, record, new_record, managed)
    plan_blocks(root, files, tools, managed, create=False)
    plan_manifest(root, manifest, tools, new_record, managed)
    # 只有真的写入的文件，里面与模板不一致的块才算被覆盖；块不齐整份跳过的文件留给补齐计划
    stale = check.stale_blocks(root, files, manifest)
    managed.overwritten += [f"标记块：{rel} 的 {name}" for rel, name in stale if rel in managed.writes]

    # 2. 补齐计划：以管理计划的结果为起点，只留新增的改动
    fill = Plan(writes=dict(managed.writes))
    plan_fill(root, files, tools, list(new_record), fill)
    fill_writes = {rel: text for rel, text in fill.writes.items() if managed.writes.get(rel) != text}
    for rel in unsafe_targets(root, list(fill_writes)):
        # 走到这里说明目标是符号链接（如 CLAUDE.md -> AGENTS.md）或在项目外：单独报告，其余补齐照写
        fill.notes.append(f"{rel} 是符号链接或在项目外，未补齐，请手动处理")
        del fill_writes[rel]
    return managed, fill, fill_writes


def show_dry_run(root: Path, managed: Plan, fill_writes: dict[str, str], notes: list[str], tips: list[str], as_json: bool) -> None:
    """update --dry-run：打印管理计划与补齐计划，不写、不问。"""
    if as_json:
        data = {
            "root": str(root),
            "managed": {"writes": list(managed.writes), "deletes": managed.deletes, "overwritten": managed.overwritten},
            "fill": list(fill_writes),
            "notes": notes,
        }
        print(dump_json(data))
        return
    print("将更新的文件：" + ("、".join([*managed.writes, *managed.deletes]) or "无，已是当前版本"))
    if managed.overwritten:
        print("以下副本或标记块与共享版本不一致，将按共享版本刷新：")
        print(bullets(managed.overwritten), end="")
    if fill_writes:
        print(FILL_TITLE + "、".join(fill_writes))
    print_notes(notes, "已跳过，需要你处理：")
    print_notes(tips, TIPS_TITLE, color=None)
    ask = f"终端里运行 {NAME} update 会询问是否补齐；非交互环境加 --yes" if fill_writes else f"确认后运行 {NAME} update"
    print(f"只列计划，未写任何文件。{ask}")


def run(root: Path, yes: bool = False, dry_run: bool = False, as_json: bool = False) -> int:
    # 1. 预检：源码仓库本身、没有或无效的 manifest 都停下
    try:
        manifest = preflight(root, "update")
    except Stop as exc:
        print(str(exc))
        return exc.code
    if manifest is None:
        print(f"没有 {MANIFEST}：先运行 {NAME} init（判断的项目根：{root}）")
        if hint := repo_root_hint(root):
            print(hint)
        return 1
    # 2. 两份计划；--dry-run 只打印，到此为止
    managed, fill, fill_writes = plan_update(root, manifest)
    notes = list(dict.fromkeys(managed.notes + fill.notes))
    tips = list(dict.fromkeys(managed.tips + fill.tips))
    if dry_run:
        show_dry_run(root, managed, fill_writes, notes, tips, as_json)
        return 0
    # 3. 管理计划直接写
    try:
        apply(root, managed)
    except ValueError as exc:
        print(str(exc))
        return 1
    print("更新的文件：" + ("、".join([*managed.writes, *managed.deletes]) or "无，已是当前版本"))
    if managed.overwritten:
        print("以下副本或标记块与共享版本不一致（被手改，或项目新增了语言），已按共享版本刷新：")
        print(bullets(managed.overwritten), end="")

    # 4. 补齐：交互确认或 --yes 才写，否则只列为待补齐
    if fill_writes:
        print(FILL_TITLE + "、".join(fill_writes))
        if yes or (interactive() and ask_yes("按补齐计划写入？")):
            apply(root, Plan(writes=fill_writes))             # 不安全的目标已在 plan_update 里挑出去
            print("已补齐。这些文件属于这次升级，请与副本、.rulemason.yaml 一起提交。")
        else:
            print(f"待补齐：未写入；终端里重新运行 {NAME} update 并答 y，非交互环境加 --yes")
    print_notes(notes, "已跳过，需要你处理：")
    print_notes(tips, TIPS_TITLE, color=None)
    if not has_openspec(root):
        print(CHECKPOINTS_OFF)
    return 0
