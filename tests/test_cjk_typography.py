"""cjk_typography：纯函数与 result-check 接线验收。"""
from __future__ import annotations

import json
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

ALL_RULES = sorted(cjk.KNOWN_RULES)


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


def test_new_rules_halfwidth_alpha_ideo():
    assert cjk.find_hits("你好,世界", ["halfwidth_punct_cjk"])
    assert not cjk.find_hits("你好，世界", ["halfwidth_punct_cjk"])
    assert not cjk.find_hits("你好.世界", ["halfwidth_punct_cjk"])
    assert cjk.find_hits("ＡＢ", ["fullwidth_alpha"])
    assert not cjk.find_hits("AB", ["fullwidth_alpha"])
    assert cjk.find_hits("你好\u3000世界", ["ideographic_space"])
    # 未列入 rules 不启用
    assert not cjk.find_hits("你好,世界", ["cjk_latin_space"])


def test_cjk_ext_a_and_fw_punct_narrow():
    # 扩展 A：㐀 U+3400
    assert cjk.find_hits("㐀Git", ["cjk_latin_space"])
    # 表格竖线旁不报
    assert not cjk.find_hits("| 看（说明） | x |\n", ["fw_punct_space"])
    # 强调标记旁不报
    assert not cjk.find_hits("见 **THEN** 「说明」", ["fw_punct_space"])
    # URL 占位旁不报（裸 URL 剥离）
    assert not cjk.find_hits("见 https://ex.com/a ，即可", ["fw_punct_space"])


def test_preprocess_code_url_and_link_visible_text():
    assert not cjk.find_hits("见 `使用Git` 即可", ["cjk_latin_space"])
    assert not cjk.find_hits("文件（`.rulemason/`）、入口", ["fw_punct_space"])
    assert not cjk.find_hits("见 https://example.com/使用Git 即可", ["cjk_latin_space"])
    hits = cjk.find_hits("见[使用Git](https://example.com/x)说明", ["cjk_latin_space"])
    assert hits
    assert not cjk.find_hits("见[说明](https://example.com/使用Git)即可", ["cjk_latin_space"])
    # ~~~ 围栏
    assert not cjk.find_hits("前\n~~~\n使用Git\n~~~\n后", ["cjk_latin_space"])
    # 尖括号自动链接
    assert not cjk.find_hits("见 <https://example.com/使用Git> 即可", ["cjk_latin_space"])
    # 引用式链接定义
    assert not cjk.find_hits("见[说明][x]。\n\n[x]: https://example.com/使用Git\n", ["cjk_latin_space"])
    # CommonMark 缩进代码：空行后四空格
    assert not cjk.find_hits("段。\n\n    使用Git\n\n后", ["cjk_latin_space"])


def test_disable_enable_directives():
    text = "前使用Git\n<!-- rulemason-disable -->\n中使用Git\n<!-- rulemason-enable -->\n后使用Git"
    hits = cjk.find_hits(text, ["cjk_latin_space"])
    assert len(hits) == 2  # 前、后；中间关闭
    # 按名关闭
    text2 = "<!-- rulemason-disable halfwidth_punct_cjk -->\n你好,世界 使用Git\n<!-- rulemason-enable -->"
    hits2 = cjk.find_hits(text2, ["halfwidth_punct_cjk", "cjk_latin_space"])
    assert all(h.rule == "cjk_latin_space" for h in hits2)
    # 代码块内注释不生效
    text3 = "```\n<!-- rulemason-disable -->\n```\n使用Git"
    assert cjk.find_hits(text3, ["cjk_latin_space"])
    # 未知短名
    assert cjk.directive_error("<!-- rulemason-disable no_such -->\nx") is not None


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
    assert "共 1 处" in bad.items[0].explanation
    payload = json.loads(bad.items[0].evidence or "{}")
    assert payload["hit_total"] == 1
    assert payload["hits_truncated"] is False
    assert payload["hits"][0]["rule"] == "cjk_latin_space"
    assert "line" in payload["hits"][0] and "column" in payload["hits"][0]
    human = render_human(bad)
    assert "使用Git" not in human
    assert "使用Git" not in (bad.items[0].evidence or "")

    err = run_check({"text": "x"}, _req(rules=["no_such_rule"]))
    assert err.exit_code == EXIT_INPUT_ERROR
    assert err.items[0].status == STATUS_INPUT_ERROR

    unknown = run_check({}, _req())
    assert unknown.items[0].status == STATUS_UNKNOWN
    assert unknown.exit_code == EXIT_NOT_PASS

    bad_dir = run_check({"text": "<!-- rulemason-disable nope -->\nx"}, _req(rules=["cjk_latin_space"]))
    assert bad_dir.exit_code == EXIT_INPUT_ERROR


def test_multi_hits_and_truncation():
    body = "\n".join(["使用Git"] * 3)
    report = run_check({"text": body}, _req(rules=["cjk_latin_space"], max_hits=2))
    assert report.items[0].status == STATUS_FAIL
    assert "共 3 处" in report.items[0].explanation
    assert "显示前 2 处" in report.items[0].explanation
    payload = json.loads(report.items[0].evidence or "{}")
    assert payload["hit_total"] == 3
    assert payload["hits_truncated"] is True
    assert len(payload["hits"]) == 2


def test_path_skip_and_default_units():
    skip = run_check({"structured": {"结论": "x"}}, _req(path="步骤.文案", rules=["cjk_latin_space"]))
    assert skip.items[0].status == STATUS_SKIP

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
    assert "rulemason-disable" in text
    assert "halfwidth_punct_cjk" in text or "max_hits" in text
