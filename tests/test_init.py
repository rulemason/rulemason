"""rulemason init 的测试：预检与 openspec、选工具、生成副本、标记块、补配置、命令表、计划确认与重复运行。"""
from __future__ import annotations

import builtins
import datetime
import json
import os
import shutil
import stat

import pytest
import yaml
from conftest import (
    REACT_PACKAGE,
    commit,
    git,
    git_init,
    project_folder,
    run_cli,
    snapshot,
    write,
)

from rulemason import check, init, shared, update

PY_PROJECT = {
    "openspec/config.yaml": "schema: spec-driven\n# 项目注释\ncontext: |\n  项目说明\n",
    "pyproject.toml": '[project]\nname = "x"\n',
    "uv.lock": "",
    "tests/test_x.py": "def test_x():\n    assert True\n",
    "app/main.py": "x = 1\n",
}


# ---------- 1. 工具 ----------

def _files(root) -> set[str]:
    """项目里的全部文件（不含 .git/）。"""
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


def _answers(monkeypatch, *answers: str) -> list[str]:
    """把 input() 换成依次返回 answers；记录提问。"""
    queue, asked = list(answers), []

    def fake(prompt=""):
        asked.append(prompt)
        if not queue:
            raise AssertionError(f"多问了一句：{prompt}")
        return queue.pop(0)

    monkeypatch.setattr(builtins, "input", fake)
    return asked


@pytest.fixture
def tty(monkeypatch):
    monkeypatch.setattr(init, "interactive", lambda: True)


@pytest.fixture
def project(tmp_path):
    """有 git、openspec、uv 管理的 Python 项目，已提交。"""
    root = tmp_path / "proj"
    git_init(root)
    for rel, text in PY_PROJECT.items():
        write(root, rel, text)
    commit(root)
    return root


def _init(root, tools="claude", yes=True) -> int:
    return init.run(root, tools, yes)


@pytest.fixture
def fake_openspec(tmp_path, monkeypatch):
    """替身 openspec：把参数写进项目外的日志；FAKE_OPENSPEC_FAIL=1 时失败且不建目录。"""
    bin_dir = tmp_path / "bin"
    log = tmp_path / "openspec-args.txt"
    script = bin_dir / "openspec"
    write(bin_dir, "openspec", '#!/bin/sh\necho "$@" > "$FAKE_OPENSPEC_LOG"\n[ "$FAKE_OPENSPEC_FAIL" = 1 ] && exit 3\nmkdir -p openspec\nprintf \'schema: spec-driven\\ncontext: |\\n  Language: zh-CN\\n\' > openspec/config.yaml\n')
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_OPENSPEC_LOG", str(log))
    return log


# ---------- 2. 预检与 openspec（4.1） ----------

def test_new_dir_agrees_to_openspec_init(tmp_path, tty, fake_openspec, monkeypatch, capsys):
    root = tmp_path / "fresh"
    write(root, "main.py", "x = 1\n")
    _answers(monkeypatch, "y", "y")
    launched, real_run = [], init.subprocess.run

    def spy(cmd, **kwargs):
        launched.append(cmd)
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(init.subprocess, "run", spy)

    assert init.run(root, "claude,codex", False) == 0

    openspec_cmd = next(cmd for cmd in launched if cmd[1:3] == ["init", "--tools"])
    assert openspec_cmd[0] == init.shutil.which("openspec")    # 以 which 找到的完整路径启动：Windows 上是 openspec.cmd
    args = fake_openspec.read_text(encoding="utf-8").split()
    assert args[:3] == ["init", "--tools", "claude,codex"] and args[3:] == ["--language", "zh-CN"]
    assert (root / "AGENTS.md").is_file() and (root / ".rulemason.yaml").is_file()
    assert "没有 git" in capsys.readouterr().out


def test_declining_openspec_init_installs_rules_layer_only(tmp_path, tty, fake_openspec, monkeypatch, capsys):
    root = tmp_path / "fresh"
    write(root, "main.py", "x = 1\n")
    _answers(monkeypatch, "n", "y")

    assert init.run(root, "claude", False) == 0
    assert not fake_openspec.exists() and not (root / "openspec").exists()
    assert (root / ".rulemason/rules/code-style.md").is_file() and (root / ".rulemason.yaml").is_file()
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "还没有接 OpenSpec" in agents and ".rulemason/rules/workflow-gates.md" in agents
    assert "需要 OpenSpec" in capsys.readouterr().out


def test_missing_openspec_command_installs_rules_layer_only(tmp_path, monkeypatch, capsys):
    root = tmp_path / "fresh"
    write(root, "main.py", "x = 1\n")
    monkeypatch.setattr(init.shutil, "which", lambda name: None)

    assert _init(root) == 0
    out = capsys.readouterr().out
    assert "npm install -g @fission-ai/openspec" in out and "需要 OpenSpec" in out
    assert not (root / "openspec").exists() and (root / ".rulemason/rules/code-style.md").is_file()
    assert not (root / "openspec/specs/workflow-gates/spec.md").exists()


def test_failed_openspec_init_stops(tmp_path, tty, fake_openspec, monkeypatch):
    root = tmp_path / "fresh"
    write(root, "main.py", "x = 1\n")
    monkeypatch.setenv("FAKE_OPENSPEC_FAIL", "1")
    _answers(monkeypatch, "y")

    assert init.run(root, "claude", False) == 1
    assert fake_openspec.is_file() and _files(root) == {"main.py"}


def test_refuses_rulemason_repo_itself(capsys):
    before = git(shared.SOURCE_ROOT, "status", "--porcelain")
    assert _init(shared.SOURCE_ROOT) == 1
    assert "rulemason 仓库本身" in capsys.readouterr().out
    assert git(shared.SOURCE_ROOT, "status", "--porcelain") == before


# ---------- 3. 选工具（4.2） ----------

def test_numbered_fallback_marks_detected_dirs_without_prechecking(project, monkeypatch, capsys):
    """读不了单键时退回编号输入：第一次全不勾，只标注检测到的目录；输入编号多选。"""
    (project / ".claude").mkdir()
    (project / ".cursor").mkdir()
    _answers(monkeypatch, "", "9", "4，2")
    assert init.choose_tools(project, None, None) == ["claude", "codex"]
    out = capsys.readouterr().out
    assert "[ ] Claude Code（claude）  检测到" in out and "[ ] Codex（codex）" in out and "[x]" not in out
    assert out.count("至少选一个") == 2                       # 空输入与越界各提示一次


def test_numbered_fallback_prechecks_recorded_tools(project, monkeypatch, capsys):
    _answers(monkeypatch, "")
    assert init.choose_tools(project, {"tools": ["claude", "cursor"]}, None) == ["claude", "cursor"]
    assert "[x] Claude Code" in capsys.readouterr().out


def test_tools_flag_does_not_ask(project, monkeypatch):
    _answers(monkeypatch)                                   # 任何提问都会让测试失败
    assert init.choose_tools(project, None, "codex, claude") == ["claude", "codex"]


def test_non_tty_without_tools_errors(project, monkeypatch):
    monkeypatch.setattr(init, "interactive", lambda: False)
    before = snapshot(project)
    assert init.run(project, None, True) == 2
    assert snapshot(project) == before


# ---------- 4. 生成副本（4.3） ----------

def test_generated_copies_match_shared_source_and_manifest(project):
    assert _init(project, "claude,codex") == 0

    src = shared.shared_root()
    rules = check.copied_rules(project, shared.list_files(project))
    assert rules == [
        "rules/code-style.md",
        "rules/python.md",
        "rules/workflow-gates.md",
        "rules/cjk-typography.md",
        "rules/result-check-contracts.md",
        "rules/prose-hygiene.md",
        "rules/agent-coding-caution.md",
        "rules/product-artifact-caution.md",
        "lint/ruff-base.toml",
    ]
    for rel in rules:
        assert (project / ".rulemason" / rel).read_text(encoding="utf-8") == (src / rel).read_text(encoding="utf-8")
    assert not (project / ".rulemason/rules/react.md").exists() and not (project / ".rulemason/lint/eslint-base.mjs").exists()
    for target in (".claude/skills/rulemason", ".agents/skills/rulemason"):
        for rel in shared.SKILL_FILES:
            assert (project / target / rel).read_bytes() == (src / "skills/rulemason" / rel).read_bytes()
    manifest = shared.read_manifest(project)
    assert manifest["tools"] == ["claude", "codex"] and manifest["rulemason"] == shared.__version__
    assert manifest["files"] == {rel: shared.sha256_file(project / rel) for rel in shared.generated_files(["claude", "codex"], rules)}


# ---------- 5. 标记块（4.4） ----------

def test_existing_agents_content_is_kept_verbatim(project):
    head = "# 我的项目\n\n自写简介。\n\n## Code style\n"
    tail = "\n本项目样板：app/main.py。\n\n## 其他\n\n自写内容。\n"
    write(project, "AGENTS.md", head + tail)
    write(project, "CLAUDE.md", "自写的 Claude 说明\n")

    assert _init(project, "claude,opencode") == 0

    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith(head + "\n<!-- rulemason:code-style -->")
    assert tail in text and ".rulemason/rules/python.md" in text
    assert "## Workflow gates\n\n<!-- rulemason:workflow-gates -->" in text
    claude = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.startswith("自写的 Claude 说明\n\n<!-- rulemason:claude -->\n@AGENTS.md\n")
    assert ".rulemason/rules/workflow-gates.md" in (project / "opencode.jsonc").read_text(encoding="utf-8")


def test_new_agents_from_template_marks_pending(project):
    assert _init(project) == 0
    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith(f"# {project.name}\n") and text.count("待 /rulemason 补充") == 2       # 简介（没有 README）与样板豁免
    assert "## 红线（不可违反）\n\n暂无\n" in text and "判断用的红线规则：暂无（判断未启用；项目红线见上文「红线」一节）" in text


def test_unpaired_markers_leave_file_untouched(project, capsys):
    original = "# x\n\n## Code style\n\n<!-- rulemason:code-style -->\n半个块\n"
    write(project, "AGENTS.md", original)
    assert _init(project) == 0
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == original
    assert "rulemason:code-style 标记块不成对" in capsys.readouterr().out


def test_project_without_python_skips_python_rules(tmp_path):
    root = tmp_path / "web"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    assert _init(root, "claude") == 0
    assert "python.md" not in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "python.md" not in (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert not (root / "ruff.toml").exists()


# ---------- 6. 补配置（4.5） ----------

def test_config_rules_appended_and_context_kept(project):
    base = init.check.base_artifact_rules()
    original = PY_PROJECT["openspec/config.yaml"] + f"rules:\n  proposal:\n    - {base['proposal'][0]}\n    - 项目追加的一条\n"
    write(project, "openspec/config.yaml", original)

    assert _init(project) == 0

    text = (project / "openspec/config.yaml").read_text(encoding="utf-8")
    assert text.startswith(PY_PROJECT["openspec/config.yaml"] + "rules:\n  proposal:\n")
    data = yaml.safe_load(text)
    assert data["context"] == "项目说明\n"
    assert data["rules"]["proposal"] == [base["proposal"][0], "项目追加的一条", base["proposal"][1]]
    assert all(data["rules"][a] == items for a, items in base.items() if a != "proposal")


def test_ruff_select_is_reported_not_changed(project, capsys):
    text = '[project]\nname = "x"\n\n[tool.ruff.lint]\nselect = ["E"]\n'
    write(project, "pyproject.toml", text)
    assert _init(project) == 0
    assert (project / "pyproject.toml").read_text(encoding="utf-8") == text
    assert "pyproject.toml 写了 select" in capsys.readouterr().out
    assert not (project / "ruff.toml").exists()


def test_ruff_and_eslint_configs_gain_inheritance(project):
    write(project, "svc/pyproject.toml", '[tool.ruff.lint.per-file-ignores]\n"cli.py" = ["T201"]\n')
    write(project, "web/eslint.config.mjs", 'import js from "@eslint/js";\n\nexport default [\n  js.configs.recommended,\n];\n')
    assert _init(project) == 0

    ruff = (project / "svc/pyproject.toml").read_text(encoding="utf-8")
    assert ruff.startswith('[tool.ruff]\nextend = "../.rulemason/lint/ruff-base.toml"')
    eslint = (project / "web/eslint.config.mjs").read_text(encoding="utf-8")
    assert eslint.startswith('import rulemasonBase from "../.rulemason/lint/eslint-base.mjs";\nimport js')
    assert "export default [\n  { rules: rulemasonBase },\n  js.configs.recommended," in eslint


def test_existing_workflow_spec_is_reported_not_changed(project, capsys):
    write(project, check.WORKFLOW_SPEC, "# workflow-gates Specification\n\n项目自有内容\n")
    assert _init(project) == 0
    assert (project / check.WORKFLOW_SPEC).read_text(encoding="utf-8") == "# workflow-gates Specification\n\n项目自有内容\n"
    assert "需由 /rulemason 合并" in capsys.readouterr().out


# ---------- 7. 命令表（4.6） ----------

def test_commands_uv_with_tests(project):
    rows = init.detect_commands(project, shared.list_files(project))
    assert rows == {"判断": "可选，未启用", "ruff": "`uv run ruff check .`", "测试": "`uv run pytest`", "前端 lint": "无，跳过", "文案检查": "可选，未启用"}


@pytest.mark.parametrize(("rel", "prefix"), [("pyproject.toml", ""), ("api/pyproject.toml", "cd api && ")])
def test_commands_python_without_uv_lock(tmp_path, rel, prefix):
    """没有 uv.lock：ruff 用 uvx 跑，测试命令猜不到，写待确认而不是「无，跳过」。"""
    root = tmp_path / "p"
    write(root, rel, '[project]\nname = "x"\n')
    write(root, "tests/test_x.py", "def test_x():\n    assert True\n")
    rows = init.detect_commands(root, shared.list_files(root))
    assert rows["ruff"] == f"`{prefix}uvx ruff check .`"
    assert rows["测试"] == "待确认：填项目跑测试的命令"


def test_commands_skip_workspace_members(project):
    """uv workspace 成员没有自己的 uv.lock：根目录那条 ruff 已覆盖，不另加 uvx 那条，也不写待确认。"""
    write(project, "packages/a/pyproject.toml", '[project]\nname = "a"\n')
    rows = init.detect_commands(project, shared.list_files(project))
    assert rows["ruff"] == "`uv run ruff check .`"
    assert rows["测试"] == "`uv run pytest`"


def test_commands_nested_pyproject_under_unlocked_root(tmp_path):
    """根目录没有锁文件、下面有示例项目：只认最上层那个目录。"""
    root = tmp_path / "p"
    write(root, "pyproject.toml", '[project]\nname = "x"\n')
    write(root, "examples/demo/pyproject.toml", '[project]\nname = "demo"\n')
    rows = init.detect_commands(root, shared.list_files(root))
    assert rows["ruff"] == "`uvx ruff check .`"
    assert rows["测试"] == init.TESTS_UNKNOWN


def test_commands_sibling_unlocked_dirs_pending_once(tmp_path):
    """平级的两个无锁目录各一条 ruff，「待确认」只写一次。"""
    root = tmp_path / "p"
    write(root, "a/pyproject.toml", '[project]\nname = "a"\n')
    write(root, "b/pyproject.toml", '[project]\nname = "b"\n')
    rows = init.detect_commands(root, shared.list_files(root))
    assert rows["ruff"] == "`cd a && uvx ruff check .`；`cd b && uvx ruff check .`"
    assert rows["测试"] == init.TESTS_UNKNOWN


def test_commands_unlocked_python_beside_frontend_tests(tmp_path):
    """混合仓库：前端识别出了测试，没有锁文件的 Python 也要留一条待确认，免得检查点只跑前端测试。"""
    root = tmp_path / "p"
    write(root, "web/package.json", '{"scripts": {"test": "vitest"}}')
    write(root, "api/pyproject.toml", '[project]\nname = "api"\n')
    rows = init.detect_commands(root, shared.list_files(root))
    assert rows["测试"] == "`cd web && npm run test`；待确认：填项目跑测试的命令"
    assert rows["ruff"] == "`cd api && uvx ruff check .`"


def test_commands_pnpm_scripts(tmp_path):
    root = tmp_path / "p"
    write(root, "web/package.json", '{"scripts": {"lint": "eslint .", "test": "vitest"}}')
    write(root, "web/pnpm-lock.yaml", "")
    rows = init.detect_commands(root, shared.list_files(root))
    assert rows["前端 lint"] == "`cd web && pnpm run lint`" and rows["测试"] == "`cd web && pnpm run test`"
    assert rows["ruff"] == "无，跳过"


def test_commands_nothing_detected(tmp_path):
    root = tmp_path / "p"
    write(root, "README.md", "x\n")
    rows = init.detect_commands(root, shared.list_files(root))
    assert [rows[k] for k in ("ruff", "测试", "前端 lint")] == ["无，跳过"] * 3


def test_existing_command_table_is_not_written(project):
    write(project, "AGENTS.md", "# x\n\n## Workflow gates\n\n| 名称 | 命令 |\n|---|---|\n| ruff | 自定义 |\n")
    assert _init(project) == 0
    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "自动识别，请确认" not in text and "| ruff | 自定义 |" in text


# ---------- 8. 计划与确认（4.7） ----------

def test_rejecting_plan_writes_nothing(project, tty, monkeypatch):
    _answers(monkeypatch, "n")
    before = snapshot(project)
    assert init.run(project, "claude", False) == 0
    assert snapshot(project) == before


@pytest.mark.parametrize(("tools", "hinted"), [("opencode,claude", True), ("claude", False)])
def test_opencode_skill_hint_after_next_step(project, capsys, tools, hinted):
    """接入了 OpenCode 时，收尾的下一步之后补一句 OpenCode 里的叫法。"""
    assert init.run(project, tools, True) == 0
    out = capsys.readouterr().out
    assert (f"{init.NEXT_STEP}\n{shared.OPENCODE_SKILL_HINT}\n" in out) is hinted
    assert out.count(shared.OPENCODE_SKILL_HINT) == (1 if hinted else 0)


def test_clean_worktree_plan_has_no_untouched_line(project, capsys):
    """计划以外没有未提交改动时，不写「其余 0 个未提交改动不变」这句废话。"""
    assert init.run(project, "claude", False, plan_only=True) == 0
    out = capsys.readouterr().out
    assert "## 文件计划" in out and "未提交改动" not in out


def test_untouched_lines_only_when_something_is_dirty(project):
    """摘要与完整清单共用这一行：计划外没有改动时不写，有时写数量。"""
    plan = init.Plan()
    assert init.untouched_lines(project, plan) == []
    write(project, "notes.md", "草稿\n")
    assert init.untouched_lines(project, plan) == ["不会碰：其余 1 个未提交改动不变"]


def test_unrelated_uncommitted_changes_untouched(project, capsys):
    write(project, "app/main.py", "x = 2\n")
    write(project, "notes.md", "草稿\n")
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert "其余 2 个未提交改动不变" in out
    assert out.rstrip().endswith(init.NEXT_STEP)
    assert (project / "app/main.py").read_text(encoding="utf-8") == "x = 2\n"
    assert (project / "notes.md").read_text(encoding="utf-8") == "草稿\n"


# ---------- 9. 重复运行、追加与移除工具（4.8） ----------

def test_second_run_changes_nothing(project, capsys):
    assert _init(project, "claude,opencode,codex") == 0
    commit(project)
    assert _init(project, "claude,opencode,codex") == 0
    assert git(project, "status", "--porcelain") == ""
    assert "没有需要改动的文件" in capsys.readouterr().out


def test_adding_tool_only_adds_its_entry(project):
    _init(project, "claude")
    commit(project)
    _init(project, "claude,cursor")
    changed = {line[3:] for line in git(project, "status", "--porcelain", "--untracked-files=all").splitlines()}
    assert changed == {".rulemason.yaml"} | {f".agents/skills/rulemason/{rel}" for rel in shared.SKILL_FILES}


def test_removing_tool_deletes_untouched_copies_and_keeps_edited(project, capsys):
    _init(project, "claude,codex,opencode")
    write(project, ".claude/skills/rulemason/SKILL.md", "手改\n")

    _init(project, "opencode")

    assert not (project / ".claude/skills/rulemason/templates").exists()
    assert (project / ".claude/skills/rulemason/SKILL.md").read_text(encoding="utf-8") == "手改\n"
    assert ".claude/skills/rulemason/SKILL.md 被手改过" in capsys.readouterr().out
    assert (project / ".agents/skills/rulemason/SKILL.md").is_file()
    assert shared.read_manifest(project)["tools"] == ["opencode"]


# ---------- 10. 审查补充：ruff 表头、无法识别的配置、不安全目标、重复导入 ----------

@pytest.mark.parametrize("header", ["[tool.ruff]", "[tool.ruff]   # 项目自己的说明"])
def test_ruff_header_gets_extend(project, header):
    write(project, "pyproject.toml", f'[project]\nname = "x"\n\n{header}\nline-length = 100\n')
    assert _init(project) == 0
    text = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert f'{header}\nextend = ".rulemason/lint/ruff-base.toml"' in text and "line-length = 100" in text


def test_other_ruff_extend_gets_base_at_chain_tail_and_legacy_eslint_is_reported(project, capsys):
    write(project, "ruff.toml", 'extend = "base.toml"\n')
    write(project, "base.toml", "line-length = 100\n")
    write(project, "web/.eslintrc.json", "{}\n")
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert (project / "ruff.toml").read_text(encoding="utf-8") == 'extend = "base.toml"\n'          # 起点逐字不变
    assert (project / "base.toml").read_text(encoding="utf-8").startswith('extend = ".rulemason/lint/ruff-base.toml"')
    assert "已继承其他 ruff 配置" not in out and "ruff.toml" not in out.split("需要你处理", 1)[1]
    assert "web/.eslintrc.json 是旧格式 .eslintrc" in out and "npx @eslint/migrate-config web/.eslintrc.json" in out
    assert (project / "web/.eslintrc.json").read_text(encoding="utf-8") == "{}\n"


def test_symlinked_dir_pointing_outside_writes_nothing(project, tmp_path, capsys):
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".rulemason").symlink_to(outside, target_is_directory=True)
    before = snapshot(project)

    assert _init(project) == 1

    assert "符号链接或在项目外" in capsys.readouterr().out
    assert list(outside.iterdir()) == []
    assert not (project / "AGENTS.md").exists() and snapshot(project) == before


def test_lone_agents_import_in_claude_md_is_replaced_by_block(project, capsys):
    write(project, "CLAUDE.md", "@AGENTS.md\n\n## 项目自己的说明\n\n先读 README。\n")
    assert _init(project) == 0
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")

    assert text.startswith("<!-- rulemason:claude -->\n@AGENTS.md\n")                # 块放在原来那一行的位置
    assert text.count("@AGENTS.md") == 1
    assert text.endswith("<!-- /rulemason:claude -->\n\n## 项目自己的说明\n\n先读 README。\n")
    assert "块外已导入 AGENTS.md" not in capsys.readouterr().out
    assert _init(project) == 0 and (project / "CLAUDE.md").read_text(encoding="utf-8") == text    # 再跑一次不变


@pytest.mark.parametrize(("claude", "suffix"), [("说明\r\n@AGENTS.md\r\n尾部\r\n", "\r\n尾部\r\n"), ("说明\n\n@AGENTS.md", "")])
def test_lone_agents_import_keeps_its_line_ending(project, claude, suffix):
    write(project, "CLAUDE.md", claude)
    assert _init(project) == 0
    text = (project / "CLAUDE.md").read_bytes().decode("utf-8")
    assert text.count("@AGENTS.md") == 1 and text.endswith("<!-- /rulemason:claude -->" + suffix)


def test_lone_agents_import_with_another_form_is_replaced_and_the_other_reported(project, capsys):
    write(project, "CLAUDE.md", "@AGENTS.md\n\n@./AGENTS.md\n")
    assert _init(project) == 0
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- rulemason:claude -->\n@AGENTS.md\n") and "\n@./AGENTS.md\n" in text
    assert "块外已导入 AGENTS.md" in capsys.readouterr().out


@pytest.mark.parametrize("claude", ["```\n@AGENTS.md\n```\n", "~~~\n@AGENTS.md\n```\n@AGENTS.md\n~~~\n"])
def test_agents_import_inside_code_fence_is_left_alone(project, claude, capsys):
    write(project, "CLAUDE.md", claude)
    assert _init(project) == 0
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith(claude) and text.endswith("<!-- /rulemason:claude -->\n")       # 示例不动，块加在文末
    assert "块外已导入 AGENTS.md" not in capsys.readouterr().out                             # 代码块里的不算导入


def test_lone_agents_import_next_to_fenced_example_is_replaced(project):
    write(project, "CLAUDE.md", "@AGENTS.md\n\n```\n@AGENTS.md\n```\n")
    assert _init(project) == 0
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- rulemason:claude -->\n@AGENTS.md\n") and text.endswith("```\n@AGENTS.md\n```\n")


@pytest.mark.parametrize("claude", ["@./AGENTS.md\n", "@AGENTS.md\n\n@AGENTS.md\n", "  @AGENTS.md\n",
                                    "见 @AGENTS.md\n@AGENTS.md\n"])
def test_other_agents_import_forms_are_still_reported(project, claude, capsys):
    write(project, "CLAUDE.md", claude)
    assert _init(project) == 0
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith(claude) and "<!-- rulemason:claude -->" in text                 # 原行不动，块照常写入
    assert "块外已导入 AGENTS.md" in capsys.readouterr().out


def test_rewrites_keep_crlf_and_mode_and_handle_missing_final_newline(project):
    path = project / "pyproject.toml"
    path.write_bytes(b'[project]\r\nname = "x"\r\n\r\n[tool.ruff.lint]\r\nextend-select = ["E"]\r\n[tool.ruff]')
    path.chmod(0o644)
    write(project, "ruff.toml", "# 只有注释")
    assert _init(project) == 0

    data = path.read_bytes()
    assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b"")
    assert data.count(b"[tool.ruff]") == 1 and stat.S_IMODE(path.stat().st_mode) == 0o644
    assert (project / "ruff.toml").read_text(encoding="utf-8").splitlines()[1].startswith("extend = ")
    assert stat.S_IMODE((project / "AGENTS.md").stat().st_mode) != 0o600


# ---------- 11. 迁移中发现的识别问题（cli-migration-fixes） ----------

def test_english_command_table_header_is_recognized(project):
    write(project, "AGENTS.md", "# x\n\n## Workflow gates\n\n| Name | Command |\n|---|---|\n| ruff | 自定义 |\n")
    assert _init(project) == 0
    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "自动识别，请确认" not in text and "| Name | Command |" in text


def test_equivalent_workflow_requirement_is_not_reported(project, capsys):
    spec = "# workflow-gates Specification\n\n## Requirements\n\n### Requirement: Apply 后自动精简与独立审查\n\n引用 `.rulemason/rules/workflow-gates.md`。\n"
    write(project, check.WORKFLOW_SPEC, spec)
    assert _init(project) == 0
    assert "需由 /rulemason 合并" not in capsys.readouterr().out
    assert (project / check.WORKFLOW_SPEC).read_text(encoding="utf-8") == spec


# ---------- 项目根：在子目录运行与显式路径 ----------


def test_check_in_subdirectory_matches_root(project, monkeypatch, capsys):
    assert _init(project) == 0
    capsys.readouterr()
    monkeypatch.chdir(project)
    root_code = run_cli("check")
    at_root = capsys.readouterr().out
    monkeypatch.chdir(project / "app")
    assert run_cli("check") == root_code
    assert capsys.readouterr().out == at_root


def test_init_in_subdirectory_uses_that_directory(project, monkeypatch, capsys):
    """与 openspec init 一致：找不到清单就在当前目录接入，并写明仓库根与接入整个仓库的做法。"""
    monkeypatch.chdir(project / "app")
    assert run_cli("init", "--tools", "claude", "--yes") == 0
    assert (project / "app/.rulemason.yaml").is_file()
    assert not (project / ".rulemason.yaml").exists() and not (project / ".rulemason").exists()
    hint = f"当前目录在 git 仓库 {project.resolve()} 里；要接入整个仓库，到仓库根运行，或运行 rulemason init {project.resolve()}"
    assert hint in capsys.readouterr().out


def test_plan_shows_repo_root_hint_but_json_fields_stay(project, monkeypatch, capsys):
    monkeypatch.chdir(project / "app")
    assert run_cli("init", "--tools", "claude", "--plan") == 0
    assert f"当前目录在 git 仓库 {project.resolve()} 里" in capsys.readouterr().out
    assert run_cli("init", "--tools", "claude", "--plan", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["root"] == str((project / "app").resolve()) and "tips" not in data


def test_new_directory_under_workspace_repo_stays_local(tmp_path, tty, fake_openspec, monkeypatch, capsys):
    """工作区目录是装着多个项目的 git 仓库，在其下自己还不是仓库的新目录里接入：rulemason 与 openspec 都写在新目录。"""
    workspace = tmp_path / "ws"
    git_init(workspace)
    write(workspace, "other/README.md", "# 别的项目\n")
    write(workspace, "rm-test/main.py", "x = 1\n")
    before = sorted(p.name for p in workspace.iterdir())
    monkeypatch.chdir(workspace / "rm-test")
    _answers(monkeypatch, "y", "y")

    assert run_cli("init", "--tools", "claude") == 0

    assert (workspace / "rm-test/.rulemason.yaml").is_file() and (workspace / "rm-test/openspec/config.yaml").is_file()
    assert f"当前目录在 git 仓库 {workspace.resolve()} 里" in capsys.readouterr().out
    assert sorted(p.name for p in workspace.iterdir()) == before                # 工作区目录里没有新文件


def test_explicit_path_gets_no_repo_root_hint(project, monkeypatch, capsys):
    """在仓库根运行 rulemason init app：当前目录就是仓库根，「当前目录在 git 仓库……」说不通，不提示。"""
    monkeypatch.chdir(project)
    assert run_cli("init", "app", "--tools", "claude", "--yes") == 0
    assert (project / "app/.rulemason.yaml").is_file()
    assert "当前目录在 git 仓库" not in capsys.readouterr().out


def test_existing_project_in_subdirectory_gets_no_repo_root_hint(project, monkeypatch, capsys):
    monkeypatch.chdir(project / "app")
    assert run_cli("init", "--tools", "claude", "--yes") == 0
    capsys.readouterr()
    assert run_cli("init", "--tools", "claude", "--yes") == 0                   # 第二次：找到 app/ 的清单
    assert "当前目录在 git 仓库" not in capsys.readouterr().out


def test_init_with_explicit_path_uses_that_path(project, monkeypatch):
    write(project, "packages/web/openspec/config.yaml", "schema: spec-driven\n")
    monkeypatch.chdir(project)
    assert run_cli("init", "packages/web", "--tools", "claude", "--yes") == 0
    assert (project / "packages/web/.rulemason.yaml").is_file()
    assert not (project / ".rulemason.yaml").exists()


# ---------- 取消工具时删除入口 ----------


def test_cancel_claude_keeps_project_text_in_claude_md(project):
    assert _init(project, "claude,codex") == 0
    claude = project / "CLAUDE.md"
    claude.write_text("项目自己的说明\n\n" + claude.read_text(encoding="utf-8"), encoding="utf-8")
    assert _init(project, "codex") == 0
    assert claude.read_text(encoding="utf-8") == "项目自己的说明\n"
    assert not (project / ".claude/skills/rulemason").exists()


def test_cancel_claude_deletes_claude_md_with_only_block(project):
    assert _init(project, "claude,codex") == 0
    assert _init(project, "codex") == 0
    assert not (project / "CLAUDE.md").exists()


@pytest.mark.parametrize("edited", [False, True])
def test_cancel_opencode_deletes_untouched_config_only(project, capsys, edited):
    assert _init(project, "opencode,claude") == 0
    config = project / "opencode.jsonc"
    if edited:
        config.write_text(config.read_text(encoding="utf-8").replace("{", '{\n  "model": "x",', 1), encoding="utf-8")
    capsys.readouterr()
    assert _init(project, "claude") == 0
    assert config.exists() == edited
    assert ("取消 OpenCode 后保留" in capsys.readouterr().out) == edited


def test_cancel_claude_keeps_text_after_block_and_reports_unpaired(project, capsys):
    assert _init(project, "claude,codex") == 0
    claude = project / "CLAUDE.md"
    claude.write_text(claude.read_text(encoding="utf-8") + "\n块后的说明\n", encoding="utf-8")
    assert _init(project, "codex") == 0
    assert claude.read_text(encoding="utf-8") == "块后的说明\n"
    assert _init(project, "claude,codex") == 0
    claude.write_text(claude.read_text(encoding="utf-8").replace("<!-- /rulemason:claude -->", ""), encoding="utf-8")
    capsys.readouterr()
    assert _init(project, "codex") == 0
    assert "取消 Claude Code 后未删除" in capsys.readouterr().out


# ---------- init --plan（agent-io） ----------

def _unjoined(root):
    """在 project 上加已有的 .claude/ 与自写 AGENTS.md：不带 --tools 时推断为 claude，AGENTS.md 是修改。"""
    write(root, ".claude/settings.json", "{}\n")
    write(root, "AGENTS.md", "# 自写\n")
    commit(root)
    return root


def _no_openspec_init(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("--plan 不应运行 openspec init")
    monkeypatch.setattr(init, "ensure_openspec", fail)


def test_plan_writes_nothing_in_non_interactive_session(project, monkeypatch, capsys):
    root = _unjoined(project)
    _no_openspec_init(monkeypatch)
    monkeypatch.setattr(init, "interactive", lambda: False)
    monkeypatch.setattr(builtins, "input", lambda *_: pytest.fail("--plan 不应提问"))
    before = snapshot(root)
    assert init.run(root, None, False, plan_only=True) == 0
    out = capsys.readouterr().out
    assert "工具：claude" in out and ".rulemason/rules/code-style.md" in out and "未写任何文件" in out
    assert snapshot(root) == before


def test_plan_json_marks_add_and_modify(project, capsys):
    root = _unjoined(project)
    assert init.run(root, None, False, plan_only=True, as_json=True) == 0
    data = json.loads(capsys.readouterr().out)
    actions = {w["path"]: w["action"] for w in data["writes"]}
    assert actions["AGENTS.md"] == "modify" and actions[".rulemason/rules/code-style.md"] == "add"
    assert data["tools"] == ["claude"] and data["openspec_init"] is False and data["untouched_dirty"] == 0
    assert set(data) == {"root", "tools", "writes", "deletes", "overwritten", "notes", "untouched_dirty", "openspec_init"}


def test_plan_without_openspec_does_not_create_it(project, monkeypatch, capsys):
    root = _unjoined(project)
    shutil.rmtree(root / "openspec")
    _no_openspec_init(monkeypatch)
    assert init.run(root, "claude", False, plan_only=True, as_json=True) == 0
    assert json.loads(capsys.readouterr().out)["openspec_init"] is True
    assert not (root / "openspec").exists()
    assert init.run(root, "claude", False, plan_only=True) == 0
    assert "将先询问是否运行 openspec init" in capsys.readouterr().out


def test_plan_without_git_has_null_dirty_count(project, capsys):
    root = project
    shutil.rmtree(root / ".git")
    assert init.run(root, "claude", False, plan_only=True, as_json=True) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["untouched_dirty"] is None
    assert "没有 git" in captured.err                             # 提示走 stderr，标准输出只有 JSON


@pytest.mark.parametrize("argv", [["init", "--json"], ["init", "--tools", "claude", "--yes", "--json"], ["update", "--json"], ["update", "--yes", "--json"]])
def test_json_without_plan_or_dry_run_is_rejected(project, monkeypatch, capsys, argv):
    """--json 不配 --plan / --dry-run 时报错退出，不写任何文件。"""
    root = _unjoined(project)
    monkeypatch.chdir(root)
    before = snapshot(root)
    assert run_cli(*argv) == 2
    assert "--json 只能配合" in capsys.readouterr().err
    assert snapshot(root) == before


@pytest.mark.parametrize(("argv", "code"), [(["check", "--json"], 1), (["init", "--plan", "--json"], 0), (["update", "--dry-run", "--json"], 1)])
def test_cli_json_flags(project, monkeypatch, capsys, argv, code):
    """三个只读选项接到命令行：未接入项目里 check 与 update 非 0，init --plan 为 0，输出都是 JSON 或提示、不写文件。"""
    root = _unjoined(project)
    monkeypatch.chdir(root)
    before = snapshot(root)
    assert run_cli(*argv) == code
    out = capsys.readouterr().out
    if argv[0] == "update":
        assert "先运行 rulemason init" in out                    # 预检失败：文字说明，非 0 退出
    else:
        json.loads(out)
    assert snapshot(root) == before


# ---------- OpenSpec operations 提示（openspec-operations） ----------

def test_init_appends_operations_and_keeps_config(project):
    before = (project / "openspec/config.yaml").read_text(encoding="utf-8")
    assert _init(project) == 0
    text = (project / "openspec/config.yaml").read_text(encoding="utf-8")
    assert text.startswith(before.rstrip("\n"))                       # 原文（含注释、context）逐字保留在前
    data = yaml.safe_load(text)
    assert list(data)[-1] == "operations"
    assert data["operations"] == check.base_operations(project)
    assert ".rulemason/rules/workflow-gates.md" in data["operations"]["archive"]["guidance"][0]
    assert data["rules"] and data["context"] == "项目说明\n"
    assert _init(project) == 0                                         # 重复运行不再追加
    assert (project / "openspec/config.yaml").read_text(encoding="utf-8") == text


def test_existing_operations_are_left_alone(project):
    own = "operations:\n  apply:\n    guidance:\n      - 项目自己的提示\n"
    write(project, "openspec/config.yaml", PY_PROJECT["openspec/config.yaml"] + own)
    assert _init(project) == 0
    data = yaml.safe_load((project / "openspec/config.yaml").read_text(encoding="utf-8"))
    assert data["operations"] == {"apply": {"guidance": ["项目自己的提示"]}}


def test_plan_operations_without_config_is_quiet(tmp_path):
    plan = init.Plan()
    init.plan_operations(tmp_path, plan)
    assert not plan.writes and not plan.notes


def test_operations_not_appended_when_other_keys_would_change(project):
    """原文以 `|+` 块收尾、带两个尾随空行（算内容）：追加会改变 context，计划只记提示、不写 operations。"""
    write(project, "openspec/config.yaml", "schema: spec-driven\ncontext: |+\n  项目说明\n\n\n")
    plan = init.Plan()
    init.plan_operations(project, plan)
    assert not plan.writes and "operations 无法安全追加" in plan.notes[0]


def test_null_operations_is_left_alone(project):
    write(project, "openspec/config.yaml", PY_PROJECT["openspec/config.yaml"] + "operations:\n")
    assert _init(project) == 0
    assert yaml.safe_load((project / "openspec/config.yaml").read_text(encoding="utf-8"))["operations"] is None


# ---------- 写完后汇报失败（readable-config-errors） ----------

def test_init_finishes_when_report_check_fails(project, capsys):
    write(project, "openspec/judgments.yaml", "id: x\n")
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert (project / ".rulemason.yaml").is_file()
    assert "check 未完成：openspec/judgments.yaml 的顶层应是列表" in out
    assert "本次改动的文件：" in out and init.NEXT_STEP in out


def test_init_does_not_swallow_other_errors_in_report(project, monkeypatch):
    """report 只兜住项目配置读不出来；程序自身的其他 ValueError 照常上抛，由命令行外层报 init 失败。"""
    def broken(_root):
        raise ValueError("程序缺陷")
    monkeypatch.setattr(check, "run", broken)
    with pytest.raises(ValueError, match="程序缺陷"):
        _init(project)


# ---------- React 落法（shared-react-rules） ----------

def test_react_project_references_react_rules(project):
    write(project, "web/package.json", REACT_PACKAGE)
    assert _init(project, tools="claude,opencode") == 0
    for rel in ("AGENTS.md", "CLAUDE.md", "opencode.jsonc"):
        assert ".rulemason/rules/react.md" in (project / rel).read_text(encoding="utf-8"), rel
    assert json.loads((project / "opencode.jsonc").read_text(encoding="utf-8"))["instructions"][2] == ".rulemason/rules/react.md"
    assert (project / ".rulemason/rules/react.md").is_file()
    assert ".rulemason/rules/react.md" in shared.read_manifest(project)["files"]


def test_non_react_project_has_no_react_rules(project):
    write(project, "frontend/package.json", '{"name": "site", "devDependencies": {"eslint": "^9"}}\n')
    assert _init(project, tools="claude,opencode") == 0
    for rel in ("AGENTS.md", "CLAUDE.md", "opencode.jsonc"):
        assert "react.md" not in (project / rel).read_text(encoding="utf-8"), rel
    json.loads((project / "opencode.jsonc").read_text(encoding="utf-8"))          # 去掉那一行后仍是合法 JSON


@pytest.mark.parametrize("files", [[], ["app/main.py"], ["web/package.json"], ["app/main.py", "web/package.json"]])
def test_opencode_template_stays_valid_json(tmp_path, files):
    write(tmp_path, "web/package.json", REACT_PACKAGE)
    instructions = json.loads(init.opencode_template(tmp_path, files))["instructions"]
    assert instructions[0] == ".rulemason/rules/code-style.md"
    assert instructions[-1] == ".rulemason/rules/workflow-gates.md"


# ---------- 已有 OpenCode 配置追加落法（shared-react-rules 决策 5） ----------

OPENCODE_OWN = """{
  "$schema": "https://opencode.ai/config.json",
  // 项目自己的注释
  "model": "x",
  "instructions": [
    ".rulemason/rules/code-style.md",
    ".rulemason/rules/workflow-gates.md"
  ]
}
"""


def test_append_instructions_keeps_rest_of_file():
    new = init.append_instructions(OPENCODE_OWN, [".rulemason/rules/react.md"])
    assert new == OPENCODE_OWN.replace('workflow-gates.md"\n', 'workflow-gates.md",\n    ".rulemason/rules/react.md"\n')


@pytest.mark.parametrize(("text", "expected"), [
    ('{"instructions": []}', '{"instructions": [\n    "r1",\n    "r2"]}'),
    ('{"instructions": [\n  ]}', '{"instructions": [\n    "r1",\n    "r2"\n  ]}'),
    ('{"instructions": ["a",]}', '{"instructions": ["a",\n    "r1",\n    "r2"]}'),
    ('{"instructions": ["a", "b"]}', '{"instructions": ["a", "b",\n    "r1",\n    "r2"]}'),
    ('{"instructions": [\n\t"a"\n]}', '{"instructions": [\n\t"a",\n\t"r1",\n\t"r2"\n]}'),
    ('{"instructions": ["https://example.com/a.md"]}', '{"instructions": ["https://example.com/a.md",\n    "r1",\n    "r2"]}'),
])
def test_append_instructions_shapes(text, expected):
    assert init.append_instructions(text, ["r1", "r2"]) == expected


@pytest.mark.parametrize("text", [
    '{"instructions": ["a", // 注释\n]}',
    '{"instructions": ["a"], "x": {"instructions": ["b"]}}',
    '{"instructions": ["a]b", "c"]}',
    '// "instructions": ["x"]\n{}',
    '/* "instructions": ["x"] */ {}',
])
def test_append_instructions_declines_when_unsafe(text):
    assert init.append_instructions(text, ["r"]) is None


def test_unsafe_opencode_config_is_only_reported(project):
    write(project, ".opencode/opencode.jsonc", '{"instructions": [".rulemason/rules/code-style.md", // 注释\n]}')
    plan = init.Plan()
    init.plan_opencode(project, shared.list_files(project), plan)
    assert ".opencode/opencode.jsonc" not in plan.writes
    assert plan.notes[0].startswith(".opencode/opencode.jsonc 的 instructions 缺少")


def test_update_appends_react_to_existing_opencode_config(project, capsys):
    write(project, ".opencode/opencode.jsonc", OPENCODE_OWN.replace('    ".rulemason/rules/code-style.md",\n', '    ".rulemason/rules/code-style.md",\n    ".rulemason/rules/python.md",\n'))
    assert _init(project, tools="claude,opencode") == 0
    commit(project)
    write(project, "web/package.json", REACT_PACKAGE)                  # 接入后才加 React
    config = project / ".opencode/opencode.jsonc"
    before = config.read_text(encoding="utf-8")
    assert update.run(project) == 0                                     # 非交互、没有 --yes：只列出
    assert config.read_text(encoding="utf-8") == before
    assert update.run(project, yes=True) == 0
    after = config.read_text(encoding="utf-8")
    assert after.startswith(before.split('    ".rulemason/rules/workflow-gates.md"')[0])
    assert after.rstrip().endswith('"\n  ]\n}')
    assert check.opencode_instruction_values(after)[-1] == ".rulemason/rules/react.md"
    assert check.collect(project)[0].layers["接入 工具入口"] == []


# ---------- rulekit 0.5 遗留文件：不识别，照常接入 ----------

def test_plan_json_ignores_rulekit_manifest(project, capsys):
    root = _unjoined(project)
    write(root, ".rulekit.yaml", 'version: 1\ntools: [claude]\nrulekit: 0.5.2\nfiles: {}\n')
    write(root, ".rulekit/rules/code-style.md", "旧副本\n")
    commit(root)
    before = snapshot(root)
    assert init.run(root, None, False, plan_only=True, as_json=True) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["deletes"] == [] and ".rulemason.yaml" in [w["path"] for w in data["writes"]]
    assert snapshot(root) == before


def test_init_proceeds_despite_sibling_rulekit_reference(project):
    write(project, "AGENTS.md", "## Code style\n\n../rulekit/rules/code-style.md\n")
    commit(project)
    assert _init(project) == 0
    assert "../rulekit/rules/code-style.md" in (project / "AGENTS.md").read_text(encoding="utf-8")


# ---------- init 体验（init-ux-1） ----------

def _fake_select(monkeypatch, picked):
    """把单键选择器换成固定返回；记录传给它的预勾与标注。"""
    seen = {}

    def choose(title, labels, checked, notes, **_):
        seen.update(labels=labels, checked=checked, notes=notes)
        return picked

    monkeypatch.setattr(init.select, "choose", choose)
    return seen


def test_first_run_checks_nothing_and_marks_detected(project, monkeypatch):
    (project / ".claude").mkdir()
    seen = _fake_select(monkeypatch, [1, 3])
    assert init.choose_tools(project, None, None) == ["claude", "codex"]
    assert seen["checked"] == [False, False, False, False]
    assert seen["notes"] == ["", "检测到", "", ""]


def test_rerun_prechecks_recorded_tools(project, monkeypatch):
    (project / ".claude").mkdir()
    seen = _fake_select(monkeypatch, [1])
    assert init.choose_tools(project, {"tools": ["claude", "cursor"]}, None) == ["claude"]
    assert seen["checked"] == [False, True, True, False] and seen["notes"] == ["", "", "", ""]


def test_cancelling_selector_writes_nothing(project, tty, monkeypatch, capsys):
    _fake_select(monkeypatch, None)
    before = snapshot(project)
    assert init.run(project, None, False) == 0
    assert "已取消" in capsys.readouterr().out and snapshot(project) == before


def test_summary_then_d_expands_full_plan(project, tty, monkeypatch, capsys):
    asked = _answers(monkeypatch, "d", "y")
    assert init.run(project, "claude", False) == 0
    out = capsys.readouterr().out
    summary, full = out.split("## 文件计划\n新增：", 1)                               # 摘要在前，d 之后才是完整清单
    assert "新增 " in summary and "规则副本" in summary and "  - .rulemason/rules/code-style.md" not in summary
    assert "  - .rulemason/rules/code-style.md" in full
    assert [q.startswith("按计划写入？ [y/N/d]") for q in asked] == [True, True]          # 展开后再问一次


def test_report_gives_conclusion_and_todos_only(project, capsys):
    write(project, "web/eslint.config.js", "module.exports = [];\n")
    assert _init(project) == 0
    out = capsys.readouterr().out
    tail = out.split("本次改动的文件", 1)[0]
    assert "## 识别表" not in out and "## 各层状态" not in out
    assert check.run(project)[0].splitlines()[0] in out and out.rstrip().endswith(init.NEXT_STEP)
    assert "需要你处理" in out and "import rulemasonBase from" in out and "{ rules: rulemasonBase }" in out
    assert tail.rstrip().endswith(check.run(project)[0].splitlines()[0])     # 结论行紧接在改动清单之前


@pytest.mark.parametrize("rule", [".claude/", ".claude/skills/", "*.md", "SKILL.md"])
def test_gitignore_is_opened_for_skill_copy(project, capsys, rule):
    write(project, ".gitignore", f"{rule}\n")
    commit(project)
    assert _init(project) == 0
    text = (project / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith(f"{rule}\n") and "!.claude/skills/rulemason/" in text and "随项目提交" in text
    assert ("!.claude/\n.claude/*\n" in text) is (rule == ".claude/")                 # 只从被忽略的那一级起放行
    assert ("!.rulemason/**" in text) is (rule == "*.md")                                    # *.md 也挡住规则副本，一并放行
    assert shared.ignored_files(project, [".claude/skills/rulemason/SKILL.md"]) == []
    assert "fix_gitignore" not in json.loads(check.run(project, as_json=True)[0])["next"]["code"]


def test_gitignore_opens_rulemason_dir_itself(project):
    write(project, ".gitignore", ".rulemason/\n")
    assert _init(project) == 0
    text = (project / ".gitignore").read_text(encoding="utf-8")
    assert "!.rulemason/\n!.rulemason/**" in text and "!.claude/" not in text
    assert shared.ignored_files(project, [".rulemason/rules/code-style.md"]) == []


def test_gitignore_is_not_appended_twice_for_nested_ignore(project):
    """忽略来自子目录自己的 .gitignore 时，根文件的放行规则没用：写过一次就不再重复追加。"""
    write(project, ".claude/.gitignore", "*\n")
    write(project, ".gitignore", "!.claude/skills/rulemason/\n!.claude/skills/rulemason/**\n")
    commit(project)
    before = (project / ".gitignore").read_text(encoding="utf-8")
    assert _init(project) == 0
    assert (project / ".gitignore").read_text(encoding="utf-8") == before


def test_gitignore_is_left_alone_when_copy_not_ignored(project):
    write(project, ".gitignore", ".venv/\n")
    assert _init(project) == 0
    assert (project / ".gitignore").read_text(encoding="utf-8") == ".venv/\n"


def test_yes_without_openspec_installs_rules_layer_only(tmp_path, fake_openspec, capsys):
    root = tmp_path / "fresh"
    git_init(root)
    write(root, "main.py", "x = 1\n")
    assert _init(root) == 0
    assert not fake_openspec.exists() and not (root / "openspec").exists()
    assert sorted(p.name for p in (root / ".claude").iterdir()) == ["skills"]
    assert "还没有接 OpenSpec" in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "需要 OpenSpec" in capsys.readouterr().out
    text, code = check.run(root)
    assert code == 0 and "检查点" not in text.split("\n", 1)[0]


def test_update_completes_gates_once_openspec_appears(tmp_path, fake_openspec, capsys):
    root = tmp_path / "fresh"
    git_init(root)
    write(root, "main.py", "x = 1\n")
    assert _init(root) == 0
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    assert update.run(root, yes=True) == 0
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "还没有接 OpenSpec" not in agents and "不走 OpenSpec 改代码之前" in agents
    assert (root / "openspec/specs/workflow-gates/spec.md").is_file()
    assert "rules:" in (root / "openspec/config.yaml").read_text(encoding="utf-8")


@pytest.mark.parametrize(("readme", "expected"), [
    ("# 章法\n\n[![ci](x)](y)\n\n章法是一个字帖检索站，按书家浏览单字。它只收录公有领域作品。第三句不要。\n", "章法是一个字帖检索站，按书家浏览单字。它只收录公有领域作品。"),
    ("# 标题\n\n![logo](a.png)\n\n> 引用\n\nOne line intro without period\n", "One line intro without period"),
    ("# T\n\nBuilt on Node.js v1.0 for teams. Ships as a CLI. Third sentence.\n", "Built on Node.js v1.0 for teams. Ships as a CLI."),
    ("# 只有标题\n", None),
    ("# 章法\n\n中文 · [English](https://example.com/README.en.md)\n\n章法是一个字帖检索站。\n", "章法是一个字帖检索站。"),
    ("# 章法\n\n[English](https://example.com/en) | 简体中文\n\n章法是一个字帖检索站。\n", "章法是一个字帖检索站。"),
    ("# T\n\n[文档](https://a) · [示例](https://b) · [更新日志](https://c)\n\nA tool for teams.\n", "A tool for teams."),
    ("# T\n\n本工具是 [OpenSpec](https://example.com) 的配套检查器，给 AI 编码用。\n", "本工具是 [OpenSpec](https://example.com) 的配套检查器，给 AI 编码用。"),
    ("# T\n\n见 [文档](https://a)\n", None),
    ("# T\n\nA CLI for [OpenSpec](https://example.com)\n", "A CLI for [OpenSpec](https://example.com)"),
    ("# T\n\nEnglish | [日本語](https://a) | [中文](https://b)\n\nA tool for teams.\n", "A tool for teams."),
])
def test_agents_intro_is_prefilled_from_readme(project, readme, expected):
    write(project, "README.md", readme)
    assert _init(project) == 0
    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    intro = text.split("\n\n")[1]
    assert intro == (expected or "待 /rulemason 补充：一两句话写这个项目是什么、给谁用。")
    assert "## 红线（不可违反）\n\n暂无\n" in text


def test_existing_agents_intro_is_kept(project):
    write(project, "README.md", "一句简介。\n")
    write(project, "AGENTS.md", "# 自写\n\n别的简介。\n")
    assert _init(project) == 0
    assert (project / "AGENTS.md").read_text(encoding="utf-8").startswith("# 自写\n\n别的简介。\n")


def _archives(root, n):
    for i in range(n):
        write(root, f"openspec/changes/archive/2026-01-0{i + 1}-c{i}/proposal.md", "# P\n")


def test_key_prompt_when_conditions_met(project, tty, monkeypatch, capsys):
    _archives(project, 3)
    monkeypatch.setattr(init.engine, "api_key", lambda: "")
    called = []
    monkeypatch.setattr(init.key_cmd, "run", lambda: called.append(True) or 0)
    asked = _answers(monkeypatch, "y", "y")
    assert init.run(project, "claude", False) == 0
    assert "现在配置 Jev 的 key" in asked[1] and shared.KEY_URL in asked[1] and called == [True]


def test_key_hint_only_when_conditions_not_met(project, tty, monkeypatch, capsys):
    monkeypatch.setattr(init.engine, "api_key", lambda: "")
    _answers(monkeypatch, "y")
    assert init.run(project, "claude", False) == 0
    out = capsys.readouterr().out
    assert "判断功能需要 git 与至少 3 个已归档 change" in out and "现在配置" not in out


@pytest.mark.parametrize("has_key", [True, False])
def test_no_key_prompt_with_key_or_yes(project, tty, monkeypatch, capsys, has_key):
    _archives(project, 3)
    monkeypatch.setattr(init.engine, "api_key", lambda: "k" if has_key else "")
    asked = _answers(monkeypatch, "y")
    assert init.run(project, "claude", not has_key) == 0           # 有 key 时交互运行，没 key 时 --yes
    assert "Jev 的 key" not in capsys.readouterr().out and all("key" not in q for q in asked)


def test_has_key_hint_says_how_to_enable_judgment(project, tty, monkeypatch, capsys):
    _archives(project, 60)
    monkeypatch.setattr(init.engine, "api_key", lambda: "k")
    asked = _answers(monkeypatch, "y")
    assert init.run(project, "claude", False) == 0
    out = capsys.readouterr().out
    assert "判断条件已满足；判断审 OpenSpec 方案、界面文案与直接改动的说明" in out and "/rulemason" in out
    assert all("key" not in q for q in asked)                                   # 只说明，不提问


def test_has_key_hint_absent_when_conditions_not_met(project, tty, monkeypatch, capsys):
    monkeypatch.setattr(init.engine, "api_key", lambda: "k")                    # 只归档了 0 个，条件未满足
    _answers(monkeypatch, "y")
    assert init.run(project, "claude", False) == 0
    out = capsys.readouterr().out
    assert "判断条件已满足" not in out and "判断功能需要" not in out


def test_has_key_hint_absent_when_judgment_enabled(project, tty, monkeypatch, capsys):
    _archives(project, 60)
    write(project, "openspec/judgments.yaml", "[]\n")
    monkeypatch.setattr(init.engine, "api_key", lambda: "k")
    _answers(monkeypatch, "y")
    assert init.run(project, "claude", False) == 0
    assert "判断条件已满足" not in capsys.readouterr().out

def test_go_project_gets_only_generic_rules_and_update_adds_python_later(tmp_path, capsys):
    root = tmp_path / "svc"
    git_init(root)
    write(root, "go.mod", "module x\n")
    write(root, "main.go", "package main\n")
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    commit(root)
    assert _init(root) == 0
    assert sorted(p.relative_to(root / ".rulemason").as_posix() for p in (root / ".rulemason").rglob("*") if p.is_file()) == [
        "README.md",
        "result-check/product-artifact.hint.json",
        "result-check/product-artifact.strict.json",
        "result-check/prose-hygiene.hint.json",
        "result-check/prose-hygiene.strict.json",
        "rules/agent-coding-caution.md",
        "rules/cjk-typography.md",
        "rules/code-style.md",
        "rules/product-artifact-caution.md",
        "rules/prose-hygiene.md",
        "rules/result-check-contracts.md",
        "rules/workflow-gates.md",
    ]
    assert "- `rules/code-style.md`" in (root / ".rulemason/README.md").read_text(encoding="utf-8")
    assert check.run(root)[1] == 0

    write(root, "pyproject.toml", '[project]\nname = "x"\n')
    write(root, "app/main.py", "x = 1\n")
    assert update.run(root, yes=True) == 0
    assert (root / ".rulemason/rules/python.md").is_file() and (root / ".rulemason/lint/ruff-base.toml").is_file()
    assert ".rulemason/rules/python.md" in shared.read_manifest(root)["files"]
    assert ".rulemason/rules/python.md" in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert check.run(root)[1] == 0


# ---------- lint 写法、坏路径与 ruff.toml 位置（init-ux-2） ----------

@pytest.mark.parametrize(("config", "expected"), [
    ('import js from "@eslint/js";\nexport default defineConfig([\n  js.configs.recommended,\n]);\n',
     'export default defineConfig([\n  { rules: rulemasonBase },\n  js.configs.recommended,'),
    ('import tseslint from "typescript-eslint";\nexport default tseslint.config(\n  ...tseslint.configs.recommended,\n);\n',
     'export default tseslint.config(\n  { rules: rulemasonBase },\n  ...tseslint.configs.recommended,'),
    ('export default tseslint.config();\n', 'export default tseslint.config(\n  { rules: rulemasonBase },);'),
])
def test_eslint_define_config_and_tseslint_are_patched(project, capsys, config, expected):
    write(project, "web/eslint.config.js", config)
    assert _init(project) == 0
    text = (project / "web/eslint.config.js").read_text(encoding="utf-8")
    assert text.startswith('import rulemasonBase from "../.rulemason/lint/eslint-base.mjs";\n') and expected in text
    assert "无法自动识别" not in capsys.readouterr().out


def test_broken_eslint_ref_is_repointed_not_duplicated(project):
    old = 'import rulekitBase from "../../../.rulekit/lint/eslint-base.mjs";\nexport default [{ rules: { ...rulekitBase } }];\n'
    write(project, "apps/admin-web/eslint.config.js", old)
    assert _init(project) == 0
    text = (project / "apps/admin-web/eslint.config.js").read_text(encoding="utf-8")
    assert text == old.replace("../../../.rulekit/", "../../.rulemason/")
    report, _ = check.collect(project)
    assert report.layers["接入 lint 继承"] == []


def test_broken_ruff_extend_is_repointed(project):
    write(project, "ruff.toml", "extend = '../rulekit/lint/ruff-base.toml'\n")
    assert _init(project) == 0
    assert (project / "ruff.toml").read_text(encoding="utf-8") == "extend = '.rulemason/lint/ruff-base.toml'\n"


def test_root_eslint_config_import_is_relative(project):
    write(project, "eslint.config.js", "export default [];\n")
    assert _init(project) == 0
    assert 'from "./.rulemason/lint/eslint-base.mjs"' in (project / "eslint.config.js").read_text(encoding="utf-8")


@pytest.mark.parametrize(("extra", "home"), [({}, "apps/api"), ({"scripts/tool.py": "x = 1\n"}, ".")])
def test_new_ruff_config_goes_to_the_only_python_dir(tmp_path, extra, home):
    root = tmp_path / "proj"
    git_init(root)
    files = {"openspec/config.yaml": "schema: spec-driven\n", "apps/api/pyproject.toml": '[project]\nname = "api"\n', "apps/api/app/main.py": "x = 1\n", **extra}
    for rel, text in files.items():
        write(root, rel, text)
    assert _init(root) == 0
    config = root / home / "ruff.toml"
    expected = "../../.rulemason/lint/ruff-base.toml" if home != "." else ".rulemason/lint/ruff-base.toml"
    assert f'extend = "{expected}"' in config.read_text(encoding="utf-8")
    assert sorted(p.relative_to(root).as_posix() for p in root.rglob("ruff.toml") if ".rulemason" not in p.parts) == [config.relative_to(root).as_posix()]
    assert check.collect(root)[0].layers["接入 lint 继承"] == []


# ---------- 11. lint 继承链、旧位置副本与手动项说明（lint-fix-guidance） ----------

def test_remove_then_init_points_ruff_back_to_copy(project, capsys):
    from rulemason import remove
    assert _init(project) == 0
    first_claude = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert remove.run(project, yes=True) == 0
    assert '\nextend = "lint/ruff-base.toml"' in (project / "ruff.toml").read_text(encoding="utf-8")
    capsys.readouterr()
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert '\nextend = ".rulemason/lint/ruff-base.toml"' in (project / "ruff.toml").read_text(encoding="utf-8")
    assert (project / "lint/ruff-base.toml").is_file()                                     # 不代为删除
    todos = out.split("需要你处理", 1)[1].split("提示：", 1)[0] if "需要你处理" in out else ""
    assert "ruff" not in todos                                                              # ruff 不算待处理
    assert "提示：\n  - lint/ruff-base.toml 是基础配置的旧位置副本" in out
    assert check.collect(project)[0].layers["接入 lint 继承"] == []
    assert (project / "CLAUDE.md").read_text(encoding="utf-8") == first_claude              # remove 留下的那一行由新块接替，与初次接入逐字相同
    assert "块外已导入 AGENTS.md" not in out


def test_edited_old_ruff_copy_is_not_changed(project, capsys):
    write(project, "lint/ruff-base.toml", "[lint]\nselect = []\n")
    write(project, "ruff.toml", 'extend = "lint/ruff-base.toml"\n')
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert (project / "ruff.toml").read_text(encoding="utf-8") == 'extend = "lint/ruff-base.toml"\n'
    assert "ruff.toml 继承的 lint/ruff-base.toml 与基础配置不同（被改过或来自旧版本）：未修改" in out
    assert "diff lint/ruff-base.toml .rulemason/lint/ruff-base.toml" in out
    assert '再把第 1 行 extend = "lint/ruff-base.toml" 里的 lint/ruff-base.toml 改为 .rulemason/lint/ruff-base.toml' in out


def test_eslint_import_of_old_copy_is_repointed(project):
    write(project, "lint/eslint-base.mjs", (shared.shared_root() / "lint/eslint-base.mjs").read_text(encoding="utf-8"))
    old = 'import legacyBase from "../../lint/eslint-base.mjs";\n\nexport default [\n  { rules: legacyBase },\n];\n'
    write(project, "apps/admin-web/eslint.config.js", old)
    assert _init(project) == 0
    text = (project / "apps/admin-web/eslint.config.js").read_text(encoding="utf-8")
    assert text == old.replace("../../lint/", "../../.rulemason/lint/")
    assert text.count("eslint-base.mjs") == 1


def test_two_configs_share_one_chain_tail(project):
    write(project, "apps/api/ruff.toml", 'extend = "../../ruff-common.toml"\n')
    write(project, "apps/worker/ruff.toml", 'extend = "../../ruff-common.toml"\n')
    write(project, "ruff-common.toml", "line-length = 100\n")
    assert _init(project) == 0
    common = (project / "ruff-common.toml").read_text(encoding="utf-8")
    assert common.count("extend =") == 1 and common.startswith('extend = ".rulemason/lint/ruff-base.toml"')
    for sub in ("api", "worker"):
        assert (project / f"apps/{sub}/ruff.toml").read_text(encoding="utf-8") == 'extend = "../../ruff-common.toml"\n'
    assert check.collect(project)[0].layers["接入 lint 继承"] == []


def test_three_level_chain_only_tail_changes(project):
    write(project, "ruff.toml", 'extend = "a.toml"\n')
    write(project, "a.toml", 'extend = "b.toml"\n')
    write(project, "b.toml", "line-length = 100\n")
    assert _init(project) == 0
    assert (project / "a.toml").read_text(encoding="utf-8") == 'extend = "b.toml"\n'
    assert (project / "b.toml").read_text(encoding="utf-8").startswith('extend = ".rulemason/lint/ruff-base.toml"')


def test_cycle_is_reported_and_nothing_changes(project, capsys):
    write(project, "ruff.toml", 'extend = "a.toml"\n')
    write(project, "a.toml", 'extend = "ruff.toml"\n')
    assert _init(project) == 0
    assert "ruff 继承链绕回自己：ruff.toml → a.toml → ruff.toml" in capsys.readouterr().out
    assert (project / "a.toml").read_text(encoding="utf-8") == 'extend = "ruff.toml"\n'


def test_select_note_gives_line_and_two_options(project, capsys):
    write(project, "ruff.toml", '# 项目 ruff\n[lint]\nselect = ["E", "F"]\n')
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert 'ruff.toml 写了 select' in out and '位置：第 3 行 select = ["E", "F"]' in out
    assert 'extend-select = ["E", "F"]' in out and "删去这一行" in out and "改完运行：rulemason update" in out
    assert "sed" not in out


def test_outside_config_note_gives_new_line_and_copy_reminder(project, capsys):
    write(project, "ruff.toml", 'extend = "~/configs/ruff.toml"\n')
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert "ruff.toml 继承了项目外的 ~/configs/ruff.toml：未修改" in out and "位置：第 1 行" in out
    assert '改为：extend = ".rulemason/lint/ruff-base.toml"' in out and "~/configs/ruff.toml 里本项目要用的设置" in out
    assert (project / "ruff.toml").read_text(encoding="utf-8") == 'extend = "~/configs/ruff.toml"\n'


def test_unrecognized_eslint_note_gives_import_and_entry(project, capsys):
    write(project, "web/eslint.config.js", 'import js from "@eslint/js";\nmodule.exports = [js.configs.recommended];\n')
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert 'web/eslint.config.js 的格式无法自动识别：未修改' in out
    assert '在第 1 行（第一条 import）之前加入：import rulemasonBase from "../.rulemason/lint/eslint-base.mjs";' in out
    assert "{ rules: rulemasonBase }," in out


def test_duplicate_eslint_import_is_reported_not_changed(project, capsys):
    write(project, "lint/eslint-base.mjs", "export default {};\n")
    text = (
        'import js from "@eslint/js";\nimport legacyBase from "../../lint/eslint-base.mjs";\n'
        'import rulemasonBase from "../../.rulemason/lint/eslint-base.mjs";\n\nexport default [\n'
        "  { rules: rulemasonBase },\n  js.configs.recommended,\n  {\n  },\n  { rules: legacyBase },\n];\n"
    )
    write(project, "apps/admin-web/eslint.config.js", text)
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert (project / "apps/admin-web/eslint.config.js").read_text(encoding="utf-8") == text
    assert "apps/admin-web/eslint.config.js 重复引入基础规则（../../lint/eslint-base.mjs 与 .rulemason/ 下的副本）" in out
    assert "@eslint/js" not in out.split("重复引入基础规则", 1)[1].splitlines()[0]          # 与基础规则无关的引入不算
    assert '删去第 2 行 import legacyBase from "../../lint/eslint-base.mjs";' in out
    assert "再删去用到它的第 10 行 { rules: legacyBase }," in out
    report, _ = check.collect(project)
    assert any(item.startswith("apps/admin-web/eslint.config.js 重复引入基础规则") for item in report.layers["接入 lint 继承"])
    assert check.exit_code(report) == 1


def test_pyproject_tail_without_tool_ruff_gets_two_line_note(project, capsys):
    write(project, "ruff.toml", 'extend = "pyproject.toml"\n')
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert "pyproject.toml 无法安全写入 extend（找不到 [tool.ruff] 表头）：未修改" in out
    assert '在文件里加入这两行：[tool.ruff] 与 extend = ".rulemason/lint/ruff-base.toml"' in out


def test_edited_old_eslint_copy_is_not_changed(project, capsys):
    write(project, "lint/eslint-base.mjs", "export default { 'no-console': 'off' };\n")
    old = 'import legacyBase from "../lint/eslint-base.mjs";\n\nexport default [\n  { rules: legacyBase },\n];\n'
    write(project, "web/eslint.config.js", old)
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert (project / "web/eslint.config.js").read_text(encoding="utf-8") == old
    assert "web/eslint.config.js 引入的 lint/eslint-base.mjs 与基础配置不同（被改过或来自旧版本）：未修改" in out
    assert "diff lint/eslint-base.mjs .rulemason/lint/eslint-base.mjs" in out


def test_remove_then_init_points_eslint_back_to_copy(project):
    from rulemason import remove
    write(project, "web/package.json", '{"dependencies": {"react": "18.0.0"}}\n')
    write(project, "web/eslint.config.mjs", "export default [\n];\n")
    assert _init(project) == 0
    assert remove.run(project, yes=True) == 0
    assert '"../lint/eslint-base.mjs"' in (project / "web/eslint.config.mjs").read_text(encoding="utf-8")
    assert _init(project) == 0
    text = (project / "web/eslint.config.mjs").read_text(encoding="utf-8")
    assert '"../.rulemason/lint/eslint-base.mjs"' in text and text.count("eslint-base.mjs") == 1


def test_duplicate_import_of_edited_old_copy_says_diff_first(project, capsys):
    write(project, "lint/eslint-base.mjs", "export default { 'no-console': 'off' };\n")
    text = (
        'import legacyBase from "../lint/eslint-base.mjs";\nimport rulemasonBase from "../.rulemason/lint/eslint-base.mjs";\n\n'
        "export default [\n  { rules: rulemasonBase },\n  { rules: legacyBase },\n];\n"
    )
    write(project, "web/eslint.config.js", text)
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert "先看差异：diff lint/eslint-base.mjs .rulemason/lint/eslint-base.mjs，要保留的规则写进 web/eslint.config.js" in out
    assert out.index("先看差异") < out.index("删去第 1 行")


def test_duplicate_note_covers_named_import_and_every_use(project, capsys):
    text = (
        'import { base } from "../gone/eslint-base.mjs";\nimport legacy from "../../gone2/eslint-base.mjs";\n'
        'import rulemasonBase from "../.rulemason/lint/eslint-base.mjs";\n\nexport default [\n'
        "  { rules: rulemasonBase },\n  { rules: legacy },\n  { files: ['*.ts'], rules: { ...legacy } },\n];\n"
    )
    write(project, "web/eslint.config.js", text)
    assert _init(project) == 0
    out = capsys.readouterr().out
    assert "删去第 1 行 import { base }" in out and "再删去配置里用到它的地方" in out
    assert "再删去用到它的第 7 行 { rules: legacy }," in out
    assert "再在第 8 行去掉对 legacy 的使用：{ files: ['*.ts'], rules: { ...legacy } }," in out


def test_broken_reference_at_chain_tail_is_repointed_in_tail(project):
    write(project, "ruff.toml", 'extend = "config/ruff-shared.toml"\n')
    write(project, "config/ruff-shared.toml", 'extend = "../gone/ruff-base.toml"\n')
    assert _init(project) == 0
    assert (project / "ruff.toml").read_text(encoding="utf-8") == 'extend = "config/ruff-shared.toml"\n'
    assert (project / "config/ruff-shared.toml").read_text(encoding="utf-8") == 'extend = "../.rulemason/lint/ruff-base.toml"\n'


def test_unreadable_chain_file_is_reported_by_init(project, capsys):
    write(project, "ruff.toml", 'extend = "bad.toml"\n')
    (project / "bad.toml").write_bytes(b"\xff\xfe")
    assert _init(project) == 0
    assert "ruff.toml 继承的 bad.toml 读不出" in capsys.readouterr().out
    assert (project / "ruff.toml").read_text(encoding="utf-8") == 'extend = "bad.toml"\n'


# ---------- 放项目的文件夹（multi-project-folder） ----------

def test_plan_in_project_folder_hints_without_changing_writes(tmp_path, capsys):
    folder, alone = tmp_path / "A", tmp_path / "A-alone"
    project_folder(folder)
    write(alone, "README.md", "# 产品目录\n")

    assert init.run(folder, "claude", False, plan_only=True) == 0
    out = capsys.readouterr().out
    assert "这里有独立项目 b、c；" in out and "分别运行 rulemason init" in out

    writes = []
    for root in (folder, alone):
        assert init.run(root, "claude", False, plan_only=True, as_json=True) == 0
        writes.append(json.loads(capsys.readouterr().out)["writes"])
    assert writes[0] == writes[1]                                   # 提示不改变计划


# ---------- 接入日期（joined-date-spec-lint-audits） ----------

def test_init_records_today_and_keeps_it_on_rerun(project, monkeypatch):
    class Day(datetime.date):
        now = (2026, 11, 5)

        @classmethod
        def today(cls):
            return cls(*cls.now)
    monkeypatch.setattr(init, "date", Day)
    assert init.run(project, "claude", True) == 0
    assert shared.read_manifest(project)["joined"] == "2026-11-05"
    assert (project / ".rulemason.yaml").read_text(encoding="utf-8").splitlines()[2] == "joined: '2026-11-05'"

    Day.now = (2026, 11, 9)                                                    # 几天后再运行
    assert init.run(project, "claude,codex", True) == 0
    assert shared.read_manifest(project)["joined"] == "2026-11-05"


def test_init_ignores_old_deleted_manifest_in_git(project, monkeypatch):
    write(project, ".rulemason.yaml", "version: 1\ntools: []\n")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-10-01T10:00:00")
    commit(project, "很久以前接入过")
    (project / ".rulemason.yaml").unlink()
    commit(project, "卸载")
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    assert init.run(project, "claude", True) == 0
    assert shared.read_manifest(project)["joined"] == datetime.date.today().isoformat()   # 重新接入记当天，不取旧日期
