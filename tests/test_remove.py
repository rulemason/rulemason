"""rulemason remove 的测试：卸载后副本、清单与标记块不在，lint 改到项目 lint/ 且结果不变，手改与项目内容保留，预检与只看计划不写文件。"""
from __future__ import annotations

import pytest
import yaml
from conftest import REACT_PACKAGE, commit, git_init, run_cli, snapshot, write

from rulemason import check, init, remove, shared

PY_PROJECT = {
    "openspec/config.yaml": "schema: spec-driven\n# 项目注释\ncontext: |\n  项目说明\n",
    "pyproject.toml": '[project]\nname = "x"\n',
    "uv.lock": "",
    "app/main.py": "x = 1\n",
    "web/package.json": REACT_PACKAGE,
    "web/eslint.config.mjs": "export default [\n];\n",
}


@pytest.fixture
def joined(tmp_path):
    """Python + React 项目，用 claude 与 opencode 接入后已提交。"""
    root = tmp_path / "proj"
    git_init(root)
    for rel, text in PY_PROJECT.items():
        write(root, rel, text)
    assert init.run(root, "claude,opencode", True) == 0
    commit(root)
    return root


# ---------- 1. 共用函数 ----------

def test_drop_block_collapses_blank_lines():
    text = "# x\n\n## Code style\n\n<!-- rulemason:code-style -->\n正文\n<!-- /rulemason:code-style -->\n\n项目自己的样板\n"
    assert init.drop_block(text, "code-style") == "# x\n\n## Code style\n\n项目自己的样板\n"
    assert init.drop_block("<!-- rulemason:claude -->\nx\n<!-- /rulemason:claude -->\n", "claude") == ""
    assert init.drop_block("没有块\n", "claude") == "没有块\n"


def test_shared_lint_refs_resolve_from_config_dir(joined):
    text = (joined / "web/eslint.config.mjs").read_text(encoding="utf-8")
    assert check.eslint_shared_refs(joined, "web/eslint.config.mjs", text) == ["../.rulemason/lint/eslint-base.mjs"]
    assert check.ruff_shared_refs(joined, "ruff.toml", 'extend = ".rulemason/lint/ruff-base.toml"\n') == [".rulemason/lint/ruff-base.toml"]
    assert check.ruff_shared_refs(joined, "ruff.toml", 'extend = "other.toml"\n') == []


@pytest.mark.parametrize(("text", "expected"), [
    ('{"instructions": [\n    ".rulemason/a.md",\n    "own.md"\n  ]}', '{"instructions": [\n    "own.md"\n  ]}'),
    ('{"instructions": [".rulemason/a.md", "own.md"]}', '{"instructions": ["own.md"]}'),
    ('{"instructions": [".rulemason/a.md"]}', '{"instructions": []}'),
])
def test_remove_instructions_shapes(text, expected):
    assert remove.remove_instructions(text, [".rulemason/a.md"]) == expected


def test_remove_instructions_declines_when_unsafe():
    assert remove.remove_instructions('{"instructions": [".rulemason/a.md", // 注释\n]}', [".rulemason/a.md"]) is None


# ---------- 2. 卸载结果 ----------

def test_remove_fresh_project(joined):
    assert remove.run(joined, yes=True) == 0
    for rel in (".rulemason", ".rulemason.yaml", ".claude/skills/rulemason", ".agents/skills/rulemason", "opencode.jsonc"):
        assert not (joined / rel).exists(), rel
    assert (joined / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"    # Claude Code 仍读项目指令
    agents = (joined / "AGENTS.md").read_text(encoding="utf-8")
    assert "rulemason:" not in agents
    assert "## Code style" in agents and "## 红线（不可违反）" in agents       # 块外的标题与内容不动
    config = yaml.safe_load((joined / "openspec/config.yaml").read_text(encoding="utf-8"))
    assert "operations" not in config and config["rules"] and config["context"] == "项目说明\n"
    assert (joined / "openspec/config.yaml").read_text(encoding="utf-8").startswith(PY_PROJECT["openspec/config.yaml"])
    assert (joined / "app/main.py").read_text(encoding="utf-8") == "x = 1\n"
    assert check.run(joined)[0].splitlines()[0] == "接入：运行 rulemason init"


def test_lint_moves_to_project_dir(joined):
    ruff_copy = (joined / ".rulemason/lint/ruff-base.toml").read_text(encoding="utf-8")
    eslint_copy = (joined / ".rulemason/lint/eslint-base.mjs").read_text(encoding="utf-8")
    assert remove.run(joined, yes=True) == 0
    assert (joined / "lint/ruff-base.toml").read_text(encoding="utf-8") == ruff_copy
    assert (joined / "lint/eslint-base.mjs").read_text(encoding="utf-8") == eslint_copy
    assert 'extend = "lint/ruff-base.toml"' in (joined / "ruff.toml").read_text(encoding="utf-8")
    assert 'from "../lint/eslint-base.mjs"' in (joined / "web/eslint.config.mjs").read_text(encoding="utf-8")


def test_hand_edited_copy_is_kept(joined, capsys):
    write(joined, ".rulemason/rules/code-style.md", "改过\n")
    assert remove.run(joined, yes=True) == 0
    assert (joined / ".rulemason/rules/code-style.md").read_text(encoding="utf-8") == "改过\n"
    assert ".rulemason/rules/code-style.md 被手改过" in capsys.readouterr().out
    assert not (joined / ".rulemason/rules/python.md").exists()


def test_changed_operations_are_only_reported(joined, capsys):
    config = joined / "openspec/config.yaml"
    write(joined, "openspec/config.yaml", config.read_text(encoding="utf-8").replace("写代码前与写完代码后", "写代码前后"))
    assert remove.run(joined, yes=True) == 0
    assert "operations" in yaml.safe_load(config.read_text(encoding="utf-8"))
    assert "operations 与 init 追加时不同" in capsys.readouterr().out


def test_own_opencode_config_keeps_other_entries(joined):
    (joined / "opencode.jsonc").unlink()
    write(joined, ".opencode/opencode.jsonc", '{\n  "model": "x",\n  "instructions": [\n    "docs/own.md",\n    ".rulemason/rules/code-style.md"\n  ]\n}\n')
    assert remove.run(joined, yes=True) == 0
    assert (joined / ".opencode/opencode.jsonc").read_text(encoding="utf-8") == '{\n  "model": "x",\n  "instructions": [\n    "docs/own.md"\n  ]\n}\n'


def test_project_content_is_listed_not_removed(joined, capsys):
    assert remove.run(joined, plan_only=True) == 0
    out = capsys.readouterr().out
    for item in ("产物写法规则（rules）", "openspec/specs/workflow-gates/spec.md", "AGENTS.md 的项目简介、命令表与红线", "lint/ruff-base.toml：由 .rulemason/lint/ruff-base.toml 移来"):
        assert item in out, item


# ---------- 3. 预检与只看计划 ----------

def test_plan_only_and_non_interactive_write_nothing(joined, monkeypatch):
    monkeypatch.setattr(remove, "interactive", lambda: False)
    before = snapshot(joined)
    assert remove.run(joined, plan_only=True) == 0
    assert remove.run(joined) == 2
    assert snapshot(joined) == before


def test_lint_conflict_stops(joined, capsys):
    write(joined, "lint/ruff-base.toml", "# 项目自己的\n")
    before = snapshot(joined)
    assert remove.run(joined, yes=True) == 1
    assert "lint/ruff-base.toml 已存在且内容与" in capsys.readouterr().out
    assert snapshot(joined) == before


@pytest.mark.parametrize("rulekit_manifest", [False, True])
def test_stops_without_writing_when_not_joined(tmp_path, rulekit_manifest, capsys):
    root = tmp_path / "proj"
    write(root, "app/main.py", "x = 1\n")
    if rulekit_manifest:
        write(root, ".rulekit.yaml", 'version: 1\ntools: [claude]\nrulekit: 0.5.2\nfiles: {}\n')      # rulekit 0.5 遗留文件：不识别，同样算没有接入
    before = snapshot(root)
    assert remove.run(root, yes=True) == 1
    assert snapshot(root) == before
    out = capsys.readouterr().out
    assert "没有接入" in out and "迁移" not in out


def test_source_repo_stops(capsys):
    assert remove.run(shared.SOURCE_ROOT, plan_only=True) == 1
    assert "仓库本身" in capsys.readouterr().out


def test_cli_remove(joined, monkeypatch):
    monkeypatch.chdir(joined)
    assert run_cli("remove", "--plan") == 0
    assert run_cli("remove", "--yes") == 0
    assert not (joined / ".rulemason.yaml").exists()


def test_claude_md_keeps_project_content_and_agents_import(joined):
    claude = joined / "CLAUDE.md"
    write(joined, "CLAUDE.md", claude.read_text(encoding="utf-8") + "\n## 项目自己的说明\n")
    assert remove.run(joined, yes=True) == 0
    text = claude.read_text(encoding="utf-8")
    assert text.startswith("@AGENTS.md\n") and "## 项目自己的说明" in text and "rulemason:" not in text


# ---------- 4. 边界（审查补充） ----------

def test_pyproject_ruff_with_single_quotes(joined):
    (joined / "ruff.toml").unlink()
    write(joined, "pyproject.toml", "[project]\nname = 'x'\n\n[tool.ruff]\nextend = '.rulemason/lint/ruff-base.toml'\n")
    assert remove.run(joined, yes=True) == 0
    assert "extend = 'lint/ruff-base.toml'" in (joined / "pyproject.toml").read_text(encoding="utf-8")


def test_unrecognized_lint_reference_keeps_copies(joined, capsys):
    (joined / "ruff.toml").unlink()
    write(joined, "pyproject.toml", '[tool.other]\nextend = "x"\n\n[tool.ruff]\nextend = ".rulemason/lint/ruff-base.toml"\n')
    assert remove.run(joined, yes=True) == 0
    assert (joined / ".rulemason/lint/ruff-base.toml").is_file()        # 还被引用，不能删
    assert not (joined / ".rulemason.yaml").exists()
    assert "仍引用 .rulemason/lint/" in capsys.readouterr().out


def test_identical_lint_target_is_reused(joined):
    write(joined, "lint/ruff-base.toml", (joined / ".rulemason/lint/ruff-base.toml").read_text(encoding="utf-8"))
    assert remove.run(joined, yes=True) == 0
    assert not (joined / ".rulemason").exists()


def test_lint_target_directory_stops(joined):
    (joined / "lint/ruff-base.toml").mkdir(parents=True)
    before = snapshot(joined)
    assert remove.run(joined, yes=True) == 1
    assert snapshot(joined) == before


def test_unpaired_agents_block_is_only_reported(joined, capsys):
    agents = joined / "AGENTS.md"
    write(joined, "AGENTS.md", agents.read_text(encoding="utf-8") + "<!-- rulemason:code-style -->\n")
    text = agents.read_text(encoding="utf-8")
    assert remove.run(joined, yes=True) == 0
    assert agents.read_text(encoding="utf-8") == text
    assert "AGENTS.md：rulemason:code-style 标记块不成对；卸载时未删除" in capsys.readouterr().out


def test_operations_removed_with_following_content_kept(joined):
    config = joined / "openspec/config.yaml"
    write(joined, "openspec/config.yaml", config.read_text(encoding="utf-8") + "\n# 项目后来加的\nextra: 1\n")
    text = config.read_text(encoding="utf-8")
    assert remove.run(joined, yes=True) == 0
    assert config.read_text(encoding="utf-8") == text.replace(init.operations_section(joined), "\n", 1)
    assert yaml.safe_load(config.read_text(encoding="utf-8"))["extra"] == 1


def test_manifest_is_deleted_last_and_outside_paths_kept(joined, capsys):
    manifest = shared.read_manifest(joined)
    manifest["files"]["app/main.py"] = shared.sha256_file(joined / "app/main.py")    # 写错或被篡改的清单
    write(joined, ".rulemason.yaml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
    plan = remove.build_removal(joined, manifest)
    assert plan.deletes[-1] == ".rulemason.yaml"
    assert "app/main.py" not in plan.deletes
    assert remove.run(joined, yes=True) == 0
    assert (joined / "app/main.py").is_file()


def test_claude_md_with_own_agents_import_is_not_duplicated(joined):
    claude = joined / "CLAUDE.md"
    write(joined, "CLAUDE.md", "@AGENTS.md\n\n" + claude.read_text(encoding="utf-8"))
    assert remove.run(joined, yes=True) == 0
    assert claude.read_text(encoding="utf-8").count("@AGENTS.md") == 1


def test_claude_md_symlink_to_agents_is_left_alone(joined):
    claude = joined / "CLAUDE.md"
    claude.unlink()
    claude.symlink_to("AGENTS.md")
    assert remove.run(joined, yes=True) == 0
    assert claude.is_symlink()
    assert "rulemason:" not in (joined / "AGENTS.md").read_text(encoding="utf-8")


def test_chain_tail_reference_moves_to_project_lint(joined):
    write(joined, "ruff.toml", 'extend = "config/ruff-shared.toml"\n')
    write(joined, "config/ruff-shared.toml", 'extend = "../.rulemason/lint/ruff-base.toml"\n')
    copy = (joined / ".rulemason/lint/ruff-base.toml").read_text(encoding="utf-8")
    assert remove.run(joined, yes=True) == 0
    assert (joined / "ruff.toml").read_text(encoding="utf-8") == 'extend = "config/ruff-shared.toml"\n'
    assert (joined / "config/ruff-shared.toml").read_text(encoding="utf-8") == 'extend = "../lint/ruff-base.toml"\n'
    assert (joined / "lint/ruff-base.toml").read_text(encoding="utf-8") == copy


def test_remove_in_subdirectory_of_unjoined_repo_stops(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    git_init(repo)
    write(repo, "web/main.py", "x = 1\n")
    monkeypatch.chdir(repo / "web")
    assert run_cli("remove", "--yes") == 1
    assert f"判断的项目根：{(repo / 'web').resolve()}" in capsys.readouterr().out
