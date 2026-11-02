"""从 rulekit 0.5 格式迁移：旧清单、旧副本、旧标记块与已知配置里的旧路径，并入 init 的同一份文件计划。"""
from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from rulemason import check
from rulemason.shared import (
    COPY_DIR,
    NAME,
    OLD_COPY_DIR,
    OLD_MANIFEST,
    OLD_NAME,
    sha256_file,
)

if TYPE_CHECKING:
    from rulemason.init import Plan

INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")             # 只改标记，块内内容由 plan_blocks 刷新
OLD_PREFIXES = (f"{OLD_COPY_DIR}/", f".claude/skills/{OLD_NAME}/", f".agents/skills/{OLD_NAME}/")   # 迁移只删这些目录下的旧副本
OLD_MARKER = re.compile(rf"<!-- (/?){OLD_NAME}:")


class MigrationError(ValueError):
    """旧副本被手改过，迁移停止，不写任何文件。"""


def carried_manifest(old: dict) -> dict:
    """新清单的起点：沿用工具选择与用户自加的键；旧版本键与旧副本记录不带过来。"""
    return {key: value for key, value in old.items() if key not in (OLD_NAME, "files")}


def old_copies(root: Path, old: dict) -> list[str]:
    """旧清单记录、在旧副本目录里且仍存在的文件；任一与记录的校验值不符就抛 MigrationError。"""
    record = old.get("files") or {}
    existing = [rel for rel in record if is_old_copy(rel) and (root / rel).is_file()]
    changed = [rel for rel in existing if sha256_file(root / rel) != record[rel]]
    if changed:
        raise MigrationError(f"以下旧副本与 {OLD_MANIFEST} 记录不符，迁移停止，未写任何文件：" + "、".join(changed))
    return existing


def plan_migration(root: Path, files: list[str], old: dict, plan: Plan) -> None:
    """把迁移写进 plan：删旧清单与旧副本，标记改名，已知配置换路径前缀。改后的文本留在 plan.writes，后续计划以它为起点。"""
    # 1. 清单只是仓库里的文本：记录的路径不在旧副本目录里就不删，只报告
    record = old.get("files") or {}
    outside = [rel for rel in record if not is_old_copy(rel)]
    if outside:
        plan.notes.append(f"{OLD_MANIFEST} 记录了旧副本目录以外的路径，迁移不删：" + "、".join(outside))

    # 2. 删除旧清单与核对过的旧副本；旧副本目录里没记录的文件不删，只报告
    plan.deletes += [OLD_MANIFEST, *old_copies(root, old)]
    unrecorded = [rel for rel in files_under_old_dirs(root) if rel not in record]
    if unrecorded:
        plan.notes.append(f"以下文件不在 {OLD_MANIFEST} 的记录里，迁移不删，请自行处理：" + "、".join(unrecorded))

    # 3. 指令文件只改标记；已知配置只换路径前缀 .rulekit/ → .rulemason/
    for rel in INSTRUCTION_FILES:
        _rewrite(root, rel, plan, lambda text: OLD_MARKER.sub(rf"<!-- \1{NAME}:", text))
    for rel in config_files(root, files):
        _rewrite(root, rel, plan, lambda text: text.replace(f"{OLD_COPY_DIR}/", f"{COPY_DIR}/"))


def is_old_copy(rel: str) -> bool:
    """在旧副本目录里、且没有 .. 跳出的相对路径。"""
    return rel.startswith(OLD_PREFIXES) and ".." not in Path(rel).parts


def files_under_old_dirs(root: Path) -> list[str]:
    """直接遍历旧副本目录：没有 git 时 list_files 会跳过 .rulekit/，这里不依赖它。"""
    dirs = [root / prefix for prefix in OLD_PREFIXES]
    return sorted(p.relative_to(root).as_posix() for d in dirs if d.is_dir() for p in d.rglob("*") if p.is_file())


def config_files(root: Path, files: list[str]) -> list[str]:
    """会引用副本路径的配置：OpenCode instructions、ruff、ESLint、项目 workflow-gates 规格。"""
    return list(dict.fromkeys([*check.config_refs(root, files), check.WORKFLOW_SPEC]))


def _rewrite(root: Path, rel: str, plan: Plan, change: Callable[[str], str]) -> None:
    path = root / rel
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    new = change(text)
    if new != text:
        plan.writes[rel] = new


def residue_notes(root: Path, files: list[str], plan: Plan) -> list[str]:
    """迁移后标记块外仍留着的旧名：迁移不改，列进汇报交给 /rulemason。"""
    hits = check.residue_hits(root, files, lambda rel: plan.text(root, rel))
    # 本次计划要删的文件（如取消 Claude Code 时的 CLAUDE.md）不再报残留
    return [f"{rel} 标记块外仍有 {'、'.join(found)}：迁移不改，请运行 /{NAME} 处理" for rel, found in hits if rel not in plan.deletes]
