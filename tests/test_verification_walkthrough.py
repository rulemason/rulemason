"""verification-walkthrough 结构预设：hint/strict、不偷换旧短名、种子生命周期。"""
from __future__ import annotations

import json
from pathlib import Path

from rulemason import cli
from rulemason.result_check import STATUS_HINT, run_check
from rulemason.shared import packaged_result_check_preset, seed_result_check_presets


def _run_cli(*argv: str):
    try:
        cli.main(list(argv))
    except SystemExit as exc:
        return exc.code
    return 0


COMPLETE = (
    "# 功能走查\n\n"
    "## 验证走查\n会话记录。\n\n"
    "## 可观察期望\n列表页显示三条。\n\n"
    "## 差距与待决\n无。\n"
)

MISSING_GAPS = (
    "# 功能走查\n\n"
    "## 验证走查\n会话记录。\n\n"
    "## 可观察期望\n列表页显示三条。\n"
)


def test_preset_short_names_not_stolen() -> None:
    prose = json.loads(packaged_result_check_preset("hint"))
    assert prose["checks"][0]["type"] == "prose_hygiene"
    product = json.loads(packaged_result_check_preset("product-artifact.hint"))
    assert all(c["type"] == "pattern" for c in product["checks"])
    walk = json.loads(packaged_result_check_preset("verification-walkthrough.hint"))
    assert all(c["type"] == "pattern" for c in walk["checks"])
    assert all(c["severity"] == "hint" for c in walk["checks"])
    assert {c["id"] for c in walk["checks"]} == {
        "walkthrough-heading",
        "observable-expectation-heading",
        "gaps-heading",
    }
    strict = json.loads(packaged_result_check_preset("verification-walkthrough.strict"))
    assert all(c["severity"] == "strict" for c in strict["checks"])


def test_walkthrough_hint_alone_exit_zero(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "r.json"
    rec.write_text(json.dumps({"text": MISSING_GAPS}, ensure_ascii=False), encoding="utf-8")
    code = _run_cli(
        "result-check", "--json", "--record", str(rec),
        "--preset", "verification-walkthrough.hint",
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(i["status"] == STATUS_HINT for i in payload["items"])


def test_walkthrough_strict_fails_on_missing(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "r.json"
    rec.write_text(json.dumps({"text": MISSING_GAPS}, ensure_ascii=False), encoding="utf-8")
    code = _run_cli(
        "result-check", "--json", "--record", str(rec),
        "--preset", "verification-walkthrough.strict",
    )
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert any(i["status"] == "失败" for i in payload["items"])


def test_walkthrough_complete_passes() -> None:
    report = run_check(
        {"text": COMPLETE},
        json.loads(packaged_result_check_preset("verification-walkthrough.strict")),
    )
    assert report.exit_code == 0
    assert all(i.status == "通过" for i in report.items)


def test_english_synonym_headings_pass() -> None:
    text = (
        "# Review\n\n## Walkthrough\nnotes\n\n"
        "## Expected Behavior\nbutton enabled\n\n## Gaps\nnone\n"
    )
    report = run_check(
        {"text": text},
        json.loads(packaged_result_check_preset("verification-walkthrough.hint")),
    )
    assert report.exit_code == 0
    assert all(i.status == "通过" for i in report.items)


def test_keyword_in_prose_without_heading_is_miss() -> None:
    text = "本文讨论验证走查、可观察期望与差距，但没有独立小节。\n"
    report = run_check(
        {"text": text},
        json.loads(packaged_result_check_preset("verification-walkthrough.strict")),
    )
    assert report.exit_code == 1


def test_code_fence_fake_heading_false_positive() -> None:
    text = "摘要\n\n```\n## 验证走查\n## 可观察期望\n## 差距与待决\n```\n"
    report = run_check(
        {"text": text},
        json.loads(packaged_result_check_preset("verification-walkthrough.strict")),
    )
    assert report.exit_code == 0


def test_hint_does_not_swallow_other_failure() -> None:
    report = run_check(
        {"text": MISSING_GAPS},
        {
            "schema": 1,
            "checks": [
                *json.loads(packaged_result_check_preset("verification-walkthrough.hint"))["checks"],
                {"id": "must", "type": "must_contain", "texts": ["MISSING_TOKEN"]},
            ],
        },
    )
    assert report.exit_code == 1
    assert any(i.status == STATUS_HINT for i in report.items)
    assert any(i.status == "失败" for i in report.items)


def test_cli_short_names_still_prose_and_product(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "r.json"
    rec.write_text(json.dumps({"text": "I hope this helps"}, ensure_ascii=False), encoding="utf-8")
    # hint 仍是 prose：命中 closer 且默认 hint → exit 0
    assert _run_cli("result-check", "--json", "--record", str(rec), "--preset", "hint") == 0
    # product-artifact 缺标题 → hint exit 0
    rec.write_text(json.dumps({"text": "# 只有摘要\n"}, ensure_ascii=False), encoding="utf-8")
    assert _run_cli(
        "result-check", "--json", "--record", str(rec), "--preset", "product-artifact.hint",
    ) == 0


def test_seed_walkthrough_idempotent(tmp_path: Path) -> None:
    first = seed_result_check_presets(tmp_path)
    assert any(p.endswith("verification-walkthrough.hint.json") for p in first)
    path = tmp_path / ".rulemason/result-check/verification-walkthrough.hint.json"
    custom = path.read_text(encoding="utf-8").replace("Walkthrough", "WalkX")
    path.write_text(custom, encoding="utf-8")
    assert seed_result_check_presets(tmp_path) == []
    assert path.read_text(encoding="utf-8") == custom


def test_illegal_preset_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rec = tmp_path / "r.json"
    rec.write_text("{}", encoding="utf-8")
    code = _run_cli(
        "result-check", "--json", "--record", str(rec), "--preset", "verification-walkthrough",
    )
    assert code != 0
