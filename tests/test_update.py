"""rulemason update 的测试：旧版本副本被刷新、手改被列出、标记块以外的内容与命令表不变。"""
from __future__ import annotations

import json

import pytest
import yaml
from conftest import (
    commit,
    drop_operations,
    git,
    git_init,
    snapshot,
    write,
    write_manifest,
)

from rulemason import __version__, check, init, shared, update


def _old_version_project(tmp_path):
    """用 init 接入后，伪造成旧版本：副本与标记块是旧内容（校验值对得上），另有一处手改。"""
    root = tmp_path / "proj"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    write(root, "app/main.py", "x = 1\n")
    assert init.run(root, "claude", True) == 0

    manifest = shared.read_manifest(root)
    write(root, ".rulemason/rules/code-style.md", "旧版本九条\n")                      # 旧版本副本
    manifest["files"][".rulemason/rules/code-style.md"] = shared.sha256_text("旧版本九条\n")
    manifest["rulemason"] = "0.4.0"
    write_manifest(root, manifest)
    write(root, ".claude/skills/rulemason/SKILL.md", "有人手改\n")                     # 手改，校验值对不上

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    agents = agents.replace("开始相关代码工作前", "旧版块内文字。开始相关代码工作前")
    agents = agents.replace("| ruff | 无，跳过 |", "| ruff | 自定义 |").replace("待 /rulemason 补充：一两句话", "已补的简介，原")
    write(root, "AGENTS.md", agents)
    commit(root)
    return root


def test_update_refreshes_copies_and_lists_hand_edits(tmp_path, capsys):
    root = _old_version_project(tmp_path)
    before = (root / "AGENTS.md").read_text(encoding="utf-8")

    assert update.run(root) == 0

    src = shared.shared_root()
    assert (root / ".rulemason/rules/code-style.md").read_text(encoding="utf-8") == (src / "rules/code-style.md").read_text(encoding="utf-8")
    assert (root / ".claude/skills/rulemason/SKILL.md").read_text(encoding="utf-8") == (src / "skills/rulemason/SKILL.md").read_text(encoding="utf-8")
    manifest = shared.read_manifest(root)
    assert manifest["rulemason"] == __version__
    assert manifest["files"][".rulemason/rules/code-style.md"] == shared.sha256_file(root / ".rulemason/rules/code-style.md")

    out = capsys.readouterr().out
    hand_edits = out.split("已按共享版本刷新：", 1)[1]
    assert ".claude/skills/rulemason/SKILL.md" in hand_edits and ".rulemason/rules/code-style.md" not in hand_edits

    after = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "旧版块内文字" not in after
    assert after == before.replace("旧版块内文字。", "")                              # 只有块内变了
    assert "| ruff | 自定义 |" in after and "已补的简介" in after


def test_update_lists_missing_blocks_as_pending_without_yes(tmp_path, monkeypatch, capsys):
    root = _old_version_project(tmp_path)
    write(root, "AGENTS.md", "# 自写\n")
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(AssertionError("非交互不应提问")))

    assert update.run(root) == 0

    assert (root / "AGENTS.md").read_text(encoding="utf-8") == "# 自写\n"
    out = capsys.readouterr().out
    assert "补齐计划（你自己的文件）：AGENTS.md" in out and "待补齐：未写入" in out


def _joined_before_python(tmp_path):
    """接入时还没有 Python 代码的项目：没有生成 ruff 配置。"""
    root = tmp_path / "proj"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    write(root, "README.md", "x\n")
    assert init.run(root, "claude", True) == 0
    return root


def test_update_yes_fills_missing_ruff_config(tmp_path, capsys):
    root = _joined_before_python(tmp_path)
    assert not (root / "ruff.toml").exists()
    write(root, "app/main.py", "x = 1\n")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    capsys.readouterr()

    assert update.run(root) == 0                                  # 非交互、没有 --yes：只列出
    assert not (root / "ruff.toml").exists()
    assert "ruff.toml" in capsys.readouterr().out

    assert update.run(root, yes=True) == 0
    assert '.rulemason/lint/ruff-base.toml' in (root / "ruff.toml").read_text(encoding="utf-8")
    assert (root / "AGENTS.md").read_text(encoding="utf-8").count("| ruff |") == agents.count("| ruff |")   # 命令表不被 update 改动


def test_update_without_manifest_stops(tmp_path, capsys):
    root = tmp_path / "proj"
    write(root, "app/main.py", "x = 1\n")
    assert update.run(root) == 1
    assert "先运行 rulemason init" in capsys.readouterr().out
    assert not (root / ".rulemason").exists()


def test_update_refreshes_claude_block_only(tmp_path):
    root = _old_version_project(tmp_path)
    write(root, "CLAUDE.md", "自写说明\n\n<!-- rulemason:claude -->\n@AGENTS.md\n<!-- /rulemason:claude -->\n")
    assert update.run(root) == 0
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("自写说明\n\n<!-- rulemason:claude -->\n@AGENTS.md\n@.rulemason/rules/code-style.md\n")


def test_update_yes_replaces_lone_agents_import_with_claude_block(tmp_path, capsys):
    root = _old_version_project(tmp_path)
    write(root, "CLAUDE.md", "@AGENTS.md\n\n自写说明\n")                               # claude 块被删，只剩 remove 留下的那一行
    assert update.run(root, yes=True) == 0
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- rulemason:claude -->\n@AGENTS.md\n") and text.endswith("-->\n\n自写说明\n")
    assert text.count("@AGENTS.md") == 1 and "块外已导入 AGENTS.md" not in capsys.readouterr().out


@pytest.mark.parametrize("case", ["self", "invalid"])
def test_update_stops_without_writing(tmp_path, case, capsys):
    if case == "self":
        before = git(shared.SOURCE_ROOT, "status", "--porcelain")
        assert update.run(shared.SOURCE_ROOT) == 1
        assert git(shared.SOURCE_ROOT, "status", "--porcelain") == before
        return
    root = _old_version_project(tmp_path)
    write(root, ".rulemason.yaml", "tools: [claude]\n")
    stale = (root / ".rulemason/rules/code-style.md").read_text(encoding="utf-8")
    assert update.run(root) == 1
    assert (root / ".rulemason/rules/code-style.md").read_text(encoding="utf-8") == stale


def test_update_without_manifest_names_project_root(tmp_path, capsys):
    root = tmp_path / "proj"
    root.mkdir()
    assert update.run(root) == 1
    assert f"判断的项目根：{root}" in capsys.readouterr().out


def test_update_removes_old_template_copies(tmp_path, capsys):
    """0.6.1 及以前，每份 skill 副本带 3 个判断层模板；升级后不再生成，内容未改就删除。"""
    root = tmp_path / "proj"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    assert init.run(root, "claude", True) == 0
    manifest = shared.read_manifest(root)
    for name in ("judgments", "judge", "judge_cases"):
        rel = f".claude/skills/rulemason/templates/{name}.yaml"
        write(root, rel, f"旧模板 {name}\n")
        manifest["files"][rel] = shared.sha256_text(f"旧模板 {name}\n")
    write_manifest(root, manifest)

    assert update.run(root) == 0
    assert not (root / ".claude/skills/rulemason/templates").exists()
    assert not any("/templates/" in rel for rel in shared.read_manifest(root)["files"])


@pytest.mark.parametrize("answer", ["y", "n"])
def test_update_asks_before_filling_when_interactive(tmp_path, monkeypatch, answer):
    root = _old_version_project(tmp_path)
    write(root, "AGENTS.md", "# 自写\n")
    monkeypatch.setattr(update, "interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_: answer)
    assert update.run(root) == 0
    filled = "<!-- rulemason:code-style -->" in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert filled == (answer == "y")


def test_update_fill_skips_symlink_and_writes_the_rest(tmp_path, capsys):
    root = _old_version_project(tmp_path)
    (root / "CLAUDE.md").unlink()
    (root / "CLAUDE.md").symlink_to("AGENTS.md")                 # 常见写法：CLAUDE.md 指向 AGENTS.md
    (root / "ruff.toml").unlink()                                 # 另一处要补齐的配置
    assert update.run(root, yes=True) == 0
    assert "CLAUDE.md 是符号链接或在项目外，未补齐" in capsys.readouterr().out
    assert (root / "CLAUDE.md").is_symlink() and (root / "ruff.toml").is_file()


def test_partially_blocked_file_is_not_listed_as_overwritten(tmp_path, capsys):
    root = tmp_path / "proj"
    git_init(root)
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    assert init.run(root, "claude", True) == 0
    agents = root / "AGENTS.md"
    text = agents.read_text(encoding="utf-8").replace("所有语言通用原则", "改过")
    start, end = text.index("<!-- rulemason:workflow-gates -->"), text.index("<!-- /rulemason:workflow-gates -->")
    agents.write_text(text[:start] + text[end + len("<!-- /rulemason:workflow-gates -->"):], encoding="utf-8")   # 去掉一个块
    capsys.readouterr()
    assert update.run(root) == 0
    out = capsys.readouterr().out
    assert "标记块：AGENTS.md" not in out and "待补齐" in out


# ---------- update --dry-run（agent-io） ----------

def test_dry_run_lists_both_plans_without_writing(tmp_path, monkeypatch, capsys):
    root = _joined_before_python(tmp_path)
    write(root, "app/main.py", "x = 1\n")
    manifest = shared.read_manifest(root)
    write(root, ".rulemason/rules/code-style.md", "旧版本九条\n")
    manifest["files"][".rulemason/rules/code-style.md"] = shared.sha256_text("旧版本九条\n")
    manifest["rulemason"] = "0.1.0"
    write_manifest(root, manifest)
    commit(root)
    before = snapshot(root)
    capsys.readouterr()

    assert update.run(root, dry_run=True, as_json=True) == 0
    data = json.loads(capsys.readouterr().out)
    assert ".rulemason/rules/code-style.md" in data["managed"]["writes"] and ".rulemason.yaml" in data["managed"]["writes"]
    assert "ruff.toml" in data["fill"]
    assert set(data) == {"root", "managed", "fill", "notes"}
    monkeypatch.setattr(update, "interactive", lambda: True)          # 交互终端里也不提问
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("--dry-run 不应提问"))
    assert update.run(root, dry_run=True) == 0
    out = capsys.readouterr().out
    assert "补齐计划（你自己的文件）：" in out and "ruff.toml" in out and "未写任何文件" in out
    assert snapshot(root) == before


def test_dry_run_without_manifest_fails(tmp_path, capsys):
    root = tmp_path / "proj"
    write(root, "app/main.py", "x = 1\n")
    assert update.run(root, dry_run=True, as_json=True) == 1
    assert not (root / ".rulemason.yaml").exists()


# ---------- OpenSpec operations 提示（openspec-operations） ----------

def test_update_fills_operations_only_after_confirmation(tmp_path, capsys):
    root = _joined_before_python(tmp_path)
    drop_operations(root)
    assert "operations" not in (root / "openspec/config.yaml").read_text(encoding="utf-8")
    commit(root)
    capsys.readouterr()
    assert update.run(root, dry_run=True, as_json=True) == 0
    assert "openspec/config.yaml" in json.loads(capsys.readouterr().out)["fill"]
    assert update.run(root) == 0                                  # 非交互、没有 --yes：只列出
    assert "operations" not in (root / "openspec/config.yaml").read_text(encoding="utf-8")
    assert update.run(root, yes=True) == 0
    assert "operations" in yaml.safe_load((root / "openspec/config.yaml").read_text(encoding="utf-8"))


def test_update_treats_rulekit_manifest_as_not_joined(tmp_path, capsys):
    root = tmp_path / "proj"
    write(root, ".rulekit.yaml", 'version: 1\ntools: [claude]\nrulekit: 0.5.2\nfiles: {}\n')
    write(root, ".rulekit/rules/code-style.md", "旧副本\n")
    before = snapshot(root)
    assert update.run(root) == 1
    out = capsys.readouterr().out
    assert "先运行 rulemason init" in out and "迁移" not in out
    assert snapshot(root) == before


def test_update_drops_copies_the_project_no_longer_needs(tmp_path, capsys):
    """升级前的全量副本：没有 React 的项目 update 后删掉 react.md 与 eslint-base。"""
    root = _old_version_project(tmp_path)
    manifest = shared.read_manifest(root)
    for rel in ("rules/react.md", "lint/eslint-base.mjs"):
        text = (shared.SOURCE_ROOT / rel).read_text(encoding="utf-8")
        write(root, f".rulemason/{rel}", text)
        manifest["files"][f".rulemason/{rel}"] = shared.sha256_text(text)
    write_manifest(root, manifest)
    assert update.run(root) == 0
    assert not (root / ".rulemason/rules/react.md").exists() and not (root / ".rulemason/lint/eslint-base.mjs").exists()
    assert ".rulemason/rules/react.md" not in shared.read_manifest(root)["files"]
    assert ".rulemason/rules/react.md" in capsys.readouterr().out.split("更新的文件：", 1)[1]


# ---------- 没有 OpenSpec 与坏引用（init-ux-2） ----------

def test_update_without_openspec_says_checkpoints_are_off(tmp_path, capsys):
    root = tmp_path / "proj"
    git_init(root)
    write(root, "app/main.py", "x = 1\n")
    assert init.run(root, "claude", True) == 0
    capsys.readouterr()
    assert update.run(root) == 0
    assert capsys.readouterr().out.rstrip().splitlines()[-1] == shared.CHECKPOINTS_OFF


def test_update_yes_repoints_broken_ruff_extend(tmp_path):
    root = _joined_before_python(tmp_path)
    write(root, "app/main.py", "x = 1\n")
    write(root, "ruff.toml", 'extend = "../gone/ruff-base.toml"\n')
    assert update.run(root, yes=True) == 0
    assert (root / "ruff.toml").read_text(encoding="utf-8") == 'extend = ".rulemason/lint/ruff-base.toml"\n'
    assert check.collect(root)[0].layers["接入 lint 继承"] == []


# ---------- lint 继承链与旧位置副本（lint-fix-guidance） ----------

def test_update_fills_chain_tail_then_plans_nothing(tmp_path, capsys):
    root = _joined_before_python(tmp_path)
    write(root, "app/main.py", "x = 1\n")
    write(root, "ruff.toml", 'extend = "config/ruff-shared.toml"\n')
    write(root, "config/ruff-shared.toml", "line-length = 100\n")
    assert update.run(root, yes=True) == 0
    assert (root / "ruff.toml").read_text(encoding="utf-8") == 'extend = "config/ruff-shared.toml"\n'
    assert (root / "config/ruff-shared.toml").read_text(encoding="utf-8").startswith('extend = "../.rulemason/lint/ruff-base.toml"')
    capsys.readouterr()
    assert update.run(root, dry_run=True, as_json=True) == 0
    assert json.loads(capsys.readouterr().out)["fill"] == []


def test_update_repoints_old_copy(tmp_path, capsys):
    root = _joined_before_python(tmp_path)
    write(root, "app/main.py", "x = 1\n")
    write(root, "lint/ruff-base.toml", (shared.shared_root() / "lint/ruff-base.toml").read_text(encoding="utf-8"))   # 副本还没生成：与本机版本将写入的内容比
    write(root, "ruff.toml", 'extend = "lint/ruff-base.toml"\n')
    capsys.readouterr()
    assert update.run(root, yes=True) == 0
    out = capsys.readouterr().out
    assert (root / "ruff.toml").read_text(encoding="utf-8") == 'extend = ".rulemason/lint/ruff-base.toml"\n'
    assert "提示：" in out and "lint/ruff-base.toml 是基础配置的旧位置副本" in out
    assert check.collect(root)[0].layers["接入 lint 继承"] == []
