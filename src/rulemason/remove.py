"""rulemason remove：从项目卸载 rulemason——删副本、清单与标记块，lint 继承改到项目 lint/，列计划一次确认后写入。"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

import yaml

from rulemason import check
from rulemason.init import (
    JSON_STRING,
    Plan,
    Stop,
    apply,
    ask_yes,
    config_ref,
    instructions_array,
    interactive,
    opencode_template,
    operations_section,
    plan_drop_blocks,
    plan_stale_copies,
    preflight,
    print_plan,
    same_except,
)
from rulemason.shared import (
    COPY_DIR,
    MANIFEST,
    NAME,
    OLD_MANIFEST,
    OLD_NAME,
    list_files,
    read_yaml,
    shared_root,
    unmigrated,
)

LINT_DIR = "lint"                                            # 卸载后 lint 基础配置在项目里的新位置
CONFIG = "openspec/config.yaml"
DELETE_TITLE = "删除（rulemason 生成且未改动的文件）"


# ---------- 1. lint 继承改到项目 lint/ ----------

def lint_configs(root: Path, files: list[str]) -> list[tuple[str, Callable[[Path, str, str], list[str]], str]]:
    """(配置文件, 取共享引用的函数, 共享基础配置文件名)：项目里的 ruff 与 ESLint 配置。"""
    configs = [(f, check.ruff_shared_refs, "ruff-base.toml") for f, _ in check.ruff_configs(root, files)]
    return configs + [(f, check.eslint_shared_refs, "eslint-base.mjs") for f in check.eslint_configs(files)]


def plan_lint_move(root: Path, files: list[str], plan: Plan) -> list[str]:
    """把仍被引用的 lint 副本写到项目根 lint/，改写各配置的引用；返回被移走的副本路径。
    lint/ 里已有同名而内容不同的文件时抛 Stop。"""
    names = []
    # 1. 改写引用：每个配置改为从自己所在目录指向 lint/<文件名>
    for f, find_refs, name in lint_configs(root, files):
        text = plan.text(root, f)
        refs = find_refs(root, f, text)
        if not refs:
            continue
        new_ref = config_ref(root, f, root / LINT_DIR / name)
        for ref in refs:
            text = text.replace(f'"{ref}"', f'"{new_ref}"').replace(f"'{ref}'", f"'{new_ref}'")
        plan.writes[f] = text
        if name not in names:
            names.append(name)
    # 2. 搬运内容：副本（手改过的也照原样）写到 lint/；副本已丢失时用当前共享版本
    for name in names:
        copy = f"{COPY_DIR}/lint/{name}"
        source = root / copy
        content = (source if source.is_file() else shared_root() / "lint" / name).read_text(encoding="utf-8")
        target = f"{LINT_DIR}/{name}"
        if not (root / target).exists():
            plan.writes[target] = content
        elif not (root / target).is_file() or (root / target).read_text(encoding="utf-8") != content:
            raise Stop(f"{target} 已存在且内容与 {copy} 不同：lint 继承无法移过去，未写任何文件。请先改名或删除 {target}")
    return [f"{COPY_DIR}/lint/{name}" for name in names]


# ---------- 2. 入口与配置 ----------

def remove_instructions(text: str, refs: list[str]) -> str | None:
    """从 OpenCode 配置唯一的 instructions 数组删去 refs：只重排数组内部，其余文字逐字保留。
    没有能安全改写的数组，或删后读出的值不等于原值去掉 refs 时返回 None。"""
    match = instructions_array(text)
    if match is None:
        return None
    body = match.group(1)
    kept = [lit for lit in JSON_STRING.findall(body) if json.loads(lit) not in refs]
    element = re.search(r'\n([ \t]*)"', body)
    if not kept:
        new_body = ""
    elif element:
        # 多行数组：每条一行、照抄缩进，收尾的换行与缩进不变
        new_body = ",".join(f"\n{element.group(1)}{lit}" for lit in kept) + body[len(body.rstrip()):]
    else:
        new_body = ", ".join(kept)
    new = text[: match.start(1)] + new_body + text[match.end(1):]
    expected = [v for v in check.opencode_instruction_values(text) if v not in refs]
    if check.opencode_instruction_values(new) != expected:
        return None
    return new


def plan_opencode_removal(root: Path, files: list[str], plan: Plan) -> None:
    """OpenCode 配置：删去指向 .rulemason/ 的条目后与生成的骨架相同就删文件，否则只删条目；改不了只提示。"""
    template = opencode_template(root, files)
    skeleton = remove_instructions(template, check.opencode_instruction_values(template))
    for rel in check.opencode_configs(root):
        text = plan.text(root, rel)
        ours = [v for v in check.opencode_instruction_values(text) if v.startswith(f"{COPY_DIR}/")]
        if not ours:
            continue
        new = remove_instructions(text, ours)
        if new is None:
            plan.notes.append(f"{rel} 的 instructions 仍引用 {'、'.join(ours)}：未修改，请手动删去")
        elif new == skeleton:
            plan.deletes.append(rel)                        # 整份都是 init 生成的
        else:
            plan.writes[rel] = new


def plan_operations_removal(root: Path, plan: Plan) -> None:
    """config.yaml 的 operations 段与 init 追加时一字不差才删，并核对其他键不变；否则只提示。"""
    if not (root / CONFIG).is_file():
        return
    data = read_yaml(root / CONFIG, {})
    if "operations" not in data:
        # 走到这里说明没有 operations 段（顶层是映射才会走到下面）
        return
    text = plan.text(root, CONFIG)
    appended = operations_section(root)
    if text.count(appended) == 1:
        new = text.replace(appended, "\n", 1)
        try:
            after = yaml.safe_load(new) or {}
        except yaml.YAMLError:
            after = None                                     # 删后读不出来：不改，交给下面的提示
        if isinstance(after, dict) and "operations" not in after and same_except(data, after, "operations"):
            plan.writes[CONFIG] = new
            return
    # 走到这里说明 operations 被改过，或删后会影响其他配置
    plan.notes.append(f"{CONFIG} 的 operations 与 init 追加时不同：未修改，请自行删去 apply / archive 的检查点提示")


def keep_unrewritten_lint(root: Path, files: list[str], plan: Plan) -> None:
    """改写后仍引用 .rulemason/lint/ 的配置（引用写法没被识别出来）：保留 lint 副本，不让 lint 跑不起来。"""
    stuck = [f for f, _, _ in lint_configs(root, files) if f"{COPY_DIR}/lint/" in plan.text(root, f)]
    if not stuck:
        return
    plan.deletes = [rel for rel in plan.deletes if not rel.startswith(f"{COPY_DIR}/lint/")]
    plan.notes.append(f"{'、'.join(stuck)} 仍引用 {COPY_DIR}/lint/（写法未能自动改写）：保留 {COPY_DIR}/lint/，请手动改为 {LINT_DIR}/ 后删除")


def keep_agents_import(root: Path, plan: Plan) -> None:
    """CLAUDE.md 删完标记块后不再导入 AGENTS.md 时，留一行 @AGENTS.md：AGENTS.md 是项目指令，Claude Code 只经 CLAUDE.md 读它。"""
    rel = "CLAUDE.md"
    if not (root / "AGENTS.md").is_file() or "AGENTS.md" in plan.deletes:
        return
    if rel in plan.deletes:
        plan.deletes.remove(rel)
        plan.writes[rel] = "@AGENTS.md\n"
    elif rel in plan.writes and "@AGENTS.md" not in plan.writes[rel]:
        plan.writes[rel] = "@AGENTS.md\n\n" + plan.writes[rel]


def project_content_notes(root: Path, moved: list[str], plan: Plan) -> list[str]:
    """已成为项目内容、卸载不动的部分，逐项列给用户决定。"""
    notes = []
    if check.project_artifact_rules(root):
        notes.append(f"{CONFIG} 的产物写法规则（rules）：已是项目内容，未改动")
    if (root / check.WORKFLOW_SPEC).is_file():
        notes.append(f"{check.WORKFLOW_SPEC}：项目的检查点规格，未改动")
    if (root / "AGENTS.md").is_file() and "AGENTS.md" not in plan.deletes:
        notes.append("AGENTS.md 的项目简介、命令表与红线：未改动")
    gitignore = root / ".gitignore"
    if gitignore.is_file() and f"skills/{NAME}" in gitignore.read_text(encoding="utf-8"):
        notes.append(f".gitignore 中放行 skills/{NAME}/ 的规则：未改动，不需要时自行删去")
    notes += [f"{LINT_DIR}/{Path(copy).name}：由 {copy} 移来，今后由项目自己维护" for copy in moved]
    return notes


def build_removal(root: Path, manifest: dict) -> Plan:
    """卸载计划：lint 先移走，再删副本、清单与标记块，最后处理 OpenCode 与 operations。"""
    files = list_files(root)
    plan = Plan()
    moved = plan_lint_move(root, files, plan)
    record = {rel: digest for rel, digest in (manifest.get("files") or {}).items() if rel not in moved}
    plan_stale_copies(root, record, {}, plan)
    plan.deletes += [copy for copy in moved if (root / copy).is_file()]
    keep_unrewritten_lint(root, files, plan)
    for rel in check.BLOCKS:
        plan_drop_blocks(root, rel, plan, "卸载时")
    keep_agents_import(root, plan)
    plan_opencode_removal(root, files, plan)
    plan_operations_removal(root, plan)
    plan.notes += project_content_notes(root, moved, plan)
    plan.deletes.append(MANIFEST)                            # 清单最后删：中途失败时还能重跑 remove
    return plan


# ---------- 3. 跑 ----------

def run(root: Path, yes: bool = False, plan_only: bool = False) -> int:
    try:
        # 1. 非交互环境写入时必须带 --yes，不等待输入；只看计划不受限
        if not plan_only and not interactive() and not yes:
            raise Stop("不是交互终端：请用 --yes 运行（先看计划用 --plan）", 2)
        # 2. 预检：源码仓库、旧接入方式、旧格式、没有清单都停下
        manifest = preflight(root, "remove")
        if unmigrated(root, manifest):
            raise Stop(f"有 {OLD_MANIFEST}：这是 {OLD_NAME} 0.5 格式，先运行 {NAME} init 迁移，再卸载；未写任何文件")
        if manifest is None:
            raise Stop(f"没有 {MANIFEST}：这个项目没有接入 {NAME}（判断的项目根：{root}）；未写任何文件")
        plan = build_removal(root, manifest)
    except Stop as exc:
        print(str(exc))
        return exc.code

    # 3. 计划与确认
    print_plan(root, plan, DELETE_TITLE)                     # 计划里总有清单要删，不会是空计划
    if plan_only:
        print("只列计划，未写任何文件。确认后运行 rulemason remove --yes")
        return 0
    if not yes and not ask_yes("按计划卸载？"):
        print("已取消，未写任何文件。")
        return 0
    try:
        apply(root, plan)
    except ValueError as exc:
        print(str(exc))
        return 1

    # 4. 汇报
    print("已卸载。本次改动的文件：" + "、".join([*plan.writes, *plan.deletes]))
    print(f"本机安装的 {NAME} 不受影响；不再使用时运行 uv tool uninstall {NAME}")
    return 0
