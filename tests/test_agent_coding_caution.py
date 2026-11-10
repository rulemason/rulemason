"""编码审慎规矩分发：含新增原则，且正文不含第三方来源痕迹。"""
from __future__ import annotations

from pathlib import Path

from rulemason import init, shared

_FORBIDDEN = (
    "aa3bf0e",
    "gsd-core",
    "get-shit-done",
    "pm-skills",
    "Product-Manager",
    "anti-slop",
    "karpathy",
    "autocorrect",
    "superpowers",
    "github.com/",
)


def test_init_distributes_coding_caution_principles(tmp_path: Path) -> None:
    from conftest import commit, git_init, write

    root = tmp_path / "proj"
    git_init(root)
    write(root, "go.mod", "module x\n")
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    commit(root)
    assert init.run(root, "claude", True) == 0
    rule = root / ".rulemason/rules/agent-coding-caution.md"
    body = rule.read_text(encoding="utf-8")
    for phrase in ("可测先行", "先根因再修", "完成须有当次证据", "审阅反馈先核实"):
        assert phrase in body, phrase
    for needle in _FORBIDDEN:
        assert needle not in body, needle
    assert ".rulemason/rules/agent-coding-caution.md" in shared.read_manifest(root)["files"]
