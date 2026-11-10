"""product-artifact-caution 分发与结构预设；must_contain/pattern severity。"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from rulemason import cli, init, remove, shared, update
from rulemason.result_check import STATUS_HINT, run_check
from rulemason.shared import packaged_result_check_preset, seed_result_check_presets


def _run_cli(*argv: str):
    try:
        cli.main(list(argv))
    except SystemExit as exc:
        return exc.code
    return 0


# ---------- severity 兼容 ----------

def test_must_contain_default_still_fails() -> None:
    report = run_check(
        {"text": "只有摘要"},
        {"schema": 1, "checks": [{"id": "a", "type": "must_contain", "texts": ["非目标"]}]},
    )
    assert report.exit_code == 1
    assert report.items[0].status == "失败"


def test_pattern_hint_alone_exit_zero() -> None:
    report = run_check(
        {"text": "# 摘要\n无目标段落\n"},
        {"schema": 1, "checks": [{
            "id": "h", "type": "pattern",
            "pattern": r"(?im)^#{1,6}\s*非目标\b",
            "severity": "hint",
        }]},
    )
    assert report.exit_code == 0
    assert report.overall_pass is True
    assert report.items[0].status == STATUS_HINT


def test_must_contain_hint_alone_exit_zero() -> None:
    report = run_check(
        {"text": "只有摘要"},
        {"schema": 1, "checks": [{
            "id": "a", "type": "must_contain", "texts": ["非目标"], "severity": "hint",
        }]},
    )
    assert report.exit_code == 0
    assert report.items[0].status == STATUS_HINT


def test_pattern_hint_does_not_swallow_fail() -> None:
    report = run_check(
        {"text": "I hope this helps"},
        {"schema": 1, "checks": [
            {"id": "h", "type": "pattern", "pattern": r"非目标", "severity": "hint"},
            {"id": "t", "type": "must_contain", "texts": ["MISSING"]},
        ]},
    )
    assert report.exit_code == 1
    assert any(i.status == STATUS_HINT for i in report.items)
    assert any(i.status == "失败" for i in report.items)


def test_bad_text_severity_input_error() -> None:
    report = run_check(
        {"text": "x"},
        {"schema": 1, "checks": [{
            "id": "a", "type": "must_contain", "texts": ["x"], "severity": "loud",
        }]},
    )
    assert report.exit_code == 2


def test_unknown_and_input_error_not_swallowed_by_hint() -> None:
    missing_text = run_check(
        {},
        {"schema": 1, "checks": [{
            "id": "h", "type": "pattern", "pattern": r"非目标", "severity": "hint",
        }]},
    )
    assert missing_text.exit_code == 1
    assert missing_text.items[0].status == "无法判断"

    bad_pat = run_check(
        {"text": "x"},
        {"schema": 1, "checks": [{
            "id": "h", "type": "pattern", "pattern": "(", "severity": "hint",
        }]},
    )
    assert bad_pat.exit_code == 2


def test_legacy_prose_cjk_field_exit_codes_unchanged() -> None:
    prose = run_check(
        {"text": "I hope this helps"},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene", "rules": ["chatbot_closer"], "severity": "strict",
        }]},
    )
    assert prose.exit_code == 1

    cjk = run_check(
        {"text": "使用Git"},
        {"schema": 1, "checks": [{"id": "c", "type": "cjk_typography", "rules": ["cjk_latin_space"]}]},
    )
    assert cjk.exit_code == 1

    field = run_check(
        {"structured": {"a": 1}},
        {"schema": 1, "checks": [{
            "id": "f", "type": "field", "path": "a", "value_type": "string",
        }]},
    )
    assert field.exit_code == 1


# ---------- 预设语义 ----------

def test_preset_hint_still_prose_not_product() -> None:
    preset = json.loads(packaged_result_check_preset("hint"))
    assert preset["checks"][0]["type"] == "prose_hygiene"
    product = json.loads(packaged_result_check_preset("product-artifact.hint"))
    assert all(c["type"] == "pattern" for c in product["checks"])
    assert all(c["severity"] == "hint" for c in product["checks"])


def test_product_artifact_hint_and_strict(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "r.json"
    # 自写示例：有成功标准，缺非目标
    rec.write_text(json.dumps({
        "text": "# 功能\n\n## 成功标准\n日志可核对。\n",
    }, ensure_ascii=False), encoding="utf-8")
    code = _run_cli(
        "result-check", "--json", "--record", str(rec), "--preset", "product-artifact.hint",
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(i["status"] == STATUS_HINT for i in payload["items"])

    code = _run_cli(
        "result-check", "--json", "--record", str(rec), "--preset", "product-artifact.strict",
    )
    assert code == 1


def test_synonym_headings_pass() -> None:
    text = "# Feat\n\n## Non-goals\nv1 skip.\n\n## Acceptance\nGiven When Then.\n"
    report = run_check({"text": text}, json.loads(packaged_result_check_preset("product-artifact.hint")))
    assert report.exit_code == 0
    assert all(i.status == "通过" for i in report.items)


def test_code_fence_fake_heading_documented_false_positive() -> None:
    # 围栏内假标题仍可能匹配（已知边界：本类型不剥代码）；锁定为「会误报通过」以免静默变严
    text = "摘要\n\n```\n## 非目标\n## 验收\n```\n"
    report = run_check({"text": text}, json.loads(packaged_result_check_preset("product-artifact.strict")))
    assert report.exit_code == 0
    assert all(i.status == "通过" for i in report.items)


def test_keyword_in_prose_without_heading_is_miss() -> None:
    text = "本文讨论非目标与验收标准，但没有独立小节。\n"
    report = run_check({"text": text}, json.loads(packaged_result_check_preset("product-artifact.strict")))
    assert report.exit_code == 1


# ---------- 种子 / 分发 / remove ----------

def test_seed_presets_idempotent(tmp_path: Path) -> None:
    first = seed_result_check_presets(tmp_path)
    assert len(first) == 6
    hint = tmp_path / ".rulemason/result-check/product-artifact.hint.json"
    original = hint.read_text(encoding="utf-8")
    hint.write_text(original.replace("非目标", "范围外"), encoding="utf-8")
    custom = hint.read_text(encoding="utf-8")
    assert seed_result_check_presets(tmp_path) == []
    assert hint.read_text(encoding="utf-8") == custom


def test_init_distributes_rule_and_seeds(tmp_path: Path) -> None:
    from conftest import commit, git_init, write

    root = tmp_path / "proj"
    git_init(root)
    write(root, "go.mod", "module x\n")
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    commit(root)
    assert init.run(root, "claude", True) == 0
    rule = root / ".rulemason/rules/product-artifact-caution.md"
    assert rule.is_file()
    body = rule.read_text(encoding="utf-8")
    assert "可检验" in body
    assert "验证走查" in body
    assert "aa3bf0e986379d46c6e23c50bfa30ad812f5aa55" in body
    assert "未" in body
    assert (root / ".rulemason/result-check/product-artifact.hint.json").is_file()
    assert (root / ".rulemason/result-check/verification-walkthrough.hint.json").is_file()
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "product-artifact-caution.md" in agents
    files = shared.read_manifest(root)["files"]
    assert ".rulemason/rules/product-artifact-caution.md" in files
    assert ".rulemason/result-check/product-artifact.hint.json" not in files
    assert ".rulemason/result-check/verification-walkthrough.hint.json" not in files
    path = root / ".rulemason/result-check/product-artifact.hint.json"
    custom = path.read_text(encoding="utf-8").replace("Non-?goals?", "OutOfScopeX")
    path.write_text(custom, encoding="utf-8")
    walk = root / ".rulemason/result-check/verification-walkthrough.hint.json"
    walk_custom = walk.read_text(encoding="utf-8").replace("验证走查", "走查占位")
    walk.write_text(walk_custom, encoding="utf-8")
    assert update.run(root, yes=True) == 0
    assert path.read_text(encoding="utf-8") == custom
    assert walk.read_text(encoding="utf-8") == walk_custom


def test_remove_deletes_product_and_walkthrough_seeds(tmp_path: Path) -> None:
    from conftest import commit, git_init, write

    root = tmp_path / "proj"
    git_init(root)
    write(root, "README.md", "demo\n")
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    commit(root)
    assert init.run(root, "claude", True) == 0
    seeds = [
        root / ".rulemason/result-check/product-artifact.hint.json",
        root / ".rulemason/result-check/product-artifact.strict.json",
        root / ".rulemason/result-check/verification-walkthrough.hint.json",
        root / ".rulemason/result-check/verification-walkthrough.strict.json",
    ]
    assert all(p.is_file() for p in seeds)
    assert remove.run(root, yes=True) == 0
    assert all(not p.exists() for p in seeds)


def test_wheel_and_sdist_include_resources(tmp_path: Path) -> None:
    import subprocess
    import tarfile

    repo = Path(__file__).resolve().parents[1]
    dist = tmp_path / "dist"
    dist.mkdir()
    proc = subprocess.run(
        ["uv", "build", "--out-dir", str(dist)],
        cwd=repo, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    wheels = list(dist.glob("*.whl"))
    sdists = list(dist.glob("*.tar.gz"))
    assert wheels and sdists
    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()
        assert any(n.endswith("rules/product-artifact-caution.md") for n in names)
        assert any(n.endswith("templates/result-check/product-artifact.hint.json") for n in names)
        assert any(n.endswith("templates/result-check/product-artifact.strict.json") for n in names)
        assert any(n.endswith("templates/result-check/verification-walkthrough.hint.json") for n in names)
        assert any(n.endswith("templates/result-check/verification-walkthrough.strict.json") for n in names)
    with tarfile.open(sdists[0], "r:gz") as tf:
        snames = tf.getnames()
        assert any(n.endswith("rules/product-artifact-caution.md") for n in snames)
        assert any("product-artifact.hint.json" in n for n in snames)
        assert any("verification-walkthrough.hint.json" in n for n in snames)


def test_clean_install_preset_runs(tmp_path: Path, monkeypatch) -> None:
    """用包内模板直接跑（不依赖已接入项目），模拟干净安装后的 CLI 路径。"""
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "r.json"
    rec.write_text(json.dumps({
        "text": "## 非目标\nx\n\n## 验收\ny\n",
    }, ensure_ascii=False), encoding="utf-8")
    code = _run_cli(
        "result-check", "--json", "--record", str(rec), "--preset", "product-artifact.hint",
    )
    assert code == 0
