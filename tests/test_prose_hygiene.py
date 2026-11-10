"""prose_hygiene：hint/strict、预设、与旧退出码兼容。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import run_cli

from rulemason import prose_hygiene as ph
from rulemason.result_check import STATUS_HINT, CheckReport, run_check, run_files
from rulemason.shared import packaged_result_check_preset, seed_result_check_presets


def test_recommended_excludes_em_dash() -> None:
    assert "em_dash" not in ph.RECOMMENDED_RULES
    assert set(ph.RECOMMENDED_RULES) <= ph.KNOWN_RULES


def test_hint_hit_exit_zero() -> None:
    report = run_check(
        {"text": "I hope this helps with pricing."},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene",
            "rules": list(ph.RECOMMENDED_RULES),
        }]},
    )
    assert report.exit_code == 0
    assert report.overall_pass is True
    assert report.items[0].status == STATUS_HINT


def test_strict_hit_exit_one() -> None:
    report = run_check(
        {"text": "I hope this helps with pricing."},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene",
            "rules": ["chatbot_closer"],
            "severity": "strict",
        }]},
    )
    assert report.exit_code == 1
    assert report.items[0].status == "失败"


def test_hint_does_not_swallow_other_fail() -> None:
    report = run_check(
        {"text": "I hope this helps"},
        {"schema": 1, "checks": [
            {"id": "p", "type": "prose_hygiene", "rules": ["chatbot_closer"]},
            {"id": "t", "type": "must_contain", "texts": ["MISSING"]},
        ]},
    )
    assert report.exit_code == 1
    assert any(i.status == STATUS_HINT for i in report.items)
    assert any(i.status == "失败" for i in report.items)


def test_em_dash_off_by_default_in_preset() -> None:
    preset = json.loads(packaged_result_check_preset("hint"))
    rules = preset["checks"][0]["rules"]
    assert "em_dash" not in rules
    text = "The policy — announced yesterday — applies."
    report = run_check({"text": text}, preset)
    assert report.exit_code == 0
    assert all(i.status == "通过" for i in report.items)


def test_legacy_without_prose_unchanged() -> None:
    report = run_check(
        {"text": "Hello — world"},
        {"schema": 1, "checks": [{"id": "t", "type": "must_contain", "texts": ["Hello"]}]},
    )
    assert report.exit_code == 0


def test_cjk_fail_still_nonzero() -> None:
    report = run_check(
        {"text": "使用Git"},
        {"schema": 1, "checks": [
            {"id": "c", "type": "cjk_typography", "rules": ["cjk_latin_space"]},
            {"id": "p", "type": "prose_hygiene", "rules": ["chatbot_closer"]},
        ]},
    )
    assert report.exit_code == 1


def test_bad_severity_input_error() -> None:
    report = run_check(
        {"text": "ok"},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene",
            "rules": ["chatbot_closer"], "severity": "loud",
        }]},
    )
    assert report.exit_code == 2


def test_disable_and_allowlist() -> None:
    text = "<!-- rulemason-disable chatbot_closer -->I hope this helps<!-- rulemason-enable -->"
    assert ph.find_hits(text, ["chatbot_closer"]) == []
    assert ph.find_hits("I hope this helps", ["chatbot_closer"], allowlist=["I hope this helps"]) == []


def test_seed_presets_idempotent(tmp_path: Path) -> None:
    first = seed_result_check_presets(tmp_path)
    assert len(first) == 6
    hint = tmp_path / ".rulemason/result-check/prose-hygiene.hint.json"
    original = hint.read_text(encoding="utf-8")
    hint.write_text(original.replace("chatbot_closer", "em_dash"), encoding="utf-8")
    custom = hint.read_text(encoding="utf-8")
    second = seed_result_check_presets(tmp_path)
    assert second == []
    assert hint.read_text(encoding="utf-8") == custom


def test_max_hits_truncation_strict() -> None:
    body = "\n".join(["I hope this helps"] * 3)
    report = run_check(
        {"text": body},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene",
            "rules": ["chatbot_closer"], "severity": "strict", "max_hits": 2,
        }]},
    )
    assert report.exit_code == 1
    assert "共 3 处" in report.items[0].explanation
    payload = json.loads(report.items[0].evidence or "{}")
    assert payload["hit_total"] == 3 and payload["hits_truncated"] is True


def test_run_files_with_packaged_via_tmp(tmp_path: Path) -> None:
    rec = tmp_path / "r.json"
    req = tmp_path / "q.json"
    rec.write_text(json.dumps({"text": "plain"}), encoding="utf-8")
    req.write_text(packaged_result_check_preset("hint"), encoding="utf-8")
    report = run_files(rec, req)
    assert isinstance(report, CheckReport)
    assert report.exit_code == 0


def test_cli_preset_hint_and_strict(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "record.json"
    rec.write_text(json.dumps({"text": "I hope this helps!"}), encoding="utf-8")
    code = run_cli("result-check", "--json", "--record", str(rec), "--preset", "hint")
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["exit_code"] == 0
    assert any(i["status"] == STATUS_HINT for i in payload["items"])

    code = run_cli("result-check", "--json", "--record", str(rec), "--preset", "strict")
    assert code == 1
    assert json.loads(capsys.readouterr().out)["exit_code"] == 1


def test_cli_preset_xor_requirements(tmp_path: Path, capsys) -> None:
    rec = tmp_path / "r.json"
    req = tmp_path / "q.json"
    rec.write_text(json.dumps({"text": "ok"}), encoding="utf-8")
    req.write_text(packaged_result_check_preset("hint"), encoding="utf-8")
    msg = run_cli(
        "result-check", "--record", str(rec),
        "--requirements", str(req), "--preset", "hint",
    )
    assert isinstance(msg, str) and "--requirements 或 --preset" in msg
    msg = run_cli("result-check", "--record", str(rec))
    assert isinstance(msg, str) and "--requirements 或 --preset" in msg


def test_cli_uses_project_seed_over_packaged(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_result_check_presets(tmp_path)
    hint = tmp_path / ".rulemason/result-check/prose-hygiene.hint.json"
    # 用户关掉全部推荐短名：仅保留空跑用的 chatbot，再换成不命中的正文规则集——改为只开 em_dash
    hint.write_text(json.dumps({
        "schema": 1,
        "checks": [{
            "id": "prose-hygiene",
            "type": "prose_hygiene",
            "rules": ["em_dash"],
            "severity": "hint",
        }],
    }), encoding="utf-8")
    # 清单存在才算项目根
    (tmp_path / ".rulemason.yaml").write_text("version: 0\nfiles: {}\n", encoding="utf-8")
    rec = tmp_path / "record.json"
    rec.write_text(json.dumps({"text": "I hope this helps — really."}), encoding="utf-8")
    code = run_cli("result-check", "--json", "--record", str(rec), "--preset", "hint")
    assert code == 0
    items = json.loads(capsys.readouterr().out)["items"]
    assert items[0]["status"] == STATUS_HINT  # em_dash 命中为提示
    blob = json.dumps(items[0], ensure_ascii=False)
    assert "em_dash" in blob


def test_signpost_and_not_just_and_path(tmp_path: Path) -> None:
    assert ph.find_hits("Let's dive in to the topic", ["signpost_opener"])
    assert ph.find_hits("Not just fast but accurate", ["not_just_contrast"])
    report = run_check(
        {"structured": {"body": "I hope this helps"}},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene",
            "rules": ["chatbot_closer"], "path": "body",
        }]},
    )
    assert report.exit_code == 0
    assert report.items[0].status == STATUS_HINT


def test_unknown_rule_is_input_error() -> None:
    report = run_check(
        {"text": "ok"},
        {"schema": 1, "checks": [{
            "id": "p", "type": "prose_hygiene", "rules": ["not_a_rule"],
        }]},
    )
    assert report.exit_code == 2


@pytest.mark.parametrize("phrase,rule", [
    ("希望对你有帮助", "chatbot_closer"),
    ("本文将探讨主题", "signpost_opener"),
    ("不只是快更是稳", "not_just_contrast"),
])
def test_chinese_phrases(phrase: str, rule: str) -> None:
    assert ph.find_hits(phrase, [rule])


def test_hint_does_not_swallow_unknown_or_input_error() -> None:
    unknown = run_check(
        {"structured": {"x": 1}},  # no text
        {"schema": 1, "checks": [
            {"id": "p", "type": "prose_hygiene", "rules": ["chatbot_closer"]},
            {"id": "c", "type": "cjk_typography", "rules": ["cjk_latin_space"]},
        ]},
    )
    assert unknown.exit_code == 1
    assert any(i.status == "无法判断" for i in unknown.items)

    bad = run_check(
        {"text": "I hope this helps"},
        {"schema": 1, "checks": [
            {"id": "p", "type": "prose_hygiene", "rules": ["chatbot_closer"]},
            {"id": "b", "type": "prose_hygiene", "rules": ["nope"]},
        ]},
    )
    assert bad.exit_code == 2
    assert any(i.status == STATUS_HINT for i in bad.items)
    assert any(i.status == "输入错误" for i in bad.items)


def test_remove_deletes_seed_presets(tmp_path: Path) -> None:
    from conftest import commit, git_init, write

    from rulemason import init, remove

    root = tmp_path / "proj"
    git_init(root)
    write(root, "README.md", "demo\n")
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    commit(root)
    assert init.run(root, "claude", True) == 0
    hint = root / ".rulemason/result-check/prose-hygiene.hint.json"
    strict = root / ".rulemason/result-check/prose-hygiene.strict.json"
    pa = root / ".rulemason/result-check/product-artifact.hint.json"
    assert hint.is_file() and strict.is_file() and pa.is_file()
    assert remove.run(root, yes=True) == 0
    assert not hint.exists() and not strict.exists() and not pa.exists()
    assert not (root / ".rulemason").exists()


def test_init_seeds_not_in_manifest_and_survive_update(tmp_path: Path) -> None:
    from conftest import commit, git_init, write

    from rulemason import check, init, shared, update

    root = tmp_path / "proj"
    git_init(root)
    write(root, "README.md", "demo\n")
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    commit(root)
    assert init.run(root, "claude", True) == 0
    files = shared.read_manifest(root)["files"]
    seed = ".rulemason/result-check/prose-hygiene.hint.json"
    assert ".rulemason/rules/prose-hygiene.md" in files
    assert ".rulemason/rules/agent-coding-caution.md" in files
    assert ".rulemason/rules/product-artifact-caution.md" in files
    assert seed not in files
    assert ".rulemason/result-check/product-artifact.hint.json" not in files
    path = root / seed
    custom = path.read_text(encoding="utf-8").replace("chatbot_closer", "em_dash")
    path.write_text(custom, encoding="utf-8")
    assert check.run(root)[1] == 0
    assert update.run(root, yes=True) == 0
    assert path.read_text(encoding="utf-8") == custom
