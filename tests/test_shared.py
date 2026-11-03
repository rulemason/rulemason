"""shared.py 的测试：共享数据定位、manifest 读写、生成副本清单与列文件。"""
from __future__ import annotations

import pytest
from conftest import commit, git_init, write

from rulemason import __version__, shared

# ---------- 1. 定位共享数据 ----------

def test_shared_root_prefers_package_data(tmp_path, monkeypatch):
    packaged = tmp_path / "_shared"
    write(packaged, "rules/code-style.md", "包内版本\n")
    monkeypatch.setattr(shared, "PACKAGE_SHARED", packaged)

    assert shared.shared_root() == packaged


def test_shared_root_falls_back_to_source_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(shared, "PACKAGE_SHARED", tmp_path / "missing")

    assert shared.shared_root() == shared.SOURCE_ROOT
    assert (shared.shared_root() / "rules/code-style.md").is_file()


def test_shared_root_missing_everywhere_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(shared, "PACKAGE_SHARED", tmp_path / "missing")
    monkeypatch.setattr(shared, "SOURCE_ROOT", tmp_path)

    with pytest.raises(FileNotFoundError):
        shared.shared_root()


def test_generated_files_cover_rulemason_dir_and_selected_skills():
    files = shared.generated_files(["claude", "codex"])

    assert sum(1 for rel in files if rel.startswith(".rulemason/")) == 8
    assert files[".rulemason/rules/code-style.md"] == (shared.SOURCE_ROOT / "rules/code-style.md").read_text(encoding="utf-8")
    assert ".claude/skills/rulemason/SKILL.md" in files
    assert ".agents/skills/rulemason/SKILL.md" in files
    assert not any("/templates/" in rel for rel in files)                    # 判断层模板随安装包提供，不复制进项目


def test_cursor_and_codex_share_one_agents_skill():
    assert shared.skill_dirs(["cursor", "codex", "opencode"]) == [".agents/skills/rulemason"]
    assert shared.skill_dirs(["claude"]) == [".claude/skills/rulemason"]


# ---------- 2. manifest ----------

def test_manifest_round_trip_keeps_user_fields(tmp_path):
    write(tmp_path, ".rulemason.yaml", "version: 1\ntools: [codex]\nowner-note: keep\n")
    current = shared.read_manifest(tmp_path)

    text = shared.manifest_text(current, ["codex", "claude", "codex"], {"b": "2", "a": "1"})
    shared.write_text(tmp_path / ".rulemason.yaml", text)
    data = shared.read_manifest(tmp_path)

    assert data == {"version": 1, "tools": ["claude", "codex"], "owner-note": "keep", "rulemason": __version__, "files": {"a": "1", "b": "2"}}
    assert shared.manifest_text(data, ["claude", "codex"], {"a": "1", "b": "2"}) == text


def test_manifest_missing_returns_none(tmp_path):
    assert shared.read_manifest(tmp_path) is None


@pytest.mark.parametrize("text", ["tools: [codex]\n", "version: 2\ntools: []\n", "version: 1\ntools: [vim]\n", "- a\n"])
def test_invalid_manifest_raises(tmp_path, text):
    write(tmp_path, ".rulemason.yaml", text)

    with pytest.raises(shared.ManifestError):
        shared.read_manifest(tmp_path)


def test_write_refuses_symlink(tmp_path):
    outside = tmp_path / "outside.yaml"
    outside.write_text("keep\n", encoding="utf-8")
    link = tmp_path / "proj/.rulemason.yaml"
    link.parent.mkdir()
    link.symlink_to(outside)

    with pytest.raises(ValueError, match="符号链接"):
        shared.write_text(link, "version: 1\n")
    with pytest.raises(shared.ManifestError, match="符号链接"):
        shared.read_manifest(link.parent)
    assert outside.read_text(encoding="utf-8") == "keep\n"


def test_unsupported_tool_is_rejected():
    with pytest.raises(ValueError, match="不支持的工具"):
        shared.normalize_tools(["claude", "vim"])


# ---------- 3. 列文件 ----------

def _populate(root):
    write(root, "app/main.py", "x = 1\n")
    write(root, "node_modules/pkg/index.js", "x\n")
    write(root, ".venv/lib/site.py", "x\n")


def test_list_files_with_git_uses_gitignore(tmp_path):
    root = tmp_path / "proj"
    git_init(root)
    _populate(root)
    write(root, ".gitignore", "node_modules/\n.venv/\n")
    commit(root)
    write(root, "app/new.py", "y = 2\n")                    # 未提交的新文件也要看得到

    files = shared.list_files(root)

    assert "app/main.py" in files and "app/new.py" in files
    assert not any(f.startswith(("node_modules/", ".venv/")) for f in files)


def test_list_files_without_git_skips_fixed_dirs(tmp_path):
    root = tmp_path / "proj"
    _populate(root)

    files = shared.list_files(root)

    assert files == ["app/main.py"]
    assert shared.dirty_files(root) is None


def test_ignored_files_raises_when_git_fails(tmp_path):
    root = tmp_path / "not-a-repo"
    root.mkdir()
    with pytest.raises(ValueError, match="git check-ignore 失败"):
        shared.ignored_files(root, ["a.md"])


def test_ignored_files_handles_non_ascii_paths(tmp_path):
    root = tmp_path / "proj"
    git_init(root)
    write(root, ".gitignore", "文档/\n")
    assert shared.ignored_files(root, ["文档/说明.md", "app/main.py"]) == ["文档/说明.md"]


# ---------- 项目根：往上找最近的清单，以 git 仓库根为边界 ----------


def test_find_root_from_subdirectory(tmp_path):
    git_init(tmp_path / "proj")
    write(tmp_path / "proj", ".rulemason.yaml", "version: 1\ntools: []\n")
    sub = tmp_path / "proj/app/deep"
    sub.mkdir(parents=True)
    assert shared.find_root(sub) == tmp_path / "proj"


def test_find_root_stops_at_nested_repo(tmp_path):
    write(tmp_path / "ws", ".rulemason.yaml", "version: 1\ntools: []\n")      # 工作区根已接入、没有 git
    git_init(tmp_path / "ws/app-a")
    (tmp_path / "ws/app-a/src").mkdir()
    assert shared.find_root(tmp_path / "ws/app-a/src") == tmp_path / "ws/app-a"


def test_find_root_ignores_rulekit_manifest(tmp_path):
    write(tmp_path / "old", ".rulekit.yaml", 'version: 1\ntools: [claude]\nrulekit: 0.5.2\nfiles: {}\n')
    (tmp_path / "old/src").mkdir()
    assert shared.find_root(tmp_path / "old/src") == tmp_path / "old/src"      # 没有 git 也没有清单：停在起点


def test_find_root_stops_at_git_file(tmp_path):
    write(tmp_path / "wt", ".git", "gitdir: /elsewhere\n")                  # worktree 与子模块的 .git 是文件
    (tmp_path / "wt/src").mkdir()
    assert shared.find_root(tmp_path / "wt/src") == tmp_path / "wt"


def test_find_root_without_git_or_manifest_returns_start(tmp_path):
    start = tmp_path / "a/b"
    start.mkdir(parents=True)
    assert shared.find_root(start) == start


# ---------- 项目文件的边界：子仓库、子项目、第三方目录 ----------

EXPECTED_SKIPPED = [
    ("app-a", "另一个仓库"),
    ("packages/web", "另一个 rulemason 项目"),
    ("static/bower_components", "第三方目录"),
]


def _workspace(root):
    """一个工作区：自己的代码、一个独立仓库、一个子项目、第三方代码与 node_modules。"""
    write(root, "main.py", "x = 1\n")
    write(root, ".gitignore", "node_modules/\n")                         # 有 git 时 node_modules 由 .gitignore 排除
    write(root, "app-a/ruff.toml", "line-length = 100\n")
    git_init(root / "app-a")
    write(root, "packages/web/.rulemason.yaml", "version: 1\ntools: []\n")
    write(root, "packages/web/eslint.config.js", "export default [];\n")
    write(root, "static/bower_components/jquery/src/.eslintrc.json", "{}\n")
    write(root, "node_modules/x/index.js", "x\n")


@pytest.mark.parametrize("with_git", [False, True])
def test_scan_skips_other_projects_and_vendor_code(tmp_path, with_git):
    root = tmp_path / "ws"
    if with_git:
        git_init(root)
    _workspace(root)
    result = shared.scan(root)
    assert result.skipped == EXPECTED_SKIPPED                       # node_modules 静默跳过，不列出
    assert [f for f in result.files if f != ".gitignore"] == ["main.py"]
    assert shared.list_files(root) == result.files


def test_scan_does_not_walk_git_ignored_dirs(tmp_path):
    root = tmp_path / "proj"
    git_init(root)
    write(root, ".gitignore", "target/\n")
    write(root, "main.py", "x = 1\n")
    write(root, "target/deps/.git/HEAD", "ref\n")               # 被忽略目录里的嵌套仓库与第三方目录不算噪音
    write(root, "target/vendor/x.js", "x\n")
    assert shared.scan(root).skipped == []


def test_dirty_files_are_relative_to_subproject(tmp_path):
    repo = tmp_path / "repo"
    git_init(repo)
    write(repo, "outside.py", "x\n")
    write(repo, "packages/web/.rulemason.yaml", "version: 1\ntools: []\n")
    commit(repo)
    write(repo, "outside.py", "y\n")
    write(repo, "packages/web/app.ts", "x\n")
    assert shared.dirty_files(repo / "packages/web") == ["app.ts"]


@pytest.mark.parametrize(("marker", "skipped"), [(None, []), ("autoload.php", [("vendor", "第三方目录")]), ("modules.txt", [("vendor", "第三方目录")])])
def test_vendor_is_third_party_only_with_package_marker(tmp_path, marker, skipped):
    write(tmp_path, "vendor/avatar.svg", "<svg/>\n")                # 项目自己的资源
    if marker:
        write(tmp_path, f"vendor/{marker}", "x\n")
    assert shared.scan(tmp_path).skipped == skipped


# ---------- 方案草稿目录（init-ux-2） ----------

@pytest.mark.parametrize("in_git", [False, True])
def test_scan_skips_plan_drafts_silently(tmp_path, in_git):
    if in_git:
        git_init(tmp_path)
    write(tmp_path, "openspec/changes/add-x/prototype/package.json", '{"dependencies": {"react": "19.0.0"}}\n')
    write(tmp_path, "openspec/changes/archive/2026-01-01-a/proposal.md", "# P\n")
    write(tmp_path, "openspec/specs/a/spec.md", "# A\n")
    write(tmp_path, "app/main.py", "x = 1\n")
    scanned = shared.scan(tmp_path)
    assert sorted(scanned.files) == ["app/main.py", "openspec/specs/a/spec.md"]
    assert scanned.skipped == []
