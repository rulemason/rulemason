"""从 rulekit 0.5 格式迁移的测试：迁移结果与直接接入一致、旧副本被改时停止、旧名残留只报告、update 与 check 的提示。"""
from __future__ import annotations

import json
import shutil

import pytest
import yaml
from conftest import commit, git_init, snapshot, write

from rulemason import check, init, shared, update

PY_PROJECT = {
    "openspec/config.yaml": "schema: spec-driven\ncontext: |\n  项目说明\n",
    "pyproject.toml": '[project]\nname = "x"\n',
    "uv.lock": "",
    "tests/test_x.py": "def test_x():\n    assert True\n",
    "app/main.py": "x = 1\n",
    "tools/ruff.toml": "# 工具脚本的 ruff 配置\n",                  # 子目录的 ruff 配置：继承路径是 ../.rulemason/
    "web/eslint.config.mjs": "export default [\n];\n",
}
ESLINT = "web/eslint.config.mjs"
TOOLS = "claude,opencode"
RESIDUE_LINE = "额外步骤：发布前跑 `jev-judge --change <name>`。\n"


def _old_path(rel: str) -> str:
    return rel.replace(".rulemason/", ".rulekit/").replace("skills/rulemason", "skills/rulekit")


def _to_rulekit(root) -> None:
    """把刚用 rulemason 接入的项目改写成 rulekit 0.5.2 的样子：旧路径、旧标记、旧清单。"""
    manifest = shared.read_manifest(root)
    record = {}
    for rel in manifest["files"]:
        old = _old_path(rel)
        (root / old).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(root / rel, root / old)
        record[old] = shared.sha256_file(root / old)
    for rel in ("AGENTS.md", "CLAUDE.md", "tools/ruff.toml", "opencode.jsonc", ESLINT, check.WORKFLOW_SPEC):
        text = (root / rel).read_text(encoding="utf-8").replace("rulemasonBase", "rulekitBase")   # rulekit 写的 ESLint 变量名
        (root / rel).write_text(text.replace("rulemason:", "rulekit:").replace(".rulemason/", ".rulekit/"), encoding="utf-8")
    old_manifest = {"version": 1, "owner-note": "keep", "tools": manifest["tools"], "rulekit": "0.5.2", "files": record}
    write(root, ".rulekit.yaml", yaml.safe_dump(old_manifest, allow_unicode=True, sort_keys=False))
    (root / ".rulemason.yaml").unlink()
    for d in (".rulemason", ".claude/skills/rulemason", ".agents/skills/rulemason"):
        shutil.rmtree(root / d, ignore_errors=True)


def _new_project(root):
    git_init(root)
    for rel, text in PY_PROJECT.items():
        write(root, rel, text)
    commit(root)
    assert init.run(root, TOOLS, True) == 0
    return root


@pytest.fixture
def pair(tmp_path):
    """(rulekit 0.5 格式的项目, 直接用 rulemason 接入的同一项目)，都已提交。"""
    fresh = _new_project(tmp_path / "fresh/proj")
    commit(fresh)
    old = _new_project(tmp_path / "old/proj")
    _to_rulekit(old)
    commit(old)
    return old, fresh


# ---------- 1. 迁移结果与直接接入一致 ----------

def test_migration_matches_fresh_init(pair):
    old, fresh = pair
    assert init.run(old, TOOLS, True) == 0
    assert not (old / ".rulekit.yaml").exists() and not (old / ".rulekit").exists()
    assert not (old / ".claude/skills/rulekit").exists() and not (old / ".agents/skills/rulekit").exists()
    migrated, direct = snapshot(old), snapshot(fresh)
    # ESLint 配置只换路径前缀，rulekit 起的变量名不动，所以与直接接入只差这个名字
    assert migrated.pop(ESLINT) == direct.pop(ESLINT).replace("rulemasonBase", "rulekitBase")
    assert migrated == direct | {".rulemason.yaml": migrated[".rulemason.yaml"]}
    manifest = shared.read_manifest(old)
    assert manifest["files"] == shared.read_manifest(fresh)["files"]
    assert manifest["tools"] == ["opencode", "claude"] and manifest["owner-note"] == "keep"
    assert manifest["rulemason"] == shared.__version__ and "rulekit" not in manifest
    assert 'extend = "../.rulemason/lint/ruff-base.toml"' in (old / "tools/ruff.toml").read_text(encoding="utf-8")
    assert 'from "../.rulemason/lint/eslint-base.mjs"' in (old / ESLINT).read_text(encoding="utf-8")


def test_migration_is_one_confirmed_plan(pair, monkeypatch, capsys):
    old, _ = pair
    before = snapshot(old)
    monkeypatch.setattr(init, "interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert init.run(old, TOOLS, False) == 0
    out = capsys.readouterr().out
    assert ".rulekit.yaml" in out and ".rulemason.yaml" in out and "已取消" in out
    assert snapshot(old) == before


# ---------- 2. 旧副本被手改时停止 ----------

def test_changed_old_copy_stops_migration(pair, capsys):
    old, _ = pair
    path = old / ".rulekit/rules/code-style.md"
    path.write_text(path.read_text(encoding="utf-8") + "手改\n", encoding="utf-8")
    before = snapshot(old)
    assert init.run(old, TOOLS, True) == 1
    assert ".rulekit/rules/code-style.md" in capsys.readouterr().out
    assert snapshot(old) == before


# ---------- 3. 标记块外的旧名只报告 ----------

def test_residue_outside_blocks_is_reported_not_changed(pair, capsys):
    old, _ = pair
    agents = old / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + RESIDUE_LINE, encoding="utf-8")
    commit(old)
    assert init.run(old, TOOLS, True) == 0
    out = capsys.readouterr().out
    assert "AGENTS.md 标记块外仍有 jev-judge" in out
    assert agents.read_text(encoding="utf-8").endswith(RESIDUE_LINE)
    report, stage = check.collect(old)
    assert dict(report.findings)[check.RESIDUE_FINDING] == ["AGENTS.md 仍有 jev-judge"]
    assert stage.line == "补项目信息：在 AI 工具中运行 /rulemason 处理旧名残留" and check.exit_code(report) == 1


def test_residue_cleared_passes(pair):
    old, _ = pair
    assert init.run(old, TOOLS, True) == 0
    report, _ = check.collect(old)
    assert dict(report.findings)[check.RESIDUE_FINDING] == []
    assert check.exit_code(report) == 0


def test_residue_ignores_archive_and_gitignore_is_checked(pair):
    old, _ = pair
    assert init.run(old, TOOLS, True) == 0
    write(old, "openspec/changes/archive/2026-11-01-x/design.md", "用 jev-judge 审 .rulekit/ 副本\n")
    write(old, ".gitignore", ".claude/*\n!.claude/skills/\n.claude/skills/*\n!.claude/skills/rulekit/\n")
    report, _ = check.collect(old)
    assert dict(report.findings)[check.RESIDUE_FINDING] == [".gitignore 仍有 skills/rulekit"]


# ---------- 4. update 与 check 遇到旧格式 ----------

def test_update_refuses_old_format(pair, capsys):
    old, _ = pair
    before = snapshot(old)
    assert update.run(old) == 1
    assert "rulemason init 迁移格式" in capsys.readouterr().out
    assert snapshot(old) == before


def test_check_reports_old_format(pair):
    old, _ = pair
    report, stage = check.collect(old)
    assert stage.line == "接入：运行 rulemason init 迁移格式" and stage.code == "migrate"
    assert check.exit_code(report) == 1


# ---------- 5. 删除范围、无效旧清单、迁移时换工具 ----------

def test_paths_outside_old_copies_are_never_deleted(pair, capsys):
    old, _ = pair
    data = yaml.safe_load((old / ".rulekit.yaml").read_text(encoding="utf-8"))
    data["files"]["app/main.py"] = shared.sha256_file(old / "app/main.py")    # 写错或被篡改的旧清单
    data["files"]["../outside.txt"] = "0" * 64
    write(old, ".rulekit.yaml", yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    write(old, ".rulekit/extra.md", "没记录的文件\n")
    commit(old)
    assert init.run(old, TOOLS, True) == 0
    out = capsys.readouterr().out
    assert (old / "app/main.py").read_text(encoding="utf-8") == "x = 1\n"
    assert "旧副本目录以外的路径，迁移不删：app/main.py、../outside.txt" in out
    assert (old / ".rulekit/extra.md").is_file() and "迁移不删，请自行处理：.rulekit/extra.md" in out


def test_invalid_old_manifest_stops(pair, capsys):
    old, _ = pair
    write(old, ".rulekit.yaml", "version: 1\ntools: [nope]\n")
    before = snapshot(old)
    assert init.run(old, TOOLS, True) == 1
    assert ".rulekit.yaml 有不支持的工具" in capsys.readouterr().out
    assert snapshot(old) == before


def test_tools_can_change_during_migration(pair):
    old, _ = pair
    assert init.run(old, "claude", True) == 0
    assert shared.read_manifest(old)["tools"] == ["claude"]
    assert (old / ".claude/skills/rulemason/SKILL.md").is_file()
    assert not (old / ".agents/skills/rulemason").exists() and not (old / ".agents/skills/rulekit").exists()


def test_unrecorded_old_files_reported_without_git(pair, capsys):
    old, _ = pair
    shutil.rmtree(old / ".git")                        # 没有 git 时列文件会跳过 .rulekit/，迁移要自己找
    write(old, ".rulekit/extra.md", "没记录的文件\n")
    assert init.run(old, TOOLS, True) == 0
    assert "迁移不删，请自行处理：.rulekit/extra.md" in capsys.readouterr().out
    assert (old / ".rulekit/extra.md").is_file()


def test_migration_and_cancelling_claude_in_one_init(pair):
    old, _ = pair
    assert init.run(old, "opencode", True) == 0                   # 迁移的同时取消 Claude Code
    assert not (old / "CLAUDE.md").exists()
    assert not (old / ".claude/skills/rulemason").exists() and not (old / ".claude/skills/rulekit").exists()


# ---------- init --plan 的迁移计划（agent-io） ----------

def test_plan_json_lists_migration(pair, capsys):
    old, _ = pair
    before = snapshot(old)
    assert init.run(old, None, False, plan_only=True, as_json=True) == 0
    data = json.loads(capsys.readouterr().out)
    assert ".rulekit.yaml" in data["deletes"] and ".rulekit/rules/code-style.md" in data["deletes"]
    assert ".rulemason.yaml" in [w["path"] for w in data["writes"]]
    assert sorted(data["tools"]) == sorted(TOOLS.split(","))
    assert snapshot(old) == before


def test_plan_stops_when_old_copy_changed(pair, capsys):
    old, _ = pair
    path = old / ".rulekit/rules/code-style.md"
    path.write_text(path.read_text(encoding="utf-8") + "手改\n", encoding="utf-8")
    before = snapshot(old)
    assert init.run(old, None, False, plan_only=True) == 1
    assert snapshot(old) == before
