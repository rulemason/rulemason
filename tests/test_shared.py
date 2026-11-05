"""shared.py 的测试：共享数据定位、manifest 读写、生成副本清单与列文件。"""
from __future__ import annotations

import pytest
from conftest import commit, git_init, project_folder, write

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

    text = shared.manifest_text(current, ["codex", "claude", "codex"], {"b": "2", "a": "1"}, "2026-11-05")
    shared.write_text(tmp_path / ".rulemason.yaml", text)
    data = shared.read_manifest(tmp_path)

    assert data == {"version": 1, "tools": ["claude", "codex"], "owner-note": "keep", "rulemason": __version__, "joined": "2026-11-05", "files": {"a": "1", "b": "2"}}
    assert list(data)[:3] == ["version", "rulemason", "joined"]         # 接入日期紧跟版本号
    assert shared.manifest_text(data, ["claude", "codex"], {"a": "1", "b": "2"}, "2026-11-05") == text


def test_manifest_missing_returns_none(tmp_path):
    assert shared.read_manifest(tmp_path) is None


@pytest.mark.parametrize("text", ["tools: [codex]\n", "version: 2\ntools: []\n", "version: 1\ntools: [vim]\n", "- a\n",
                                  "version: 1\ntools: []\njoined: 上周\n", "version: 1\ntools: []\njoined: '2026-13-40'\n",
                                  "version: 1\ntools: []\njoined: '20261105'\n", "version: 1\ntools: []\njoined: 2026-13-40\n"])
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


# ---------- 项目根：往上找最近的清单，以 git 仓库根为边界；找不到返回 None ----------


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
    assert shared.find_root(tmp_path / "ws/app-a/src") is None               # 到了 app-a 仓库根还没有清单：不往上找工作区的


def test_find_root_ignores_rulekit_manifest(tmp_path):
    write(tmp_path / "old", ".rulekit.yaml", 'version: 1\ntools: [claude]\nrulekit: 0.5.2\nfiles: {}\n')
    (tmp_path / "old/src").mkdir()
    assert shared.find_root(tmp_path / "old/src") is None                      # 旧格式清单不算


def test_find_root_stops_at_git_file(tmp_path):
    write(tmp_path / "wt", ".git", "gitdir: /elsewhere\n")                  # worktree 与子模块的 .git 是文件
    (tmp_path / "wt/src").mkdir()
    assert shared.find_root(tmp_path / "wt/src") is None
    assert shared.repo_root(tmp_path / "wt/src") == tmp_path / "wt"


def test_find_root_without_git_or_manifest_returns_none(tmp_path):
    start = tmp_path / "a/b"
    start.mkdir(parents=True)
    assert shared.find_root(start) is None
    assert shared.repo_root(start) is None                                    # 不在 git 里


def test_repo_root_from_subdirectory(tmp_path):
    git_init(tmp_path / "repo")
    (tmp_path / "repo/web/src").mkdir(parents=True)
    assert shared.repo_root(tmp_path / "repo/web/src") == tmp_path / "repo"


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


def test_ignored_files_handles_chinese_names_under_gbk(tmp_path, gbk_default):
    """Windows 中文版默认 GBK：git check-ignore 的输入输出要按 UTF-8，中文文件名才判得对。"""
    git_init(tmp_path)
    write(tmp_path, ".gitignore", "草稿/\n")
    assert shared.ignored_files(tmp_path, ["草稿/方案.md", "正文.md"]) == ["草稿/方案.md"]


@pytest.mark.parametrize(("platform", "env", "legacy"), [
    ("win32", {}, True),
    ("win32", {"WT_SESSION": "1"}, False),
    ("win32", {"TERM_PROGRAM": "vscode"}, False),
    ("darwin", {}, False),
])
def test_legacy_console_and_fail_prefix(monkeypatch, platform, env, legacy):
    """旧控制台字库里没有 ✗：只有 Windows 上既无 WT_SESSION 又无 TERM_PROGRAM 时改用 ×。"""
    monkeypatch.setattr(shared.sys, "platform", platform)
    monkeypatch.delenv("WT_SESSION", raising=False)
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert shared.legacy_console() is legacy
    assert shared.fail("出错了") == ("× 出错了" if legacy else "✗ 出错了")


def test_skill_hint_only_for_opencode():
    assert shared.skill_hint_lines(["opencode", "claude"]) == [shared.OPENCODE_SKILL_HINT]
    assert shared.skill_hint_lines(["claude", "cursor"]) == []


# ---------- 放项目的文件夹（multi-project-folder） ----------

def test_folder_hint_names_sub_repos_and_sub_projects(tmp_path):
    project_folder(tmp_path)                                         # 文件夹里的说明文件不影响判断
    hint = shared.folder_hint(shared.scan(tmp_path))
    assert hint is not None
    assert hint.startswith("这里有独立项目 b、c；")
    assert "rulemason init" in hint


@pytest.mark.parametrize(("own_file", "sub_file"), [
    ("main.py", "libs/x/.git/HEAD"),           # 有 Python 代码的项目带子仓库
    ("package.json", "libs/x/.git/HEAD"),      # 有 JS/TS 的项目带子仓库
    ("README.md", "third_party/lib/a.c"),      # 没有语言，但子目录只是第三方代码
])
def test_folder_hint_absent_for_projects_and_vendor_only(tmp_path, own_file, sub_file):
    write(tmp_path, own_file, "x\n")
    write(tmp_path, sub_file, "x\n")
    assert shared.folder_hint(shared.scan(tmp_path)) is None


def test_folder_hint_truncates_long_project_lists(tmp_path):
    for i in range(12):
        write(tmp_path, f"repo-{i:02d}/.git/HEAD", "ref\n")
    hint = shared.folder_hint(shared.scan(tmp_path))
    assert hint.startswith("这里有独立项目 repo-00、") and "repo-09 等共 12 个；" in hint and "repo-10" not in hint


# ---------- 接入日期（joined-date-spec-lint-audits） ----------

def test_joined_accepts_unquoted_yaml_date(tmp_path):
    write(tmp_path, ".rulemason.yaml", "version: 1\ntools: []\njoined: 2026-11-02\n")       # 不加引号时 YAML 读成 date
    assert shared.read_manifest(tmp_path)["joined"] == "2026-11-02"


def test_joined_date_prefers_manifest_then_git(tmp_path, monkeypatch):
    git_init(tmp_path)
    write(tmp_path, ".rulemason.yaml", "version: 1\ntools: []\n")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-11-02T10:00:00")
    commit(tmp_path, "join")
    write(tmp_path, ".rulemason.yaml", "version: 1\ntools: [claude]\n")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-11-04T10:00:00")
    commit(tmp_path, "later")
    assert shared.joined_date(tmp_path, {"joined": "2026-10-30"}) == "2026-10-30"
    assert shared.joined_date(tmp_path, {}) == "2026-11-02"                   # 第一次加入那条提交，不是后来的修改


def test_joined_date_without_git_is_none(tmp_path):
    write(tmp_path, ".rulemason.yaml", "version: 1\ntools: []\n")
    assert shared.joined_date(tmp_path, {}) is None
