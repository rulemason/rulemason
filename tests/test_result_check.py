"""result-check：确定性运行结果检查的单元与 CLI 验收。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import run_cli

from rulemason import cli
from rulemason.result_check import (
    EXIT_INPUT_ERROR,
    EXIT_NOT_PASS,
    EXIT_OK,
    STATUS_FAIL,
    STATUS_INPUT_ERROR,
    STATUS_PASS,
    STATUS_SKIP,
    STATUS_UNKNOWN,
    render_human,
    run_check,
    run_files,
)

FIX = Path(__file__).parent / "fixtures" / "result_check"


def test_empty_requirements_is_input_error():
    report = run_check({"text": "hi"}, {"checks": []})
    assert report.exit_code == EXIT_INPUT_ERROR
    assert report.overall_pass is False
    assert any("空" in e for e in report.input_errors)


def test_must_contain_pass_fail_unknown_and_bad_pattern():
    assert run_check({"text": "用神妻财"}, {"checks": [
        {"id": "a", "type": "must_contain", "texts": ["妻财"]},
    ]}).items[0].status == STATUS_PASS
    assert run_check({"text": "无相关"}, {"checks": [
        {"id": "a", "type": "must_contain", "texts": ["妻财"]},
    ]}).items[0].status == STATUS_FAIL
    assert run_check({}, {"checks": [
        {"id": "a", "type": "must_contain", "texts": ["妻财"]},
    ]}).items[0].status == STATUS_UNKNOWN
    bad = run_check({"text": "x"}, {"checks": [
        {"id": "p", "type": "pattern", "pattern": "("},
    ]})
    assert bad.items[0].status == STATUS_INPUT_ERROR
    assert bad.exit_code == EXIT_INPUT_ERROR


def test_must_not_contain_and_forbid_hit():
    ok = run_check({"text": "宜观望"}, {"checks": [
        {"id": "f", "type": "must_not_contain", "texts": ["必然成功"]},
    ]})
    assert ok.items[0].status == STATUS_PASS
    hit = run_check({"text": "此事必然成功"}, {"checks": [
        {"id": "f", "type": "must_not_contain", "texts": ["必然成功"]},
    ]})
    assert hit.items[0].status == STATUS_FAIL
    assert hit.overall_pass is False


def test_structured_keys_missing_and_absent():
    missing = run_check({"structured": {"结论": "ok"}}, {"checks": [
        {"id": "s", "type": "structured_keys", "keys": ["结论", "专业断卦"]},
    ]})
    assert missing.items[0].status == STATUS_FAIL
    assert "专业断卦" in missing.items[0].explanation
    absent = run_check({"text": "结论 专业断卦"}, {"checks": [
        {"id": "s", "type": "structured_keys", "keys": ["结论"]},
    ]})
    assert absent.items[0].status == STATUS_UNKNOWN


def test_skill_requirement_is_input_error_not_pass():
    report = run_check({"text": "x", "structured": {"结论": "a"}}, {"checks": [
        {"id": "sk", "type": "skill_present", "name": "rulemason"},
        {"id": "ok", "type": "must_contain", "texts": ["x"]},
    ]})
    skill = next(i for i in report.items if i.id == "sk")
    assert skill.status == STATUS_INPUT_ERROR
    assert skill.status != STATUS_PASS
    assert report.exit_code == EXIT_INPUT_ERROR
    assert report.overall_pass is False


def test_mixed_one_fail_blocks_overall_and_skip_not_pass():
    mixed = run_check({"text": "妻财"}, {"checks": [
        {"id": "ok", "type": "must_contain", "texts": ["妻财"]},
        {"id": "bad", "type": "must_contain", "texts": ["没有的字"]},
    ]})
    assert mixed.overall_pass is False
    assert mixed.exit_code == EXIT_NOT_PASS
    skipped = run_check({"text": "妻财"}, {"checks": [
        {"id": "ok", "type": "must_contain", "texts": ["妻财"]},
        {"id": "na", "type": "skip", "reason": "调用方声明不适用"},
    ]})
    assert skipped.items[1].status == STATUS_SKIP
    assert skipped.overall_pass is True


def test_unknown_mixed_with_pass_blocks_overall():
    report = run_check({"structured": {"结论": "a", "信心度": 1, "白话推理": "b", "专业断卦": "c", "签语": "d"}}, {
        "checks": [
            {"id": "s", "type": "structured_keys",
             "keys": ["结论", "信心度", "白话推理", "专业断卦", "签语"]},
            {"id": "t", "type": "must_contain", "texts": ["妻财"]},
        ],
    })
    assert report.items[0].status == STATUS_PASS
    assert report.items[1].status == STATUS_UNKNOWN
    assert report.overall_pass is False
    assert report.exit_code == EXIT_NOT_PASS


def test_default_report_omits_full_text_and_has_limits():
    long_text = "前言" + ("很长很长的正文内容" * 20) + "妻财" + ("尾巴" * 20)
    report = run_check(
        {"text": long_text, "source": {"kind": "fixture", "id": "t"}, "limits": "仅 fixture"},
        {"checks": [{"id": "a", "type": "must_contain", "texts": ["妻财"]}]},
    )
    human = render_human(report)
    assert long_text not in human
    assert report.items[0].evidence is None or long_text not in (report.items[0].evidence or "")
    assert "限度" in human
    assert report.limits
    assert "fixture" in report.limits or "fixture" in human


def test_fixture_interpret_ok_passes():
    report = run_files(FIX / "interpret_ok.json", FIX / "requirements_ok.json")
    assert report.overall_pass is True
    assert report.exit_code == EXIT_OK
    assert all(i.status == STATUS_PASS for i in report.items)


def test_fixture_missing_field_and_forbidden_word_fail(tmp_path: Path):
    base = json.loads((FIX / "interpret_ok.json").read_text(encoding="utf-8"))
    broken = dict(base)
    broken["structured"] = {k: v for k, v in base["structured"].items() if k != "专业断卦"}
    p = tmp_path / "broken.json"
    p.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    r1 = run_files(p, FIX / "requirements_ok.json")
    assert r1.overall_pass is False
    assert r1.exit_code == EXIT_NOT_PASS

    banned = dict(base)
    banned["text"] = base["text"] + "此事必然成功"
    banned["structured"] = dict(base["structured"])
    banned["structured"]["结论"] = "必然成功"
    p2 = tmp_path / "banned.json"
    p2.write_text(json.dumps(banned, ensure_ascii=False), encoding="utf-8")
    r2 = run_files(p2, FIX / "requirements_ok.json")
    assert r2.overall_pass is False
    assert any(i.status == STATUS_FAIL for i in r2.items)


def test_cli_help_mentions_scope_keywords(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["result-check", "--help"])
    assert e.value.code == 0
    text = capsys.readouterr().out
    for key in ("fixture", "Skill", "解读", "check", "judge", "field", "value_type", "码点", "optional"):
        assert key in text
    with pytest.raises(SystemExit) as e2:
        cli.main(["check", "--help"])
    assert e2.value.code == 0
    assert "--json" in capsys.readouterr().out


def test_cli_exit_codes_and_check_json_schema_unchanged(tmp_path: Path, capsys):
    code = run_cli(
        "result-check", "--json",
        "--record", str(FIX / "interpret_ok.json"),
        "--requirements", str(FIX / "requirements_ok.json"),
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_pass"] is True
    assert payload["exit_code"] == EXIT_OK
    assert payload["schema"] == 1

    empty_req = tmp_path / "empty.json"
    empty_req.write_text('{"checks": []}', encoding="utf-8")
    code = run_cli(
        "result-check", "--json",
        "--record", str(FIX / "interpret_ok.json"),
        "--requirements", str(empty_req),
    )
    assert code == EXIT_INPUT_ERROR
    assert json.loads(capsys.readouterr().out)["overall_pass"] is False

    missing = dict(json.loads((FIX / "interpret_ok.json").read_text(encoding="utf-8")))
    del missing["text"]
    miss_path = tmp_path / "no_text.json"
    miss_path.write_text(json.dumps(missing, ensure_ascii=False), encoding="utf-8")
    code = run_cli(
        "result-check", "--json",
        "--record", str(miss_path),
        "--requirements", str(FIX / "requirements_ok.json"),
    )
    assert code == EXIT_NOT_PASS
    capsys.readouterr()

    # check --json schema 仍为 1（不因本命令改动）
    run_cli("check", "--json")
    data = json.loads(capsys.readouterr().out)
    assert data["schema"] == 1


def test_banner_lists_result_check():
    from rulemason import banner
    assert any(cmd == "rulemason result-check" for cmd, _ in banner.COMMANDS)


def test_bad_json_and_missing_file_are_exit_2(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    code = run_cli(
        "result-check", "--json",
        "--record", str(bad),
        "--requirements", str(FIX / "requirements_ok.json"),
    )
    assert code == EXIT_INPUT_ERROR
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_pass"] is False
    assert payload["exit_code"] == EXIT_INPUT_ERROR
    assert payload["input_errors"]

    code = run_cli(
        "result-check", "--json",
        "--record", str(tmp_path / "missing-record.json"),
        "--requirements", str(FIX / "requirements_ok.json"),
    )
    assert code == EXIT_INPUT_ERROR
    assert json.loads(capsys.readouterr().out)["exit_code"] == EXIT_INPUT_ERROR


def test_all_skip_and_empty_id_are_input_error():
    all_skip = run_check({"text": "x"}, {"checks": [
        {"id": "a", "type": "skip", "reason": "不适用"},
        {"id": "b", "type": "skip"},
    ]})
    assert all_skip.exit_code == EXIT_INPUT_ERROR
    assert all_skip.overall_pass is False

    empty_id = run_check({"text": "x"}, {"checks": [
        {"id": "  ", "type": "must_contain", "texts": ["x"]},
    ]})
    assert empty_id.items[0].status == STATUS_INPUT_ERROR
    assert empty_id.exit_code == EXIT_INPUT_ERROR


def test_must_not_contain_unknown_without_text():
    report = run_check({}, {"checks": [
        {"id": "f", "type": "must_not_contain", "texts": ["必然成功"]},
    ]})
    assert report.items[0].status == STATUS_UNKNOWN
    assert report.exit_code == EXIT_NOT_PASS


def test_default_output_never_contains_full_original_text():
    """短文与长文：默认人读报告与 evidence 都不得包含完整输入原文（不是加省略号假装截断）。"""
    short = "短正文"
    short_report = run_check(
        {"text": short},
        {"checks": [{"id": "a", "type": "must_contain", "texts": ["短"]}]},
    )
    short_human = render_human(short_report)
    short_ev = short_report.items[0].evidence or ""
    assert short not in short_human
    assert short not in short_ev
    assert "字段 text" in short_ev and "长度" in short_ev

    long_text = "AAA" + ("正文块" * 40) + "命中词" + ("尾部" * 40)
    long_report = run_check(
        {"text": long_text},
        {"checks": [{"id": "a", "type": "must_contain", "texts": ["命中词"]}]},
    )
    long_human = render_human(long_report)
    long_ev = long_report.items[0].evidence or ""
    assert long_text not in long_human
    assert long_text not in long_ev
    assert len(long_ev) < len(long_text)


def _struct(data: dict) -> dict:
    return {"structured": data, "source": {"kind": "fixture"}, "limits": "fixture"}


def test_field_number_range_pass_and_fail():
    ok = run_check(_struct({"n": 3}), {"checks": [
        {"id": "n", "type": "field", "path": "n", "value_type": "integer", "minimum": 1, "maximum": 5},
    ]})
    assert ok.items[0].status == STATUS_PASS
    assert ok.exit_code == EXIT_OK
    bad = run_check(_struct({"n": 9}), {"checks": [
        {"id": "n", "type": "field", "path": "n", "value_type": "integer", "minimum": 1, "maximum": 5},
    ]})
    assert bad.items[0].status == STATUS_FAIL
    assert "maximum" in bad.items[0].explanation
    assert bad.exit_code == EXIT_NOT_PASS


def test_field_string_length_codepoints_and_no_full_echo():
    # 「守静待时自有转机」= 8 码点
    text = "守静待时自有转机"
    assert len(text) == 8
    ok = run_check(_struct({"签语": text}), {"checks": [
        {"id": "q", "type": "field", "path": "签语", "value_type": "string",
         "min_length": 6, "max_length": 14},
    ]})
    assert ok.items[0].status == STATUS_PASS
    long = "这是一段明显超过十四个汉字的签语内容啊"
    assert len(long) > 14
    bad = run_check(_struct({"签语": long}), {"checks": [
        {"id": "q", "type": "field", "path": "签语", "value_type": "string",
         "min_length": 6, "max_length": 14},
    ]})
    assert bad.items[0].status == STATUS_FAIL
    human = render_human(bad)
    assert long not in human
    assert long not in (bad.items[0].evidence or "")


def test_field_enum_pattern_array_items():
    enum_ok = run_check(_struct({"色": "红"}), {"checks": [
        {"id": "e", "type": "field", "path": "色", "value_type": "string", "enum": ["红", "蓝"]},
    ]})
    assert enum_ok.items[0].status == STATUS_PASS
    enum_bad = run_check(_struct({"色": "绿"}), {"checks": [
        {"id": "e", "type": "field", "path": "色", "value_type": "string", "enum": ["红", "蓝"]},
    ]})
    assert enum_bad.items[0].status == STATUS_FAIL

    pat_ok = run_check(_struct({"码": "AB-12"}), {"checks": [
        {"id": "p", "type": "field", "path": "码", "value_type": "string", "pattern": r"^[A-Z]+-\d+$"},
    ]})
    assert pat_ok.items[0].status == STATUS_PASS
    pat_bad = run_check(_struct({"码": "??"}), {"checks": [
        {"id": "p", "type": "field", "path": "码", "value_type": "string", "pattern": r"^[A-Z]+-\d+$"},
    ]})
    assert pat_bad.items[0].status == STATUS_FAIL

    arr_ok = run_check(_struct({"xs": [1, 2]}), {"checks": [
        {"id": "a", "type": "field", "path": "xs", "value_type": "array", "min_items": 1, "max_items": 3},
    ]})
    assert arr_ok.items[0].status == STATUS_PASS
    arr_bad = run_check(_struct({"xs": []}), {"checks": [
        {"id": "a", "type": "field", "path": "xs", "value_type": "array", "min_items": 1, "max_items": 3},
    ]})
    assert arr_bad.items[0].status == STATUS_FAIL


def test_field_nested_null_missing_skip_and_undescendable():
    # 父 null → 子 skip
    null_parent = run_check(_struct({"应期": None}), {"checks": [
        {"id": "g", "type": "field", "path": "应期.推测", "value_type": "string", "min_length": 1},
    ]})
    assert null_parent.items[0].status == STATUS_SKIP

    # 父键缺失 → 子 skip
    missing_parent = run_check(_struct({"结论": "x"}), {"checks": [
        {"id": "g", "type": "field", "path": "应期.推测", "value_type": "string", "min_length": 1},
    ]})
    assert missing_parent.items[0].status == STATUS_SKIP

    # 父为对象、子空串 → 失败
    empty_child = run_check(_struct({"应期": {"推测": ""}}), {"checks": [
        {"id": "g", "type": "field", "path": "应期.推测", "value_type": "string", "min_length": 1},
    ]})
    assert empty_child.items[0].status == STATUS_FAIL

    # 父不可下降
    bad_parent = run_check(_struct({"应期": "不是对象"}), {"checks": [
        {"id": "g", "type": "field", "path": "应期.推测", "value_type": "string", "min_length": 1},
    ]})
    assert bad_parent.items[0].status == STATUS_FAIL
    assert "不可下降" in bad_parent.items[0].explanation

    # 末段在对象上缺失 → 失败
    leaf_missing = run_check(_struct({"应期": {}}), {"checks": [
        {"id": "g", "type": "field", "path": "应期.推测", "value_type": "string", "min_length": 1},
    ]})
    assert leaf_missing.items[0].status == STATUS_FAIL


def test_field_optional_and_union_null():
    opt = run_check(_struct({}), {"checks": [
        {"id": "y", "type": "field", "path": "应期", "value_type": ["object", "null"], "optional": True},
    ]})
    assert opt.items[0].status == STATUS_PASS
    null_ok = run_check(_struct({"应期": None}), {"checks": [
        {"id": "y", "type": "field", "path": "应期", "value_type": ["object", "null"], "optional": True},
    ]})
    assert null_ok.items[0].status == STATUS_PASS
    required_missing = run_check(_struct({}), {"checks": [
        {"id": "y", "type": "field", "path": "应期", "value_type": ["object", "null"]},
    ]})
    assert required_missing.items[0].status == STATUS_FAIL


def test_field_illegal_config_is_input_error():
    unknown = run_check(_struct({"a": 1}), {"checks": [
        {"id": "x", "type": "field", "path": "a", "value_type": "integer", "foo": 1},
    ]})
    assert unknown.exit_code == EXIT_INPUT_ERROR
    mismatch = run_check(_struct({"a": 1}), {"checks": [
        {"id": "x", "type": "field", "path": "a", "value_type": "integer", "min_length": 1},
    ]})
    assert mismatch.exit_code == EXIT_INPUT_ERROR
    bad_pat = run_check(_struct({"a": "x"}), {"checks": [
        {"id": "x", "type": "field", "path": "a", "value_type": "string", "pattern": "("},
    ]})
    assert bad_pat.exit_code == EXIT_INPUT_ERROR


def test_field_no_structured_is_unknown():
    report = run_check({"text": "x"}, {"checks": [
        {"id": "x", "type": "field", "path": "a", "value_type": "string"},
    ]})
    assert report.items[0].status == STATUS_UNKNOWN
    assert report.exit_code == EXIT_NOT_PASS


def test_yaomancy_shaped_field_requirements_and_null_yingqi():
    ok = run_files(FIX / "interpret_ok.json", FIX / "requirements_yaomancy_fields.json")
    assert ok.overall_pass is True
    assert ok.exit_code == EXIT_OK
    # 应期.推测 有值 → 通过；应期 null 样例：子项 skip，其余通过
    null_case = run_files(FIX / "interpret_yingqi_null.json", FIX / "requirements_yaomancy_fields.json")
    by_id = {i.id: i for i in null_case.items}
    assert by_id["yingqi-type"].status == STATUS_PASS
    assert by_id["yingqi-guess"].status == STATUS_SKIP
    assert by_id["confidence"].status == STATUS_PASS
    assert by_id["qianyu-len"].status == STATUS_PASS
    assert null_case.overall_pass is True
    assert null_case.exit_code == EXIT_OK


def test_old_requirements_still_pass_with_field_present():
    report = run_files(FIX / "interpret_ok.json", FIX / "requirements_ok.json")
    assert report.overall_pass is True
    assert report.exit_code == EXIT_OK
