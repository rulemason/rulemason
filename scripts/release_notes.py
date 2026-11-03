"""发版时生成 GitHub Release 说明：取上一个 v* tag 到本 tag 之间的 feat / fix / docs 提交标题，分组输出 Markdown。"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/rulemason/rulemason"
GROUPS = {"feat": "新功能", "fix": "修复", "docs": "文档"}   # 输出顺序即分组顺序
SUBJECT = re.compile(rf"^({'|'.join(GROUPS)})(?:\([^)]*\))?: (.+)$")
TRAILING_NOTE = re.compile(r"(?:（[^（）]*）)?\s*(?:\(#\d+\))?$")   # 末尾「（change 名，vX）」与 squash 合入加的「(#PR号)」只对开发者有意义


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def previous_tag(cwd: Path, tag: str) -> str | None:
    """返回本 tag 之前的上一个 v* tag；本 tag 是第一个时返回 None。"""
    tags = git(cwd, "tag", "--list", "v*", "--sort=-v:refname").split()
    if tag not in tags:
        raise ValueError(f"找不到 tag {tag}")
    rest = tags[tags.index(tag) + 1:]
    return rest[0] if rest else None


def grouped(subjects: list[str]) -> dict[str, list[str]]:
    """把提交标题按类型分组；不属于 feat / fix / docs 的丢弃，只返回有内容的分组。"""
    groups: dict[str, list[str]] = {}
    for subject in subjects:
        match = SUBJECT.match(subject.strip())
        if not match:
            continue
        text = TRAILING_NOTE.sub("", match.group(2)).strip()
        groups.setdefault(match.group(1), []).append(text)
    return {kind: groups[kind] for kind in GROUPS if kind in groups}


def render(tag: str, prev: str | None, subjects: list[str]) -> str:
    groups = grouped(subjects)
    parts = [f"## {GROUPS[kind]}\n\n" + "\n".join(f"- {item}" for item in items) for kind, items in groups.items()]
    if not parts:
        parts.append("本版本没有面向用户的改动。")
    parts.append("## 升级\n\n```bash\nuv tool upgrade rulemason\n```")
    if prev:
        parts.append(f"完整记录：[{prev}...{tag}]({REPO_URL}/compare/{prev}...{tag})")
    return "\n\n".join(parts) + "\n"


def notes(cwd: Path, tag: str) -> str:
    # 1. 定范围：上一个 tag 到本 tag；没有上一个 tag 时从第一个提交开始
    prev = previous_tag(cwd, tag)
    span = f"{prev}..{tag}" if prev else tag
    # 2. 取提交标题，分组渲染
    subjects = git(cwd, "log", "--format=%s", span).splitlines()
    return render(tag, prev, subjects)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("用法：python scripts/release_notes.py <tag>")
    print(notes(Path.cwd(), sys.argv[1]), end="")
