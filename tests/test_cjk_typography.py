"""cjk_typography：纯函数与 result-check 接线验收。"""
from __future__ import annotations

from pathlib import Path

from rulemason import cjk_typography as cjk
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

ALL_RULES = [
    "fullwidth_digit", "stacked_punct", "cjk_latin_space", "cjk_digit_space",
    "unit_space", "degree_percent_nospace", "fw_punct_space",
]


def _req(**kwargs):
    base = {"id": "zh", "type": "cjk_typography", "rules": list(ALL_RULES)}
    base.update(kwargs)
    return {"checks": [base]}


def test_fullwidth_digit_and_stacked_punct():
    assert cjk.find_hits("共３项", ["fullwidth_digit"])[0].rule == "fullwidth_digit"
    assert not cjk.find_hits("共 3 项", ["fullwidth_digit"])
    assert cjk.find_hits("太好了！！", ["stacked_punct"])
    assert not cjk.find_hits("太好了？！", ["stacked_punct"])
    assert not cjk.find_hits("太好了?!", ["stacked_punct"])
    assert not cjk.find_hits("太好了！？", ["stacked_punct"])
    assert not cjk.find_hits("太好了!?", ["stacked_punct"])
    assert cjk.find_hits("太好了？！！", ["stacked_punct"])


def test_cjk_spaces_units_degree_fw_punct():
    assert cjk.find_hits("使用Git", ["cjk_latin_space"])
    assert not cjk.find_hits("使用 Git", ["cjk_latin_space"])
    assert cjk.find_hits("共3项", ["cjk_digit_space"])
    assert not cjk.find_hits("共 3 项", ["cjk_digit_space"])
    assert cjk.find_hits("速率10Gbps", ["unit_space"])
    assert not cjk.find_hits("速率 10 Gbps", ["unit_space"])
    assert cjk.find_hits("完成 15 %", ["degree_percent_nospace"])
    assert not cjk.find_hits("完成 15%", ["degree_percent_nospace"])
    assert cjk.find_hits("你好， 世界", ["fw_punct_space"])
    assert not cjk.find_hits("你好，世界", ["fw_punct_space"])


def test_preprocess_code_url_and_link_visible_text():
    assert not cjk.find_hits("见 `使用Git` 即可", ["cjk_latin_space"])
    # 剥离占位不得诱发全角标点旁空格
    assert not cjk.find_hits("文件（`.rulemason/`）、入口", ["fw_punct_space"])
    assert not cjk.find_hits("见 https://example.com/使用Git 即可", ["cjk_latin_space"])
    # 可见文案参检
    hits = cjk.find_hits("见[使用Git](https://example.com/x)说明", ["cjk_latin_space"])
    assert hits
    # 仅目标含路径不误报
    assert not cjk.find_hits("见[说明](https://example.com/使用Git)即可", ["cjk_latin_space"])


def test_allowlist_covers_brand():
    hits = cjk.find_hits("打开豆瓣FM收听", ["cjk_latin_space"], allowlist=["豆瓣FM"])
    assert not hits


def test_result_check_wiring_exit_codes():
    ok = run_check({"text": "使用 Git 共 3 项。"}, _req())
    assert ok.exit_code == EXIT_OK
    assert ok.items[0].status == STATUS_PASS

    bad = run_check({"text": "使用Git"}, _req(rules=["cjk_latin_space"]))
    assert bad.exit_code == EXIT_NOT_PASS
    assert bad.items[0].status == STATUS_FAIL
    assert "cjk_latin_space" in bad.items[0].explanation
    assert "码点偏移" in bad.items[0].explanation
    human = render_human(bad)
    assert "使用Git" not in human  # 不回显全文（短句可能整段等于命中；至少 evidence 无整段策略）
    assert "使用Git" not in (bad.items[0].evidence or "")

    err = run_check({"text": "x"}, _req(rules=["no_such_rule"]))
    assert err.exit_code == EXIT_INPUT_ERROR
    assert err.items[0].status == STATUS_INPUT_ERROR

    unknown = run_check({}, _req())
    assert unknown.items[0].status == STATUS_UNKNOWN
    assert unknown.exit_code == EXIT_NOT_PASS


def test_path_skip_and_default_units():
    skip = run_check({"structured": {"结论": "x"}}, _req(path="步骤.文案", rules=["cjk_latin_space"]))
    assert skip.items[0].status == STATUS_SKIP

    # 省略 units，默认含 Gbps
    bad = run_check({"text": "速率10Gbps"}, _req(rules=["unit_space"]))
    assert bad.items[0].status == STATUS_FAIL


def test_old_requirements_still_pass():
    report = run_files(FIX / "interpret_ok.json", FIX / "requirements_ok.json")
    assert report.overall_pass is True
    assert report.exit_code == EXIT_OK


def test_cli_help_mentions_cjk(capsys):
    import pytest

    from rulemason import cli
    with pytest.raises(SystemExit) as e:
        cli.main(["result-check", "--help"])
    assert e.value.code == 0
    text = capsys.readouterr().out
    assert "cjk_typography" in text
    assert "allowlist" in text
