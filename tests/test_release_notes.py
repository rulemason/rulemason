"""scripts/release_notes.py 的测试：在临时 git 仓库里造提交与 tag，核对分组、去括号、无用户改动与第一个 tag。"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import commit, git, git_init

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_notes.py"
spec = importlib.util.spec_from_file_location("release_notes", SCRIPT)
release_notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_notes)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    git_init(root)
    commit(root, "feat: 首个版本（first，v0.1.0）")
    git(root, "tag", "v0.1.0")
    return root


def test_fix_and_archive_commits(repo):
    commit(repo, "fix(init): README 简介跳过语言切换与导航链接行（readme-intro-lang-line，v0.8.9）")
    commit(repo, "chore: 归档 readme-intro-lang-line，规格并入主 specs（rulekit-cli 修改 1 条）")
    git(repo, "tag", "v0.2.0")
    text = release_notes.notes(repo, "v0.2.0")
    assert "## 修复\n\n- README 简介跳过语言切换与导航链接行\n" in text
    assert "新功能" not in text
    assert "文档" not in text
    assert "归档" not in text
    assert "uv tool upgrade rulemason" in text
    assert text.endswith("[v0.1.0...v0.2.0](https://github.com/rulemason/rulemason/compare/v0.1.0...v0.2.0)\n")


def test_only_internal_commits(repo):
    commit(repo, "chore: 归档 x")
    commit(repo, "refactor(check): 抽出共用函数")
    git(repo, "tag", "v0.2.0")
    text = release_notes.notes(repo, "v0.2.0")
    assert text.startswith("本版本没有面向用户的改动。")
    assert "uv tool upgrade rulemason" in text
    assert "compare/v0.1.0...v0.2.0" in text


def test_first_tag_has_no_compare_link(repo):
    text = release_notes.notes(repo, "v0.1.0")
    assert "## 新功能\n\n- 首个版本\n" in text
    assert "compare" not in text


def test_first_tag_without_user_facing_commits(tmp_path):
    root = tmp_path / "repo"
    git_init(root)
    commit(root, "chore: 初始化")
    git(root, "tag", "v0.1.0")
    text = release_notes.notes(root, "v0.1.0")
    assert text.startswith("本版本没有面向用户的改动。")
    assert "compare" not in text


def test_script_prints_notes_and_checks_args(repo):
    run = subprocess.run([sys.executable, str(SCRIPT), "v0.1.0"], cwd=repo, capture_output=True, text=True)
    assert run.returncode == 0
    assert run.stdout == release_notes.notes(repo, "v0.1.0")
    bad = subprocess.run([sys.executable, str(SCRIPT)], cwd=repo, capture_output=True, text=True)
    assert bad.returncode != 0
    assert "用法" in bad.stderr


def test_squash_merge_suffix_is_stripped():
    subjects = ["fix(init): 修 A（change-a，v0.9.0） (#12)", "feat: 加 B (#13)"]
    text = release_notes.render("v0.9.0", "v0.8.9", subjects)
    assert "- 修 A\n" in text
    assert "- 加 B\n" in text
    assert "#1" not in text


def test_groups_in_fixed_order():
    subjects = ["docs(readme): 补英文版", "fix: 修 A", "feat(init): 加 B", "test: 补用例", "feat: 加 C"]
    text = release_notes.render("v1.1.0", "v1.0.0", subjects)
    assert text.index("## 新功能") < text.index("## 修复") < text.index("## 文档")
    assert "## 新功能\n\n- 加 B\n- 加 C\n" in text
    assert "补用例" not in text


def test_previous_tag_skips_later_tags(repo):
    commit(repo, "fix: a")
    git(repo, "tag", "v0.2.0")
    commit(repo, "fix: b")
    git(repo, "tag", "v0.10.0")
    assert release_notes.previous_tag(repo, "v0.10.0") == "v0.2.0"
    assert release_notes.previous_tag(repo, "v0.2.0") == "v0.1.0"


def test_unknown_tag_raises(repo):
    with pytest.raises(ValueError, match="v9.9.9"):
        release_notes.previous_tag(repo, "v9.9.9")
