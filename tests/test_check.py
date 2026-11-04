"""rulemason check 的测试：在临时项目里搭出各种接入状态，核对识别、各层状态、巡检、下一阶段与退出码。"""
from __future__ import annotations

import json

import pytest
import yaml
from conftest import (
    REACT_PACKAGE,
    commit,
    drop_operations,
    git,
    git_init,
    run_cli,
    write,
    write_manifest,
)

from rulemason import __version__, check, init, shared, update

BASE_RULES = check.base_artifact_rules()
BASE_JUDGMENTS = shared.read_judgments(check.ENGINE_BASE / "judgments.yaml")

AGENTS_OK = """# x

## Code style

.rulemason/rules/code-style.md
.rulemason/rules/python.md

## Workflow gates

.rulemason/rules/workflow-gates.md
"""


# ---------- 1. 临时项目 ----------

def _archive(root, n: int) -> None:
    for i in range(n):
        write(root, f"openspec/changes/archive/2026-01-0{i + 1}-c{i}/proposal.md", "# P\n")


def _install(root, tools: list[str], version: str = __version__) -> None:
    """照 init 的结果写出生成副本与 manifest（不经过 init，单测 check 自己）：副本按项目当前的语言挑选。"""
    root.mkdir(parents=True, exist_ok=True)
    files = shared.generated_files(tools, check.copied_rules(root, shared.list_files(root)))
    for rel, text in files.items():
        write(root, rel, text)
    manifest = yaml.safe_load(shared.manifest_text(None, tools, {rel: shared.sha256_text(t) for rel, t in files.items()}))
    manifest["rulemason"] = version
    write_manifest(root, manifest)


@pytest.fixture
def bare(tmp_path):
    """只有 openspec 与一份 Python 代码、什么都没接入的项目。"""
    root = tmp_path / "proj"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\ncontext: 项目\n")
    write(root, "app/main.py", "x = 1\n")
    commit(root)
    return root


@pytest.fixture
def joined(bare):
    """接入已完成、未选工具的项目。"""
    _install(bare, [])
    write(bare, "AGENTS.md", AGENTS_OK)
    write(bare, "openspec/config.yaml", yaml.safe_dump({"schema": "spec-driven", "context": "项目", "rules": BASE_RULES}, allow_unicode=True))
    write(bare, "ruff.toml", 'extend = ".rulemason/lint/ruff-base.toml"\n')
    commit(bare)
    return bare


def _finding(report: check.Report, name: str) -> list[str]:
    return dict(report.findings)[name]


# ---------- 2. 下一阶段 ----------

def test_bare_project_asks_for_init_even_with_history(bare):
    _archive(bare, 5)
    commit(bare)
    report, stage = check.collect(bare)
    assert stage.line == "接入：运行 rulemason init"
    assert "没有 AGENTS.md" in report.layers["接入 代码规矩与 gates"]
    assert "有 Python 代码但没有 ruff 配置" in report.layers["接入 lint 继承"]
    assert check.exit_code(report) == 1


def test_judge_is_optional_with_few_archives(joined):
    _archive(joined, 2)
    report, stage = check.collect(joined)
    assert dict(report.facts)["判断"] == "可选，未启用（需要 git 与至少 3 个已归档 change；还差 1 个）"
    assert stage.line == "日常巡检：一切一致" and check.exit_code(report) == 0


def test_judge_ready_to_enable_with_enough_archives(joined):
    _archive(joined, 3)
    report, stage = check.collect(joined)
    assert dict(report.facts)["判断"].startswith("可选，未启用（条件已满足")
    assert stage.line == "日常巡检：一切一致"


def test_fully_installed_goes_to_audit_and_exits_zero(joined):
    write(joined, "openspec/judgments.yaml", "[]\n")
    _install(joined, [])                             # 启用判断后副本要带上文案语气，update 会补
    text, code = check.run(joined)
    assert text.startswith("日常巡检：一切一致\n") and "- 判断：已启用" in text
    assert code == 0


def test_pending_placeholders_ask_for_project_content(joined):
    write(joined, "AGENTS.md", AGENTS_OK + "\n待 /rulemason 补充：项目简介\n")
    _, stage = check.collect(joined)
    assert stage.line == "补项目信息：在 AI 工具中运行 /rulemason"


# ---------- 3. 各层状态 ----------

def test_agents_without_shared_import_is_missing(joined):
    write(joined, "AGENTS.md", "# x\n\n## Code style\n\n九条正文\n\n## Workflow gates\n\n.rulemason/rules/workflow-gates.md\n")
    report, stage = check.collect(joined)
    assert any("code-style.md" in m for m in report.layers["接入 代码规矩与 gates"])
    assert stage.line == "接入：运行 rulemason update"
    assert check.exit_code(report) == 1


def test_ruff_with_select_is_reported(joined):
    write(joined, "ruff.toml", 'extend = ".rulemason/lint/ruff-base.toml"\n[lint]\nselect = ["E"]\n')
    report, _ = check.collect(joined)
    assert any("select" in m for m in report.layers["接入 lint 继承"])
    assert check.exit_code(report) == 1


def test_ruff_in_subdir_resolves_relative_to_config(joined):
    write(joined, "svc/pyproject.toml", '[tool.ruff]\nextend = "../.rulemason/lint/ruff-base.toml"\n')
    report, _ = check.collect(joined)
    assert report.layers["接入 lint 继承"] == []


def test_eslint_without_base_is_reported(joined):
    write(joined, "web/eslint.config.mjs", "export default [];\n")
    report, _ = check.collect(joined)
    assert any("eslint-base.mjs" in m for m in report.layers["接入 lint 继承"])
    assert check.exit_code(report) == 1


def test_selected_cursor_does_not_require_unselected_adapters(joined):
    _install(joined, ["cursor"])
    assert check.check_tool_entries(joined, shared.list_files(joined), ["cursor"]) == []


def test_selected_claude_missing_entries_are_reported_without_other_tools(joined):
    write(joined, ".rulemason.yaml", f"version: 1\nrulemason: {__version__}\ntools: [claude]\n")

    issues = check.check_tool_entries(joined, shared.list_files(joined), ["claude"])
    report, _ = check.collect(joined)

    assert any("CLAUDE.md" in issue for issue in issues)
    assert any(".claude/skills/rulemason" in issue for issue in issues)
    assert not any(tool in issue for issue in issues for tool in ("OpenCode", "Cursor", "Codex"))
    assert check.exit_code(report) == 1


def test_claude_md_must_import_shared_rules(joined):
    _install(joined, ["claude"])
    write(joined, "CLAUDE.md", "@AGENTS.md\n")
    issues = check.check_tool_entries(joined, shared.list_files(joined), ["claude"])
    assert issues == [f"CLAUDE.md 未导入 .rulemason/rules/{name}.md" for name in ("code-style", "python", "workflow-gates")]


def test_invalid_manifest_is_reported(joined):
    write(joined, ".rulemason.yaml", "tools: [claude]\n")
    report, stage = check.collect(joined)
    assert any("version" in m for m in report.layers["接入 工具入口"])
    assert stage.line == "接入：先修正 .rulemason.yaml"
    assert check.exit_code(report) == 1


# ---------- 4. 副本、版本（3.2） ----------

def test_hand_edited_copy_fails(joined):
    write(joined, ".rulemason/rules/code-style.md", "改过了\n")
    text, code = check.run(joined)
    assert "与记录的校验值不符（被手改）：.rulemason/rules/code-style.md" in text
    assert code == 1


def test_missing_skill_copy_fails(joined):
    _install(joined, ["codex"])
    (joined / ".agents/skills/rulemason/SKILL.md").unlink()
    report, _ = check.collect(joined)
    assert "缺少生成副本：.agents/skills/rulemason/SKILL.md" in report.layers["接入 生成副本"]
    assert check.exit_code(report) == 1


def test_version_behind_is_reported_but_exits_zero(joined):
    _install(joined, [], version="0.4.9")
    text, code = check.run(joined)
    assert text.splitlines()[0] == f"日常巡检：一切一致；版本号落后（0.4.9 → {__version__}），副本内容相同"
    assert f"项目记录 0.4.9，本机 {__version__}：只有版本号落后，副本内容相同" in text
    assert code == 0


# ---------- 5. 巡检 ----------

def test_rewritten_base_rule_is_a_finding_appended_is_not(joined):
    rules = {k: list(v) for k, v in BASE_RULES.items()}
    rules["design"][1] = rules["design"][1] + "（本项目另有说明）"     # 改写
    rules["tasks"].append("本项目追加的一条")                          # 追加
    write(joined, "openspec/config.yaml", yaml.safe_dump({"schema": "spec-driven", "rules": rules}, allow_unicode=True))
    report, stage = check.collect(joined)
    diff = _finding(report, "产物写法与基础版的差异")
    assert len(diff) == 1 and diff[0].startswith("rules.design")
    assert stage.line == "日常巡检：一切一致"


def test_engine_copy_is_reported(joined):
    write(joined, "backend/judge.py", "def load_rules():\n    return []\n")
    report, _ = check.collect(joined)
    assert _finding(report, "判断引擎副本") == ["backend/judge.py"]


def test_identical_base_rule_is_duplicate_override_is_not(joined):
    same = BASE_JUDGMENTS[0]
    changed = dict(BASE_JUDGMENTS[1], question="收紧版")
    write(joined, "openspec/judgments.yaml", yaml.safe_dump([same, changed], allow_unicode=True))
    report, _ = check.collect(joined)
    assert _finding(report, "与通用规则重复的项目规则") == [same["id"]]


def test_generic_words_in_project_lexicon(joined):
    write(joined, "openspec/copy-lexicon.yaml", "labels:\n  - 重试\n  - 书家\n")
    report, _ = check.collect(joined)
    assert _finding(report, "项目词表中已在通用词表的词") == ["重试"]


@pytest.mark.parametrize(("line", "ref"), [
    ("uv tool install rulemason==0.8.0", "0.8.0"),
    ("uv tool install git+https://github.com/rulemason/rulemason@v0.8.0", "v0.8.0"),
    ("- uses: actions/checkout@v4\n    with:\n      repository: rulemason/rulemason\n      ref: v0.8.0", "v0.8.0"),
])
def test_ci_install_ref_is_identified(joined, line, ref):
    write(joined, ".github/workflows/ci.yml", f"steps:\n  - run: {line}\n")
    report, _ = check.collect(joined)
    assert dict(report.facts)["CI"] == f".github/workflows/ci.yml 钉 {ref}"


@pytest.mark.parametrize("line", [
    "uv tool install git+https://github.com/someone/other-tool@v0.7.8",
    "pip install foo-rulemason==1.0",
    "uv tool install rulemason",        # 装了但没钉版本
])
def test_ci_install_from_other_source_is_not_a_pin(joined, line):
    write(joined, ".github/workflows/ci.yml", f"steps:\n  - run: {line}\n")
    report, _ = check.collect(joined)
    assert dict(report.facts)["CI"] == "有，未引用 rulemason"


def test_uncommitted_new_files_are_seen(bare):
    write(bare, "ruff.toml", 'extend = ".rulemason/lint/ruff-base.toml"\n')      # 新建未提交
    report, _ = check.collect(bare)
    assert report.layers["接入 lint 继承"] == []


def test_check_is_read_only_and_keeps_user_files(joined):
    write(joined, "notes/user-work.md", "keep my in-progress note\n")
    before = git(joined, "status", "--porcelain")
    check.run(joined)
    assert git(joined, "status", "--porcelain") == before
    assert (joined / "notes/user-work.md").read_text(encoding="utf-8") == "keep my in-progress note\n"


def test_check_works_without_git(tmp_path):
    root = tmp_path / "plain"
    write(root, "app/main.py", "x = 1\n")
    _install(root, [])
    text, _ = check.run(root)
    assert "无 git，无法统计" in text


# ---------- 6. rulemason 仓库本身（3.3） ----------

def test_rulemason_repo_checks_direct_rules_without_copies():
    report, _ = check.collect(shared.SOURCE_ROOT)
    assert _finding(report, "判断引擎副本") == []
    assert "接入 生成副本" not in report.layers
    assert report.layers["接入 代码规矩与 gates"] == []


# ---------- 7. 审查补充 ----------

def test_invalid_version_in_manifest_is_reported(joined):
    write(joined, ".rulemason.yaml", "version: 1\nrulemason: main\ntools: []\n")
    report, stage = check.collect(joined)
    assert any("版本格式无效" in m for m in report.layers["接入 工具入口"])
    assert stage.line == "接入：先修正 .rulemason.yaml"


def test_crlf_checkout_is_not_a_hand_edit(joined):
    path = joined / ".rulemason/rules/code-style.md"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert check.collect(joined)[0].layers["接入 生成副本"] == []


def test_chinese_paths_are_listed_and_counted(joined):
    write(joined, "文档/说明.py", "x = 1\n")
    assert "文档/说明.py" in shared.list_files(joined)
    assert shared.dirty_files(joined) == ["文档/说明.py"]


# ---------- 8. 副本被 .gitignore 忽略（cli-migration-fixes） ----------

def test_ignored_copies_fail_until_allowed(joined):
    _install(joined, ["claude"])
    write(joined, ".gitignore", ".claude/\n")
    report, _ = check.collect(joined)
    ignored = [m for m in report.layers["接入 生成副本"] if "被 .gitignore 忽略" in m]
    assert "被 .gitignore 忽略，无法随项目提交：.claude/skills/rulemason/SKILL.md" in ignored
    assert len(ignored) == len(shared.SKILL_FILES)
    assert check.exit_code(report) == 1

    write(joined, ".gitignore", ".claude/*\n!.claude/skills/\n.claude/skills/*\n!.claude/skills/rulemason/\n")
    report, _ = check.collect(joined)
    assert not any("被 .gitignore 忽略" in m for m in report.layers["接入 生成副本"])


def test_tracked_copies_matching_ignore_rule_are_reported(joined):
    _install(joined, ["claude"])
    commit(joined)                                   # 副本已入仓
    write(joined, ".gitignore", ".claude/\n")         # 之后才加忽略规则:update 新增的副本会进不了仓库
    report, _ = check.collect(joined)
    assert any("被 .gitignore 忽略" in m for m in report.layers["接入 生成副本"])


def test_ignore_check_skipped_without_git(tmp_path):
    root = tmp_path / "plain"
    _install(root, ["claude"])
    write(root, ".gitignore", ".claude/\n")
    report, _ = check.collect(root)
    assert report.layers["接入 生成副本"] == []


# ---------- 项目边界：多仓库工作区与第三方目录 ----------


def _sub_repos(ws):
    """3 个独立仓库各带 lint 配置，外加一份第三方 jQuery。"""
    for name, rel, text in (
        ("app-a", "pyproject.toml", '[tool.ruff.lint]\nselect = ["E"]\n'),
        ("app-b", "eslint.config.js", "export default [];\n"),
        ("app-c", "ruff.toml", "line-length = 100\n"),
    ):
        write(ws / name, rel, text)
        git_init(ws / name)
    write(ws, "static/bower_components/jquery/src/.eslintrc.json", "{}\n")


def test_workspace_sub_repos_and_vendor_code_are_skipped(tmp_path):
    ws = tmp_path / "ws"
    write(ws, "openspec/config.yaml", "schema: spec-driven\n")
    write(ws, "main.py", "x = 1\n")
    assert init.run(ws, "claude", True) == 0                # 根目录没有 git
    before, _ = check.collect(ws)
    _sub_repos(ws)
    others = {rel: (ws / rel).read_text(encoding="utf-8") for rel in (
        "app-a/pyproject.toml", "app-b/eslint.config.js", "app-c/ruff.toml", "static/bower_components/jquery/src/.eslintrc.json")}
    assert init.run(ws, "claude", True) == 0                # 再跑一次：子仓库与第三方代码一个都不写
    assert {rel: (ws / rel).read_text(encoding="utf-8") for rel in others} == others
    after, stage = check.collect(ws)
    assert after.layers["接入 lint 继承"] == [] and check.exit_code(after) == check.exit_code(before)
    assert dict(after.facts)["跳过"] == "app-a（另一个仓库）、app-b（另一个仓库）、app-c（另一个仓库）、static/bower_components（第三方目录）"
    assert dict(after.facts)["项目根"] == str(ws)
    assert stage.stage != "接入"


def test_skipped_label_truncates_after_ten():
    skipped = [(f"repo-{i:02d}", "另一个仓库") for i in range(12)]
    label = check.skipped_label(skipped)
    assert label.endswith("等共 12 个") and "repo-09" in label and "repo-10" not in label
    assert check.skipped_label([]) == "—"


# ---------- 结论行与标记块校验（用真实 init 出来的项目） ----------


@pytest.fixture
def inited(tmp_path):
    root = tmp_path / "proj"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    write(root, "app/main.py", "x = 1\n")
    assert init.run(root, "claude", True) == 0
    commit(root)
    return root


def _set_recorded_version(root, version: str) -> None:
    manifest = shared.read_manifest(root)
    manifest["rulemason"] = version
    write_manifest(root, manifest)


def _fill_project_info(root):
    agents = root / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace("待 /rulemason 补充", "已补").replace("（自动识别，请确认）", ""), encoding="utf-8")


def test_edited_block_is_reported_and_restored_by_update(inited, capsys):
    agents = inited / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace("所有语言通用原则", "我改了这里"), encoding="utf-8")
    report, stage = check.collect(inited)
    assert f"{check.STALE_BLOCK}：AGENTS.md 的 code-style" in report.layers["接入 生成副本"]
    assert stage.line == "接入：运行 rulemason update" and check.exit_code(report) == 1
    capsys.readouterr()
    assert update.run(inited) == 0
    assert "标记块：AGENTS.md 的 code-style" in capsys.readouterr().out
    assert "我改了这里" not in agents.read_text(encoding="utf-8")


def test_block_differences_after_upgrade_are_not_edits(inited):
    _set_recorded_version(inited, "0.1.0")
    agents = inited / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace("所有语言通用原则", "旧版本的措辞"), encoding="utf-8")
    report, _ = check.collect(inited)
    assert not any(item.startswith(check.STALE_BLOCK) for item in report.layers["接入 生成副本"])


def test_judge_label_without_git(tmp_path):
    assert check.judge_label(tmp_path, 5) == "可选，未启用（需要 git 与至少 3 个已归档 change；当前没有 git）"


# ---------- 动作代码与 check --json（agent-io） ----------

ACTION_SETUPS = {
    # 动作代码 → (场景, 文字版第一行, 退出码)
    "fix_manifest": (lambda root: write(root, ".rulemason.yaml", "tools: [claude]\n"), "接入：先修正 .rulemason.yaml", 1),
    "init": (lambda root: (root / ".rulemason.yaml").unlink(), "接入：运行 rulemason init", 1),
    "fix_gitignore": (lambda root: write(root, ".gitignore", ".claude/\n"), "接入：修改 .gitignore，放行 skills/rulemason/（副本要随项目提交）", 1),
    "update": (lambda root: write(root, ".rulemason/rules/code-style.md", "改过\n"), "接入：运行 rulemason update", 1),
    "fill_project_info": (lambda root: None, "补项目信息：在 AI 工具中运行 /rulemason", 0),
    "upgrade_machine": (lambda root: (_fill_project_info(root), _set_recorded_version(root, "99.0.0")), "日常巡检：先升级本机 rulemason", 0),
    "manual_lint": (
        lambda root: (_fill_project_info(root), write(root, ".eslintrc.json", "{}\n"), update.run(root, yes=True)),
        "接入：手动修改 .eslintrc.json（rulemason update 改不了）：.eslintrc.json 是旧格式 .eslintrc，rulemason 只接扁平配置：未修改",
        1,
    ),
    "none": (_fill_project_info, "日常巡检：一切一致", 0),
}


@pytest.mark.parametrize("code", list(ACTION_SETUPS))
def test_action_code_and_first_line(inited, code):
    """每个动作代码一个场景：文字版第一行、JSON 的 next 与退出码一致。"""
    setup, line, expected_exit = ACTION_SETUPS[code]
    setup(inited)
    out, exit_code = check.run(inited, as_json=True)
    data = json.loads(out)
    assert data["next"]["code"] == code
    assert data["text"].splitlines()[0] == line == f"{data['next']['stage']}：{data['next']['action']}"
    assert data["exit_code"] == exit_code == expected_exit


def test_check_json_matches_text_report(inited):
    text, code = check.run(inited)
    data = json.loads(check.run(inited, as_json=True)[0])
    assert data["schema"] == 1 and data["root"] == str(inited)
    assert data["next"] == {"stage": "补项目信息", "action": "在 AI 工具中运行 /rulemason", "code": "fill_project_info"}
    assert data["text"] == text and data["exit_code"] == code == 0
    assert data["facts"]["项目根"] and "接入 生成副本" in data["layers"] and "rulemason 版本" in data["findings"]


# ---------- 检查点提示（openspec-operations） ----------

def test_operations_missing_is_a_finding_not_a_failure(inited):
    _fill_project_info(inited)
    drop_operations(inited)
    report, nxt = check.collect(inited)
    assert _finding(report, "检查点提示与基础版的差异") == ["openspec/config.yaml 没有 operations（apply / archive 时给 AI 的检查点提示）"]
    assert check.exit_code(report) == 0 and nxt.stage != "接入"


def test_operations_missing_items_are_listed(inited):
    data = yaml.safe_load((inited / "openspec/config.yaml").read_text(encoding="utf-8"))
    data["operations"]["apply"]["guidance"] = ["项目自己的提示"]
    write(inited, "openspec/config.yaml", yaml.safe_dump(data, allow_unicode=True))
    items = _finding(check.collect(inited)[0], "检查点提示与基础版的差异")
    assert len(items) == 1 and items[0].startswith("operations.apply 缺少：写代码前与写完代码后")


def test_operations_consistent_after_init(inited):
    assert _finding(check.collect(inited)[0], "检查点提示与基础版的差异") == []


def test_source_repo_operations_point_to_rules():
    items = [i for body in check.base_operations(shared.SOURCE_ROOT).values() for i in body["guidance"]]
    assert all("rules/workflow-gates.md" in i and ".rulemason/" not in i for i in items)


@pytest.mark.parametrize(("operations", "expected"), [
    ("operations:\n", "openspec/config.yaml 的 operations 为空或不是映射：请手动补上基础条目"),
    ("operations:\n  apply: [x]\n  archive:\n    guidance: 文字\n", "operations.apply 缺少：写代码前与写完代码后"),
])
def test_operations_odd_shapes_are_reported_not_crashing(inited, operations, expected):
    drop_operations(inited)
    config = inited / "openspec/config.yaml"
    write(inited, "openspec/config.yaml", config.read_text(encoding="utf-8") + operations)
    items = _finding(check.collect(inited)[0], "检查点提示与基础版的差异")
    assert items[0].startswith(expected)
    if operations != "operations:\n":
        assert len(items) == 2 and items[1].startswith("operations.archive 缺少：")    # guidance 是字符串也算缺少


# ---------- 项目配置写错时的可读提示（readable-config-errors） ----------

@pytest.mark.parametrize(("rel", "text", "expected"), [
    ("openspec/config.yaml", "schema: spec-driven\ncontext: a: b\n", "openspec/config.yaml 不是合法的 YAML（第 2 行：mapping values are not allowed here）"),
    ("openspec/config.yaml", "- a\n- b\n", "openspec/config.yaml 的顶层应是映射"),
    ("openspec/judgments.yaml", "id: x\n", "openspec/judgments.yaml 的顶层应是列表"),
    ("openspec/copy-lexicon.yaml", "labels: [a\n", "openspec/copy-lexicon.yaml 不是合法的 YAML（第 2 行："),
])
def test_bad_project_yaml_raises_readable_error(inited, rel, text, expected):
    write(inited, rel, text)
    with pytest.raises(ValueError) as exc:
        check.run(inited)
    assert str(exc.value).startswith(expected)


def test_empty_project_yaml_uses_default(inited):
    write(inited, "openspec/judgments.yaml", "")
    write(inited, "openspec/copy-lexicon.yaml", "# 只有注释\n")
    check.run(inited)


@pytest.mark.parametrize("argv", [["check"], ["check", "--json"]])
def test_cli_reports_bad_config_without_traceback(inited, monkeypatch, argv):
    """外层把错误转成字符串退出码（非 0、不打印 traceback）；其他异常会直接让测试失败。"""
    write(inited, "openspec/config.yaml", "schema: spec-driven\ncontext: a: b\n")
    monkeypatch.chdir(inited)
    assert run_cli(*argv).startswith("rulemason check 失败：openspec/config.yaml 不是合法的 YAML（第 2 行")


def test_non_utf8_project_yaml_names_the_file(inited):
    (inited / "openspec/copy-lexicon.yaml").write_bytes("labels: [按钮]\n".encode("gbk"))
    with pytest.raises(check.ConfigError, match="openspec/copy-lexicon.yaml 不是 UTF-8 编码"):
        check.run(inited)


def test_yaml_error_without_mark_omits_line(inited, monkeypatch):
    write(inited, "openspec/judgments.yaml", "- id: x\n")

    def boom(_text):
        raise shared.yaml.YAMLError("坏了")
    monkeypatch.setattr(shared.yaml, "safe_load", boom)
    with pytest.raises(check.ConfigError) as exc:
        shared.read_yaml(inited / "openspec/judgments.yaml", [])
    assert str(exc.value) == "openspec/judgments.yaml 不是合法的 YAML（坏了）"


# ---------- React 识别与 ESLint 巡检（shared-react-rules） ----------

@pytest.mark.parametrize(("key", "is_react"), [("dependencies", True), ("devDependencies", True), ("peerDependencies", True), ("scripts", False)])
def test_react_dirs_read_dependency_sections(tmp_path, key, is_react):
    write(tmp_path, "studio/package.json", json.dumps({key: {"react": "19.0.0"}}))
    write(tmp_path, "package.json", '{"dependencies": {"vite": "6"}}')
    assert check.react_dirs(tmp_path, ["package.json", "studio/package.json"]) == (["studio"] if is_react else [])


def test_bad_package_json_names_the_file(tmp_path):
    write(tmp_path, "web/package.json", "{")
    with pytest.raises(check.ConfigError, match="web/package.json 不是合法的 JSON"):
        check.react_dirs(tmp_path, ["web/package.json"])


def test_react_dir_without_eslint_is_a_finding(inited):
    _fill_project_info(inited)
    write(inited, "studio/package.json", REACT_PACKAGE)
    write(inited, "frontend/package.json", '{"dependencies": {"vue": "^3"}, "devDependencies": {"eslint": "^9"}}\n')
    write(inited, "frontend/eslint.config.mjs", 'import base from "../.rulemason/lint/eslint-base.mjs";\nexport default [{ rules: { ...base } }];\n')
    assert update.run(inited, yes=True) == 0                                # 后加的 React 目录要 update 才会引用 react.md
    report, _ = check.collect(inited)
    assert _finding(report, "React 目录缺少 ESLint") == ["studio：是 React 目录，但它和上级目录都没有 ESLint 配置"]
    assert dict(report.facts)["前端目录"] == "frontend、studio（React）"
    assert check.exit_code(report) == 0                                   # 退出码不因这项巡检改变


@pytest.mark.parametrize("config_dir", ["studio", "."])
def test_eslint_in_dir_or_parent_counts(inited, config_dir):
    write(inited, "studio/package.json", REACT_PACKAGE)
    write(inited, f"{config_dir}/eslint.config.mjs", "export default [];\n")
    assert _finding(check.collect(inited)[0], "React 目录缺少 ESLint") == []


@pytest.mark.parametrize("text", ["[]", '"react"', '{"dependencies": ["react"]}', '{"dependencies": "react"}'])
def test_react_dirs_ignore_odd_shapes(tmp_path, text):
    write(tmp_path, "package.json", text)
    assert check.react_dirs(tmp_path, ["package.json"]) == []


def test_root_react_project_is_marked(inited):
    write(inited, "package.json", REACT_PACKAGE)
    assert check.react_dirs(inited, ["package.json"]) == ["."]
    assert dict(check.collect(inited)[0].facts)["前端目录"] == ".（React）"


def test_judgment_without_id_is_readable(inited, monkeypatch):
    write(inited, "openspec/judgments.yaml", "- id: a\n- question: 没有 id\n")
    monkeypatch.chdir(inited)
    assert run_cli("check") == "rulemason check 失败：openspec/judgments.yaml 第 2 条不是带 id 的映射"


# ---------- rulekit 0.5 遗留文件：不识别，当作未接入 ----------

def test_rulekit_manifest_is_treated_as_not_joined(bare):
    write(bare, ".rulekit.yaml", 'version: 1\ntools: [claude]\nrulekit: 0.5.2\nfiles: {}\n')
    write(bare, ".rulekit/rules/code-style.md", "旧副本\n")
    out, code = check.run(bare, as_json=True)
    data = json.loads(out)
    assert data["next"]["code"] == "init" and code == 1
    assert "迁移" not in data["text"] and "旧名残留" not in data["text"] and "旧接入方式" not in data["text"]


def test_old_names_outside_blocks_are_not_reported(joined):
    """旧接入引用与旧名（jev-judge、.rulekit/、skills/rulekit）都不再是巡检项，结论与没有它们时相同。"""
    baseline = json.loads(check.run(joined, as_json=True)[0])["next"]
    write(joined, "AGENTS.md", AGENTS_OK + '"../rulekit/rules/code-style.md"\n判断：`jev-judge --change x`\n')
    write(joined, ".gitignore", "!.claude/skills/rulekit/\n")
    out, code = check.run(joined, as_json=True)
    data = json.loads(out)
    assert code == 0 and data["next"] == baseline
    for word in ("旧名残留", "旧接入方式", "../rulekit/", "jev-judge", "skills/rulekit", "迁移"):
        assert word not in data["text"], word


# ---------- 判断一行提示配置 key（init-ux-1） ----------

@pytest.mark.parametrize(("has_key", "expected"), [(False, "本机未配置 key：运行 rulemason key"), (True, "要启用时在 AI 工具中运行 /rulemason")])
def test_judge_label_mentions_key_when_conditions_met(joined, monkeypatch, has_key, expected):
    _archive(joined, 3)
    monkeypatch.setattr(check, "api_key", lambda: "k" if has_key else "")
    label = check.judge_label(joined, 3)
    assert expected in label
    assert (shared.KEY_URL in label) is not has_key


# ---------- 识别与检查口径（init-ux-2） ----------

def test_frontend_dirs_need_ui_framework(tmp_path):
    write(tmp_path, "package.json", '{"devDependencies": {"turbo": "^2"}}\n')
    write(tmp_path, "apps/api/package.json", '{"dependencies": {"express": "^4"}}\n')
    write(tmp_path, "apps/web/package.json", '{"dependencies": {"vue": "^3"}}\n')
    write(tmp_path, "frontend/package.json", '{"devDependencies": {"vite": "^6", "typescript": "^5"}}\n')
    files = ["package.json", "apps/api/package.json", "apps/web/package.json", "frontend/package.json", "frontend/index.html"]
    assert check.frontend_dirs(tmp_path, files) == ["apps/web", "frontend"]
    assert check.react_dirs(tmp_path, files) == []


def test_prototype_in_change_is_not_project_code(inited):
    write(inited, "openspec/changes/add-x/prototype/package.json", REACT_PACKAGE)
    report, _ = check.collect(inited)
    assert dict(report.facts)["前端目录"] == "—" and dict(report.facts)["跳过"] == "—"
    assert _finding(report, "React 目录缺少 ESLint") == []


def test_broken_ruff_ref_is_reported_separately(joined):
    write(joined, "ruff.toml", 'extend = "../rulekit/lint/ruff-base.toml"\n')
    report, _ = check.collect(joined)
    assert report.layers["接入 lint 继承"] == ["ruff.toml 引用的基础配置不存在：../rulekit/lint/ruff-base.toml"]
    assert check.exit_code(report) == 1


def test_broken_eslint_ref_next_to_correct_one_is_manual(inited):
    _fill_project_info(inited)
    write(inited, "web/eslint.config.js", 'import a from "../.rulemason/lint/eslint-base.mjs";\nimport b from "../../gone/.rulekit/lint/eslint-base.mjs";\nexport default [{ rules: { ...a, ...b } }];\n')
    assert update.run(inited, yes=True) == 0                              # 补上 eslint-base 副本；两条引用并存的配置不改
    report, nxt = check.collect(inited)
    [item] = report.layers["接入 lint 继承"]
    assert item.splitlines()[0].startswith("web/eslint.config.js 重复引入基础规则（../../gone/.rulekit/lint/eslint-base.mjs")
    assert '删去第 2 行 import b from "../../gone/.rulekit/lint/eslint-base.mjs";' in item
    assert "再在第 3 行去掉对 b 的使用：export default [{ rules: { ...a, ...b } }];" in item      # 这行还有别的内容，不能整行删
    assert nxt.code == "manual_lint" and nxt.action == f"手动修改 web/eslint.config.js（rulemason update 改不了）：{item.splitlines()[0]}"


def _age_copy(root, rel: str, version: str) -> None:
    """模拟旧版本留下的副本：内容与当前共享版本不同，清单记录的是它自己的校验值。"""
    write(root, rel, "旧版本的内容\n")
    manifest = shared.read_manifest(root)
    manifest["files"][rel] = shared.sha256_text("旧版本的内容\n")
    manifest["rulemason"] = version
    write_manifest(root, manifest)


def test_copies_behind_fails_until_update(inited):
    _fill_project_info(inited)
    _age_copy(inited, ".rulemason/rules/code-style.md", "0.1.0")
    report, nxt = check.collect(inited)
    assert any(item.startswith(f"{check.BEHIND}（1 个文件；") for item in report.layers["接入 生成副本"])
    assert nxt.code == "update" and check.exit_code(report) == 1
    assert update.run(inited) == 0
    report, nxt = check.collect(inited)
    assert nxt.line == "日常巡检：一切一致" and check.exit_code(report) == 0


def test_newer_record_is_not_copies_behind(inited):
    _fill_project_info(inited)
    _age_copy(inited, ".rulemason/rules/code-style.md", "99.0.0")
    report, nxt = check.collect(inited)
    assert not any(item.startswith(check.BEHIND) for item in report.layers["接入 生成副本"])
    assert nxt.code == "upgrade_machine"


def test_broken_eslint_ref_alone_is_fixable_by_update(inited):
    _fill_project_info(inited)
    write(inited, "web/eslint.config.js", 'import old from "../../gone/eslint-base.mjs";\nexport default [{ rules: { ...old } }];\n')
    assert update.run(inited) == 0                                        # 先补 eslint-base 副本；非交互不写用户配置
    report, nxt = check.collect(inited)
    assert report.layers["接入 lint 继承"] == ["web/eslint.config.js 引用的基础配置不存在：../../gone/eslint-base.mjs"]
    assert nxt.code == "update" and check.exit_code(report) == 1          # update --yes 能改正路径，不是手动项


def test_version_lag_without_copy_record_does_not_claim_same_content(inited):
    _fill_project_info(inited)
    manifest = shared.read_manifest(inited)
    manifest["rulemason"] = "0.1.0"
    del manifest["files"]
    write_manifest(inited, manifest)
    report, nxt = check.collect(inited)
    assert "副本内容相同" not in nxt.action
    assert not any(check.VERSION_ONLY in item for item in _finding(report, "rulemason 版本"))


def test_enabling_judge_needs_copy_voice_copy(joined):
    write(joined, "openspec/judgments.yaml", "[]\n")                      # 版本不变，只是启用了判断
    report, nxt = check.collect(joined)
    assert any(item.startswith(check.BEHIND) for item in report.layers["接入 生成副本"])
    assert nxt.code == "update"


# ---------- 最近归档的检查点记录（gates-evidence） ----------

def _archived_change(root, name: str, report: str | None) -> None:
    write(root, f"openspec/changes/archive/{name}/proposal.md", "# P\n")
    if report is not None:
        write(root, f"openspec/changes/archive/{name}/verification.md", report)


LATEST = "2026-11-01-migrate-x"


@pytest.mark.parametrize(("text", "expected"), [
    ("## 3. 独立审查\n两轮，无 block\n## 4. ruff 与测试\n432 passed\n", []),
    (None, [f"{LATEST}：没有 verification.md"]),
    ("## ruff 与测试\n通过\n", [f"{LATEST}：verification.md 没有写到审查"]),
    ("| 步骤 | 结果 |\n|---|---|\n| 独立审查第一轮 | review 5 |\n| 测试 | 44 项 OK |\n", []),
    ("Code review: pass. Tests: 12 passed.\n", []),
    ("独立review 两轮；单元test 12 项通过\n", []),
    ("Reviewed twice; testing done.\n", []),
    ("Preview looks fine on the latest build.\n", [f"{LATEST}：verification.md 没有写到审查、测试"]),
])
def test_latest_archive_gate_records(joined, text, expected):
    _archived_change(joined, "2026-10-01-old", None)                   # 更早的归档不看
    _archived_change(joined, LATEST, text)
    report, nxt = check.collect(joined)
    assert _finding(report, "最近归档的检查点记录") == expected
    assert check.exit_code(report) == 0 and nxt.line == "日常巡检：一切一致"


def test_same_day_archives_are_all_checked(joined):
    _archived_change(joined, "2026-11-03-a", "审查 pass；测试 pass\n")
    _archived_change(joined, "2026-11-03-b", None)
    _archived_change(joined, "misplaced", None)                        # 不是 openspec 生成的目录名，忽略
    assert check.gate_records(joined) == ["2026-11-03-b：没有 verification.md"]


def test_no_archive_means_no_gate_findings(tmp_path):
    assert check.gate_records(tmp_path) == []


# ---------- lint 继承链与旧位置副本（lint-fix-guidance） ----------

def _chain(root, files: dict[str, str]):
    """写入 {路径: 内容}，返回从 ruff.toml 走出的继承链。"""
    for rel, text in files.items():
        write(root, rel, text)
    return check.ruff_chain(root, "ruff.toml", (root / "ruff.toml").read_text(encoding="utf-8"))


def test_chain_two_and_three_levels(joined):
    two = _chain(joined, {"ruff.toml": 'extend = "a.toml"\n', "a.toml": "line-length = 100\n"})
    assert (two.end, [f for f, _ in two.links]) == ("tail", ["ruff.toml", "a.toml"])
    three = _chain(joined, {"a.toml": 'extend = "b.toml"\n', "b.toml": "line-length = 100\n"})
    assert (three.end, [f for f, _ in three.links]) == ("tail", ["ruff.toml", "a.toml", "b.toml"])


def test_chain_stops_outside_project_on_cycle_and_when_too_deep(joined):
    assert _chain(joined, {"ruff.toml": 'extend = "~/configs/ruff.toml"\n'}).end == "outside"
    cycle = _chain(joined, {"ruff.toml": 'extend = "a.toml"\n', "a.toml": 'extend = "ruff.toml"\n'})
    assert (cycle.end, cycle.ref) == ("cycle", "ruff.toml")
    deep = {f"c{i}.toml": f'extend = "c{i + 1}.toml"\n' for i in range(check.CHAIN_LIMIT + 1)}
    for rel, text in deep.items():
        write(joined, rel, text)
    deep_chain = check.ruff_chain(joined, "ruff.toml", 'extend = "c0.toml"\n')
    assert deep_chain.end == "deep" and len(deep_chain.links) == check.CHAIN_LIMIT


def test_chain_tail_inherits_base_counts_as_inherited(joined):
    write(joined, "ruff.toml", 'extend = "config/ruff-shared.toml"\n')
    write(joined, "config/ruff-shared.toml", 'extend = "../.rulemason/lint/ruff-base.toml"\n')
    report, _ = check.collect(joined)
    assert report.layers["接入 lint 继承"] == [] and check.exit_code(report) == 0


def test_select_on_chain_is_reported(joined):
    write(joined, "ruff.toml", 'extend = "config/ruff-shared.toml"\n')
    write(joined, "config/ruff-shared.toml", '[lint]\nselect = ["E"]\n')
    report, _ = check.collect(joined)
    [item] = report.layers["接入 lint 继承"]
    assert item.startswith("config/ruff-shared.toml 写了 select，会覆盖基础规则") and check.exit_code(report) == 1


def test_chain_tail_without_base_is_fixable_by_update(joined):
    write(joined, "ruff.toml", 'extend = "config/ruff-shared.toml"\n')
    write(joined, "config/ruff-shared.toml", "line-length = 100\n")
    report, nxt = check.collect(joined)
    assert report.layers["接入 lint 继承"] == ["ruff.toml 没有继承 .rulemason/lint/ruff-base.toml（继承链末端 config/ruff-shared.toml）"]
    assert nxt.code == "update"


def test_old_ruff_copy_same_content_is_fixable_by_update(joined):
    write(joined, "lint/ruff-base.toml", (joined / ".rulemason/lint/ruff-base.toml").read_text(encoding="utf-8"))
    write(joined, "ruff.toml", 'extend = "lint/ruff-base.toml"\n')
    report, nxt = check.collect(joined)
    assert report.layers["接入 lint 继承"] == ["ruff.toml 继承的是旧位置的基础配置副本：lint/ruff-base.toml"]
    assert nxt.code == "update" and nxt.line == "接入：运行 rulemason update"


def test_old_ruff_copy_edited_is_manual_with_diff_steps(joined):
    write(joined, "lint/ruff-base.toml", "[lint]\nselect = []\n")
    write(joined, "ruff.toml", 'extend = "lint/ruff-base.toml"\n')
    report, nxt = check.collect(joined)
    [item] = report.layers["接入 lint 继承"]
    assert item.splitlines()[0] == "ruff.toml 继承的 lint/ruff-base.toml 与基础配置不同（被改过或来自旧版本）：未修改"
    assert "先看差异：diff lint/ruff-base.toml .rulemason/lint/ruff-base.toml" in item and "改完运行：rulemason update" in item
    assert nxt.code == "manual_lint" and nxt.action == f"手动修改 ruff.toml（rulemason update 改不了）：{item.splitlines()[0]}"
    assert "\n" not in nxt.line


def test_missing_and_deep_and_unreadable_chain_notes_name_file_and_ref(joined):
    write(joined, "ruff.toml", 'extend = "config/gone.toml"\n')
    [item] = check.collect(joined)[0].layers["接入 lint 继承"]
    assert item.splitlines()[0] == "ruff.toml 继承的 config/gone.toml 不存在：未修改" and '位置：第 1 行 extend = "config/gone.toml"' in item

    for i in range(check.CHAIN_LIMIT + 1):
        write(joined, f"c{i}.toml", f'extend = "c{i + 1}.toml"\n')
    write(joined, "ruff.toml", 'extend = "c0.toml"\n')
    [item] = check.collect(joined)[0].layers["接入 lint 继承"]
    assert item.startswith(f"ruff.toml 的 ruff 继承链超过 {check.CHAIN_LIMIT} 层：未修改")

    (joined / "bad.toml").write_bytes(b"\xff\xfe")
    write(joined, "ruff.toml", 'extend = "bad.toml"\n')
    report, nxt = check.collect(joined)
    [item] = report.layers["接入 lint 继承"]
    assert item.startswith("ruff.toml 继承的 bad.toml 读不出") and nxt.code == "manual_lint"


def test_check_json_fields_unchanged_with_manual_lint(joined):
    write(joined, "ruff.toml", 'extend = "config/gone.toml"\n')
    data = json.loads(check.run(joined, as_json=True)[0])
    assert set(data) == {"schema", "root", "next", "facts", "layers", "findings", "exit_code", "text"}
    assert set(data["next"]) == {"stage", "code", "action"} and "\n" not in data["next"]["action"]


# ---------- 项目根：未接入仓库的子目录（init-at-cwd） ----------

def test_check_in_subdirectory_of_unjoined_repo_names_repo_root(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    git_init(repo)
    write(repo, "web/main.py", "x = 1\n")
    monkeypatch.chdir(repo / "web")
    run_cli("check")
    out = capsys.readouterr().out
    assert f"项目根：{(repo / 'web').resolve()}\n" in out                 # 「项目根」的值保持纯路径
    assert f"所在 git 仓库根：{repo.resolve()}\n" in out
    assert out.startswith("接入：运行 rulemason init")
