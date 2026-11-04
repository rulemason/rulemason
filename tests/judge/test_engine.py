"""引擎测试：在临时搭的接入项目里跑，不联网、不依赖任何真实项目。各项目的 Jev 回归用例留在项目里。
运行（仓库根目录）：uv run pytest judge/tests
"""
import json
import subprocess
from pathlib import Path

import pytest

from rulemason import cli
from rulemason.judge import judge
from rulemason.judge.judge import verdict

PROJECT_RULE = """
- id: design-no-yaml
  target: design
  enforces: L1/context
  type: noul
  question: 该设计最终采纳的方案是：运行时直接读 YAML
  expect: false
  thresholds: { pass: 0.7, block: 0.3 }

- id: copy-voice
  target: copy
  enforces: L1/context
  type: score
  question: 这条界面文案的语气属于哪一档
  levels: [模板, 生硬, 自然]
  thresholds: { pass: 0.75, block: 0.25, min_confidence: 0.5 }
"""


# ---------- 1. 临时接入项目 ----------

def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _commit(root: Path, *args: str) -> None:
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", *args)


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def project(tmp_path, monkeypatch):
    """一个最小的接入项目：git 仓库、CLAUDE.md、openspec 配置与项目规则，当前目录切到它的子目录。"""
    root = tmp_path / "proj"
    _write(root, "CLAUDE.md", "# x\n\n## Code style\n\n九条\n")
    _write(root, "openspec/config.yaml", "context: 项目\nrules:\n  proposal: [a]\n  design: [b]\n")
    _write(root, "openspec/judgments.yaml", PROJECT_RULE)
    _write(root, "openspec/copy-lexicon.yaml", "labels:\n  - 待收录\n")
    _write(root, "api/README.md", "子目录\n")
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "--allow-empty", "-m", "init")
    monkeypatch.chdir(root / "api")
    monkeypatch.setattr(judge, "USER_ENV", tmp_path / "no-such-env")
    monkeypatch.setattr(judge, "OLD_USER_ENV", tmp_path / "no-such-old-env")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("JUDGE_PROVIDER", raising=False)
    judge.root.cache_clear()
    judge.config.cache_clear()
    yield root
    judge.root.cache_clear()
    judge.config.cache_clear()


def _commit_all(root: Path) -> None:
    _git(root, "add", "-A")
    _commit(root, "-m", "x")


# ---------- 2. 项目根 ----------

def test_root_is_git_toplevel_from_subdir(project):
    assert judge.root() == project.resolve()


def test_l0_enforces_uses_agents_when_only_agents_exists(project):
    (project / "CLAUDE.md").unlink()
    _write(project, "AGENTS.md", "# x\n\n## Code style\n\n共享规矩\n")

    assert judge.enforces_exists("L0/Code style")


def test_l0_enforces_falls_back_to_claude_when_agents_is_missing(project):
    assert judge.enforces_exists("L0/Code style")


def test_l0_enforces_does_not_fall_back_when_agents_exists(project):
    _write(project, "AGENTS.md", "# x\n\n## Project rules\n")

    assert not judge.enforces_exists("L0/Code style")
    assert judge.enforces_exists("L0/Project rules")


def test_outside_git_exits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    judge.root.cache_clear()
    with pytest.raises(SystemExit) as e:
        judge.root()
    assert "git" in str(e.value)


def test_git_repo_without_openspec_exits(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    monkeypatch.chdir(tmp_path)
    judge.root.cache_clear()
    with pytest.raises(SystemExit) as e:
        judge.root()
    assert "openspec" in str(e.value)


# ---------- 3. 规则：通用 + 项目 ----------

def test_base_rules_load_with_project_rules(project):
    ids = [r.id for r in judge.load_rules()]
    assert ids[:2] == ["proposal-states-non-goals", "design-no-speculative-extension"]
    assert "design-decisions-have-alternatives" not in ids          # 已改由 lint/design 检查
    assert "design-no-yaml" in ids


def test_project_rule_overrides_base_by_id(project):
    _write(project, "openspec/judgments.yaml", PROJECT_RULE + """
- id: proposal-states-non-goals
  target: proposal
  enforces: L1/proposal
  type: noul
  question: 收紧版
  expect: true
  thresholds: { pass: 0.7, block: 0.5 }
""")
    rules = judge.load_rules()
    assert [r.id for r in rules].count("proposal-states-non-goals") == 1
    assert _rules(project)["proposal-states-non-goals"].thresholds.block == 0.5


def test_project_without_rules_file_uses_base_only(project):
    (project / "openspec/judgments.yaml").unlink()
    assert len(judge.load_rules()) == 2


def _load_bad(project: Path, body: str) -> str:
    _write(project, "openspec/judgments.yaml", body)
    with pytest.raises(SystemExit) as e:
        judge.load_rules()
    return str(e.value)


def test_rule_without_enforces_is_rejected(project):
    msg = _load_bad(project, "- {id: x, target: design, type: noul, question: q, expect: true, thresholds: {pass: 0.7, block: 0.3}}")
    assert "'x'" in msg


def test_choice_type_is_rejected(project):
    msg = _load_bad(project, "- {id: y, target: design, enforces: L1/design, type: choice, question: q, thresholds: {pass: 0.7, block: 0.3}}")
    assert "'y'" in msg


def test_dangling_enforces_is_rejected(project):
    msg = _load_bad(project, "- {id: z, target: design, enforces: specs/no-such-spec, type: noul, question: q, expect: true, thresholds: {pass: 0.7, block: 0.3}}")
    assert "z" in msg and "specs/no-such-spec" in msg


# ---------- 4. 三段判定的算数 ----------

def _rules(project) -> dict:
    return {r.id: r for r in judge.load_rules()}


def test_noul_expect_false_flips(project):
    rule = _rules(project)["design-no-yaml"]
    assert verdict(rule, 0.02, None) == ("pass", "p=0.98")
    assert verdict(rule, 0.95, None)[0] == "block"


def test_thresholds_boundaries_inclusive_pass_exclusive_block(project):
    rule = _rules(project)["design-no-yaml"]                       # pass 0.7 / block 0.3
    assert verdict(rule, 0.30, None)[0] == "pass"                  # p = 0.70 等于 pass 阈值算 pass
    assert verdict(rule, 0.70, None)[0] == "review"                # p = 0.30 等于 block 阈值不算 block
    assert verdict(rule, 0.71, None)[0] == "block"


def test_score_normalizes_and_checks_confidence(project):
    rule = _rules(project)["copy-voice"]
    assert verdict(rule, 1.96, 0.93)[0] == "pass"
    assert verdict(rule, 1.0, 0.9)[0] == "review"
    assert verdict(rule, 0.02, 0.95)[0] == "block"
    v, why = verdict(rule, 0.91, 0.14)
    assert v == "review" and "置信度不足" in why


def test_speculative_extension_blocks_below_threshold(project):
    rule = _rules(project)["design-no-speculative-extension"]       # expect false：模型认为「有过度设计」的概率越高，得分越低
    assert verdict(rule, 0.92, None)[0] == "block"                  # 得分 0.08，与校准时的插件架构样本相当
    assert verdict(rule, 0.35, None)[0] == "review"                 # 得分 0.65，回放中正常 design 的最低分
    assert verdict(rule, 0.07, None)[0] == "pass"


# ---------- 5. lint ----------

@pytest.mark.parametrize("text", ["操作失败!", "操作失败！", "出错了 :(", "Oops! 出错了"])
def test_copy_lint_blocks_banned(project, text):
    assert judge.lint_copy(text)


def test_copy_lint_blocks_project_words(project):
    _write(project, "openspec/judge.yaml", "banned: [保证应验]\n")
    assert judge.lint_copy("此卦保证应验") == "含项目禁词「保证应验」"
    assert judge.lint_copy("服务暂时没有响应，可以稍后重试。") is None


DESIGN_OK = "## Risks / Trade-offs\n\n- [字体体积大] → 子集化\n\n## Migration Plan\n\n随 PR 发布。回滚即回退该 PR。\n"


def test_design_lint_ok():
    assert judge.lint_design(DESIGN_OK) == []
    assert judge.lint_design(DESIGN_OK.replace("[字体体积大]", "**字体体积大**")) == []


def test_design_lint_catches_bad_risk_line_and_missing_rollback():
    bad = DESIGN_OK.replace("- [字体体积大] → 子集化", "- 字体体积大，要子集化").replace("回滚即回退该 PR。", "")
    problems = judge.lint_design(bad)
    assert any("Risks" in p for p in problems) and any("回滚" in p for p in problems)


# ---------- 6. 短标签与词表 ----------

def test_label_len_ignores_placeholders():
    assert judge.label_len("前 {y}") == 1
    assert judge.label_len("已收录 {live} / 共 {total} 人") > judge.SHORT_LABEL


def test_lexicon_is_base_plus_project(project):
    labels = judge.lexicon()
    assert {"重试", "关闭"} <= labels                              # 通用
    assert "待收录" in labels                                       # 项目


# ---------- 7. 目标文件 ----------

def test_missing_design_is_skipped_not_error(project, capsys):
    _write(project, "openspec/changes/archive/2026-01-01-x/proposal.md", "# P\n")
    files = judge.change_files("archive/2026-01-01-x")
    assert [f for f, _, _ in files] == ["proposal.md"]
    assert "跳过 design.md" in capsys.readouterr().out


def test_unknown_change_exits(project):
    with pytest.raises(SystemExit):
        judge.change_files("no-such-change")


def test_change_found_in_archive_by_bare_name(project):
    _write(project, "openspec/changes/archive/2026-11-01-adopt-x/proposal.md", "# P\n")
    assert judge.change_dir("adopt-x").name == "2026-11-01-adopt-x"
    assert judge.change_dir("archive/2026-11-01-adopt-x").name == "2026-11-01-adopt-x"


def test_active_change_wins_over_archive(project):
    _write(project, "openspec/changes/adopt-x/proposal.md", "# P\n")
    _write(project, "openspec/changes/archive/2026-11-01-adopt-x/proposal.md", "# P\n")
    assert judge.change_dir("adopt-x") == judge.root() / "openspec/changes/adopt-x"


def test_ambiguous_archive_match_exits_and_lists(project):
    _write(project, "openspec/changes/archive/2026-10-01-fix/proposal.md", "# P\n")
    _write(project, "openspec/changes/archive/2026-11-01-fix/proposal.md", "# P\n")
    _write(project, "openspec/changes/archive/2026-11-01-prefix-fixes/proposal.md", "# P\n")
    with pytest.raises(SystemExit) as exc:
        judge.change_dir("fix")
    assert "archive/2026-10-01-fix" in str(exc.value) and "archive/2026-11-01-fix" in str(exc.value)
    assert "prefix-fixes" not in str(exc.value)


def test_archive_lookup_needs_date_prefix_and_full_name(project):
    _write(project, "openspec/changes/archive/2026-11-01-cli-migration-fixes/proposal.md", "# P\n")
    with pytest.raises(SystemExit):
        judge.change_dir("migration-fixes")                     # 只是另一个 change 名的后缀
    with pytest.raises(SystemExit):
        judge.change_dir("*")                                   # 通配符按字面处理
    assert judge.change_dir("cli-migration-fixes").name == "2026-11-01-cli-migration-fixes"


# ---------- 8. 文案：两种格式与配置 ----------

def test_copy_without_config_exits(project):
    with pytest.raises(SystemExit) as e:
        judge.copy_config()
    assert "copy.file" in str(e.value)


def test_js_i18n_needs_lang(project):
    _write(project, "openspec/judge.yaml", "copy: {file: index.html, format: js-i18n}\n")
    with pytest.raises(SystemExit) as e:
        judge.copy_config()
    assert "copy.lang" in str(e.value)


def test_json_copy_changed_against_main(project):
    _write(project, "openspec/judge.yaml", "copy: {file: web/zh.json, format: json}\n")
    _write(project, "web/zh.json", json.dumps({"a": {"b": "旧"}, "c": "不变"}, ensure_ascii=False))
    _commit_all(project)
    _write(project, "web/zh.json", json.dumps({"a": {"b": "新"}, "c": "不变", "d": "加"}, ensure_ascii=False))
    assert judge.changed_copy(*judge.copy_config()) == {"a.b": "新", "d": "加"}


I18N = """<script>
const I18N = {
  "zh-Hans": { title: "易经", items: ["初", "二"], go: "开始" },
  "zh-Hant": { title: "易經", go: "開始" },
};
</script>"""


def test_js_i18n_copy_reads_one_lang_and_skips_arrays(project):
    _write(project, "openspec/judge.yaml", "copy: {file: index.html, format: js-i18n, lang: zh-Hans}\n")
    _write(project, "index.html", I18N)
    assert judge.changed_copy(*judge.copy_config()) == {"title": "易经", "go": "开始"}       # main 上没有这个文件，全部算新增


def test_long_copy_without_copy_rule_goes_review(project, capsys):
    _write(project, "openspec/judgments.yaml", PROJECT_RULE.split("- id: copy-voice")[0])
    _write(project, "openspec/judge.yaml", "copy: {file: web/zh.json, format: json}\n")
    _write(project, "web/zh.json", json.dumps({"a": "服务暂时没有响应，可以稍后重试。"}, ensure_ascii=False))
    results = judge.run_copy(judge.load_rules(), judge.Judge("manual"))
    assert results == ["review"]
    assert "未启用文案打分规则" in capsys.readouterr().out


# ---------- 9. 裁判与 key ----------

def test_provider_defaults_to_manual_without_key(project):
    assert judge.pick_provider() == "manual"


def test_jev_without_key_exits(project, monkeypatch):
    monkeypatch.setenv("JUDGE_PROVIDER", "jev")
    with pytest.raises(SystemExit) as e:
        judge.pick_provider()
    assert "TYPESAFE_API_KEY" in str(e.value)


def _user_env(tmp_path: Path, monkeypatch, text: str) -> None:
    """把 ~/.config/rulemason/env 换成临时文件。"""
    env = tmp_path / "env"
    env.write_text(text, encoding="utf-8")
    monkeypatch.setattr(judge, "USER_ENV", env)


def test_key_read_from_user_env_file(project, tmp_path, monkeypatch):
    _user_env(tmp_path, monkeypatch, "# key\nTYPESAFE_API_KEY=\"abc\"\n")
    assert judge.api_key() == "abc"
    assert judge.pick_provider() == "jev"


def test_env_var_wins_over_user_env_file(project, tmp_path, monkeypatch):
    _user_env(tmp_path, monkeypatch, "TYPESAFE_API_KEY=file\n")
    monkeypatch.setenv("TYPESAFE_API_KEY", "var")
    assert judge.api_key() == "var"


def test_project_dotenv_is_ignored(project):
    _write(project, "api/.env", "TYPESAFE_API_KEY=should-not-be-read\n")
    assert judge.api_key() == ""


def test_dry_run_without_key_prints_payload(project, capsys):
    rule = _rules(project)["design-no-yaml"]
    assert judge.Judge(judge.pick_provider(), dry_run=True).ask("正文", [rule]) == {}
    payload = json.loads(capsys.readouterr().out)
    assert payload["model"] == judge.JEV_MODEL and "design-no-yaml" in payload["questions"]


def test_manual_mode_prints_checklist(project, capsys):
    rule = _rules(project)["design-no-yaml"]
    assert judge.Judge("manual").ask("正文", [rule]) == {}
    assert "[ ] design-no-yaml" in capsys.readouterr().out


def test_rejected_key_gives_one_line_error(project, monkeypatch, capsys):
    import httpx2
    from typesafe_sdk import TypeSafeAuthenticationError

    def rejected(argv=None):
        raise TypeSafeAuthenticationError(401, {}, httpx2.Headers(), "Cannot authenticate")

    monkeypatch.setattr(judge, "main", rejected)
    with pytest.raises(SystemExit) as exc:
        judge.cli()
    message = str(exc.value.code)
    assert "key" in message and str(judge.USER_ENV) in message
    assert "Traceback" not in message + capsys.readouterr().err


# ---------- key 位置：新位置优先，旧位置只读兜底 ----------


def _key_files(tmp_path: Path, monkeypatch, new: str | None, old: str | None) -> tuple[Path, Path]:
    new_env, old_env = tmp_path / "home/.config/rulemason/env", tmp_path / "home/.config/jev-judge/env"
    for path, text in ((new_env, new), (old_env, old)):
        if text is not None:
            _write(path.parent, path.name, text)
    monkeypatch.setattr(judge, "USER_ENV", new_env)
    monkeypatch.setattr(judge, "OLD_USER_ENV", old_env)
    return new_env, old_env


@pytest.mark.parametrize(
    ("new", "old", "expected"),
    [
        ("TYPESAFE_API_KEY=new-key\n", None, "new-key"),
        (None, "TYPESAFE_API_KEY=old-key\n", "old-key"),
        ("TYPESAFE_API_KEY=new-key\n", "TYPESAFE_API_KEY=old-key\n", "new-key"),
        (None, None, ""),
    ],
)
def test_key_location_order(project, tmp_path, monkeypatch, new, old, expected):
    new_env, _ = _key_files(tmp_path, monkeypatch, new, old)
    assert judge.setting("TYPESAFE_API_KEY") == expected
    assert judge.pick_provider() == ("jev" if expected else "manual")
    assert new_env.exists() == (new is not None)      # 只读：不因旧位置有 key 而创建新文件


def test_missing_key_message_names_new_location(project, tmp_path, monkeypatch):
    new_env, old_env = _key_files(tmp_path, monkeypatch, None, None)
    monkeypatch.setenv("JUDGE_PROVIDER", "jev")
    with pytest.raises(SystemExit) as e:
        judge.pick_provider()
    assert str(new_env) in str(e.value) and str(old_env) not in str(e.value)


# ---------- rulemason judge：参数原样转交引擎 ----------


def test_judge_subcommand_help_names_new_command(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["judge", "--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: rulemason judge")
    assert all(flag in out for flag in ("--change", "--copy", "--lint-only", "--dry-run"))


def test_judge_subcommand_matches_engine(project, capsys):
    _write(project, "openspec/changes/demo/proposal.md", "## Why\n\n要做。\n")
    _write(project, "openspec/changes/demo/design.md", "## Decisions\n\n### 1. 用 A\n\n否决 B。\n")
    expected = judge.main(["--change", "demo", "--lint-only"])
    direct = capsys.readouterr().out
    with pytest.raises(SystemExit) as e:
        cli.main(["judge", "--change", "demo", "--lint-only"])
    assert e.value.code == expected
    assert capsys.readouterr().out == direct


def test_other_commands_reject_unknown_arguments(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["check", "--change", "demo"])
    assert e.value.code == 2
    assert "无法识别的参数" in capsys.readouterr().err


# ---------- 项目根：往上找清单；没有清单时用 git 仓库根（与 init 不同） ----------


def test_root_without_manifest_is_repo_root(project):
    """未接入 rulemason 的仓库，在子目录 api/ 运行：没有清单就用 git 仓库根，才能找到 openspec/。"""
    assert Path.cwd() == (project / "api").resolve() and not (project / ".rulemason.yaml").exists()   # 夹具已切到 api/、没有清单
    assert judge.root() == project.resolve()


def test_root_is_nearest_subproject(project, monkeypatch):
    sub = project / "packages/web"
    _write(sub, ".rulemason.yaml", "version: 1\ntools: []\n")
    _write(sub, "openspec/changes/x/proposal.md", "## Why\n\n要做。\n")
    (sub / "src").mkdir()
    monkeypatch.chdir(sub / "src")
    judge.root.cache_clear()
    assert judge.root() == sub.resolve()
    assert judge.change_dir("x") == sub.resolve() / "openspec/changes/x"


# ---------- 判断层模板随引擎提供 ----------


@pytest.mark.parametrize("name", judge.TEMPLATE_NAMES)
def test_template_prints_file(tmp_path, monkeypatch, capsys, name):
    monkeypatch.chdir(tmp_path)                                  # 不要求在项目里
    assert judge.main(["--template", name]) == 0
    assert capsys.readouterr().out == (judge.TEMPLATES / f"{name}.yaml").read_text(encoding="utf-8")


def test_unknown_template_lists_names(capsys):
    assert judge.main(["--template", "rules"]) == 1
    out = capsys.readouterr().out
    assert all(name in out for name in judge.TEMPLATE_NAMES)


# ---------- 裁判那一行 ----------


def test_judge_line_manual_without_key_suggests_key_command(project):
    line = judge.judge_line("manual", dry_run=False)
    assert line == "裁判：人工（没有 key；运行 rulemason key 配置后自动用 Jev 判断）"
    assert judge.JEV_MODEL not in line


def test_judge_line_manual_by_choice_and_jev(project, monkeypatch):
    monkeypatch.setenv("JUDGE_PROVIDER", "manual")
    assert judge.judge_line("manual", dry_run=False) == "裁判：人工（已指定人工）"
    assert judge.judge_line("jev", dry_run=True) == f"裁判：jev（dry-run，不发送），模型 {judge.JEV_MODEL}"


# ---------- 项目配置写错时的可读提示（judge-config-errors） ----------

@pytest.mark.parametrize(("rel", "text", "expected"), [
    ("openspec/judgments.yaml", "- id: a\n  target: design\n bad: x\n", "✗ openspec/judgments.yaml 不是合法的 YAML（第 3 行"),
    ("openspec/judgments.yaml", "- id: a\n- target: design\n", "✗ openspec/judgments.yaml 第 2 条不是带 id 的映射"),
    ("openspec/judgments.yaml", "- just-a-string\n", "✗ openspec/judgments.yaml 第 1 条不是带 id 的映射"),
    ("openspec/config.yaml", "context: a: b\n", "✗ openspec/config.yaml 不是合法的 YAML（第 1 行"),
])
def test_bad_config_gives_one_line_without_traceback(project, rel, text, expected):
    _write(project, rel, text)
    with pytest.raises(SystemExit) as exc:
        judge.cli(["--change", "x", "--lint-only"])
    assert str(exc.value.code).startswith(expected)


@pytest.mark.parametrize("text", ["- copy\n", "copy: {file: [\n"])
def test_bad_judge_yaml_with_copy(project, text):
    _write(project, "openspec/judge.yaml", text)
    with pytest.raises(SystemExit) as exc:
        judge.cli(["--copy", "--lint-only"])
    assert str(exc.value.code).startswith("✗ openspec/judge.yaml ")


def test_non_string_id_is_rejected(project):
    _write(project, "openspec/judgments.yaml", "- id: [a, b]\n")
    with pytest.raises(SystemExit) as exc:
        judge.cli(["--change", "x", "--lint-only"])
    assert str(exc.value.code) == "✗ openspec/judgments.yaml 第 1 条不是带 id 的映射"


def test_unreadable_file_gives_one_line(project):
    (project / "openspec/judgments.yaml").unlink()
    (project / "openspec/judgments.yaml").mkdir()                      # 路径是目录：读文件时抛 OSError
    with pytest.raises(SystemExit) as exc:
        judge.cli(["--change", "x", "--lint-only"])
    assert str(exc.value.code).startswith("✗ rulemason judge 失败：")


# ---------- 10. lint：决策须写否决理由 ----------

DECISIONS = """## Decisions

### 1. 用 A
理由。**否决：** B，太慢。

### 2. 用 C
理由。备选 D 需要额外服务。

### 3. 用 E
Alternative considered: F, rejected because it is heavier.
"""


def test_decisions_with_rejections_pass():
    assert judge.lint_design(DECISIONS + DESIGN_OK) == []


def test_decision_without_rejection_is_reported():
    bad = DECISIONS.replace("理由。备选 D 需要额外服务。", "只写了理由。") + DESIGN_OK
    assert judge.lint_design(bad) == ["决策缺否决理由：2. 用 C"]


def test_decisions_without_subsections_checked_as_one():
    assert judge.lint_design("## Decisions\n\n用 A，没有比较。\n" + DESIGN_OK) == ["决策缺否决理由：用 A，没有比较。"]
    assert judge.lint_design("## Decisions\n\n用 A；否决 B。\n" + DESIGN_OK) == []


def test_design_without_decisions_skips_this_check():
    assert "## Decisions" not in DESIGN_OK
    assert judge.lint_design(DESIGN_OK) == []


def test_keyword_in_title_does_not_count():
    md = "## Decisions\n\n### 1. 备选方案的缓存策略\n用 Redis。\n" + DESIGN_OK
    assert judge.lint_design(md) == ["决策缺否决理由：1. 备选方案的缓存策略"]


def test_empty_decisions_and_lead_text():
    assert judge.lint_design("## Decisions\n\n" + DESIGN_OK) == []
    md = "## Decisions\n\n下面各条都否决了别的做法。\n\n### 1. 用 A\n只写了理由。\n" + DESIGN_OK
    assert judge.lint_design(md) == ["决策缺否决理由：1. 用 A"]          # 引导文字不算进任何一条


def test_run_change_blocks_without_calling_model(project, capsys):
    _write(project, "openspec/changes/x/design.md", "## Decisions\n\n### 1. 用 A\n只写了理由。\n" + DESIGN_OK)

    class NoModel:
        def evaluate(self, *_args, **_kwargs):
            raise AssertionError("lint 命中后不应送模型")
    results = judge.run_change("x", judge.load_rules(), NoModel())
    assert results == ["block"]
    assert "决策缺否决理由：1. 用 A" in capsys.readouterr().out
