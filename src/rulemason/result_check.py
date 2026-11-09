"""对调用方提供的已发生运行记录做确定性检查：文本 / 结构化 / 汇总与报告（不含 Skill 采集）。"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = 1
STATUS_PASS = "通过"
STATUS_FAIL = "失败"
STATUS_UNKNOWN = "无法判断"
STATUS_SKIP = "未检查/不适用"
STATUS_INPUT_ERROR = "输入错误"

EXIT_OK = 0
EXIT_NOT_PASS = 1
EXIT_INPUT_ERROR = 2

CHECK_MUST_CONTAIN = "must_contain"
CHECK_MUST_NOT_CONTAIN = "must_not_contain"
CHECK_PATTERN = "pattern"
CHECK_STRUCTURED_KEYS = "structured_keys"
CHECK_SKILL = "skill_present"
CHECK_SKIP = "skip"

SKILL_TYPES = frozenset({CHECK_SKILL, "skill", "skill_call", "skill_calls"})


@dataclass
class ItemResult:
    id: str
    status: str
    explanation: str
    evidence: str | None = None


@dataclass
class CheckReport:
    schema: int
    overall_pass: bool
    exit_code: int
    items: list[ItemResult] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)
    scope: str = ""
    limits: str = ""
    input_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "overall_pass": self.overall_pass,
            "exit_code": self.exit_code,
            "items": [asdict(i) for i in self.items],
            "source": self.source,
            "scope": self.scope,
            "limits": self.limits,
            "input_errors": self.input_errors,
        }


def load_json(path: Path) -> Any:
    """读取 UTF-8 JSON 文件；损坏时抛 ValueError。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 无法解析：{path}（{exc}）") from exc


def _excerpt(text: str, needle: str = "", limit: int = 48) -> str:
    """复核依据：优先字段定位；仅当摘录严格短于全文时附带正文片段（不承诺脱敏）。"""
    if not text:
        return "字段 text；空"
    n = len(text)
    if needle and needle in text:
        i = text.index(needle)
        start = max(0, i - 12)
        end = min(n, i + len(needle) + 12)
        # 窗口盖住全文时附带片段会等于完整原文 → 只给定位
        if start == 0 and end == n:
            return f"字段 text；长度 {n}；匹配起始 {i}"
        chunk = text[start:end]
        prefix = "…" if start else ""
        suffix = "…" if end < n else ""
        return f"字段 text；长度 {n}；{prefix}{chunk}{suffix}"
    if n <= limit:
        return f"字段 text；长度 {n}"
    return f"字段 text；长度 {n}；{text[:limit]}…"


def _as_record(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("运行记录必须是 JSON 对象")
    return raw


def _as_requirements(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, dict):
        raise ValueError("检查要求必须是 JSON 对象")
    checks = raw.get("checks")
    if checks is None:
        raise ValueError("检查要求缺少 checks 字段")
    if not isinstance(checks, list):
        raise ValueError("checks 必须是数组")
    return checks


def _item_id(check: dict[str, Any], index: int) -> str:
    raw = check.get("id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return f"check-{index + 1}"


def _text_needles(check: dict[str, Any]) -> list[str] | None:
    """解析 texts/text；无效则返回 None。"""
    needles = check.get("texts") or check.get("text")
    if isinstance(needles, str):
        needles = [needles]
    if not isinstance(needles, list) or not needles or any(not isinstance(t, str) or not t for t in needles):
        return None
    return needles


def _text_field(record: dict[str, Any]) -> tuple[str | None, bool]:
    """返回 (正文, 已提供)。缺字段或显式 null 视为未采集。"""
    if "text" not in record:
        return None, False
    value = record["text"]
    if value is None:
        return None, False
    if not isinstance(value, str):
        raise ValueError("记录的 text 必须是字符串或 null")
    return value, True


def _structured_field(record: dict[str, Any]) -> tuple[Any, bool]:
    if "structured" not in record:
        return None, False
    value = record["structured"]
    if value is None:
        return None, False
    return value, True


def _eval_must_contain(check: dict[str, Any], text: str | None, provided: bool) -> ItemResult:
    cid = check["_id"]
    needles = _text_needles(check)
    if needles is None:
        return ItemResult(cid, STATUS_INPUT_ERROR, "必须包含要求缺少有效 texts")
    if not provided:
        return ItemResult(cid, STATUS_UNKNOWN, "未提供输出正文，无法判断必须包含")
    missing = [t for t in needles if t not in text]
    if missing:
        return ItemResult(cid, STATUS_FAIL, f"缺少必需文字：{missing[0]}", evidence=_excerpt(text or ""))
    return ItemResult(cid, STATUS_PASS, "必需文字均已出现", evidence=_excerpt(text or "", needles[0]))


def _eval_must_not_contain(check: dict[str, Any], text: str | None, provided: bool) -> ItemResult:
    cid = check["_id"]
    needles = _text_needles(check)
    if needles is None:
        return ItemResult(cid, STATUS_INPUT_ERROR, "禁止包含要求缺少有效 texts")
    if not provided:
        return ItemResult(cid, STATUS_UNKNOWN, "未提供输出正文，无法判断禁止包含")
    for t in needles:
        if t in text:
            return ItemResult(cid, STATUS_FAIL, f"出现禁止文字：{t}", evidence=_excerpt(text or "", t))
    return ItemResult(cid, STATUS_PASS, "未出现禁止文字")


def _eval_pattern(check: dict[str, Any], text: str | None, provided: bool) -> ItemResult:
    cid = check["_id"]
    pattern = check.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        return ItemResult(cid, STATUS_INPUT_ERROR, "模式要求缺少有效 pattern")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        return ItemResult(cid, STATUS_INPUT_ERROR, f"模式非法：{exc}")
    if not provided:
        return ItemResult(cid, STATUS_UNKNOWN, "未提供输出正文，无法判断模式")
    if compiled.search(text or "") is None:
        return ItemResult(cid, STATUS_FAIL, "正文不匹配给定模式", evidence=_excerpt(text or ""))
    return ItemResult(cid, STATUS_PASS, "正文匹配给定模式", evidence=_excerpt(text or ""))


def _eval_structured_keys(check: dict[str, Any], structured: Any, provided: bool) -> ItemResult:
    cid = check["_id"]
    keys = check.get("keys")
    if not isinstance(keys, list) or not keys or any(not isinstance(k, str) or not k for k in keys):
        return ItemResult(cid, STATUS_INPUT_ERROR, "结构化要求缺少有效 keys")
    if not provided:
        return ItemResult(cid, STATUS_UNKNOWN, "未提供结构化输出，无法判断必填字段")
    if not isinstance(structured, dict):
        return ItemResult(cid, STATUS_FAIL, "结构化输出不可解析为对象")
    missing = [k for k in keys if k not in structured]
    if missing:
        return ItemResult(cid, STATUS_FAIL, f"缺少必填字段：{', '.join(missing)}")
    return ItemResult(cid, STATUS_PASS, "结构化可解析且必填字段齐全")


def _eval_one(check: dict[str, Any], record: dict[str, Any]) -> ItemResult:
    ctype = check.get("type")
    cid = check["_id"]
    if not isinstance(ctype, str) or not ctype.strip():
        return ItemResult(cid, STATUS_INPUT_ERROR, "检查项缺少有效 type")
    ctype = ctype.strip()
    if ctype in SKILL_TYPES:
        return ItemResult(cid, STATUS_INPUT_ERROR, "本期排除 Skill 出现检查，不得将该项记为通过")
    if ctype == CHECK_SKIP:
        reason = check.get("reason") if isinstance(check.get("reason"), str) else "调用方声明不适用"
        return ItemResult(cid, STATUS_SKIP, reason)
    text, text_ok = _text_field(record)
    structured, struct_ok = _structured_field(record)
    if ctype == CHECK_MUST_CONTAIN:
        return _eval_must_contain(check, text, text_ok)
    if ctype == CHECK_MUST_NOT_CONTAIN:
        return _eval_must_not_contain(check, text, text_ok)
    if ctype == CHECK_PATTERN:
        return _eval_pattern(check, text, text_ok)
    if ctype == CHECK_STRUCTURED_KEYS:
        return _eval_structured_keys(check, structured, struct_ok)
    return ItemResult(cid, STATUS_INPUT_ERROR, f"未知检查类型：{ctype}")


def _default_limits(source: dict[str, Any]) -> str:
    kind = source.get("kind") if isinstance(source.get("kind"), str) else ""
    if kind == "fixture":
        return "输入为离线 fixture，不等于真实模型会话或线上解读"
    if kind == "eval_report":
        return "输入由调用方从 eval 报告映射而来；本检查不验证报告真伪"
    return "来源标识可核对，不等于防伪或真实性验证；未采集的证据不得默认通过"


def _meta_from_record(record: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    source = dict(record["source"]) if isinstance(record.get("source"), dict) else {}
    scope = record["scope"] if isinstance(record.get("scope"), str) else ""
    limits = record["limits"] if isinstance(record.get("limits"), str) else ""
    if not limits:
        limits = _default_limits(source)
    return source, scope, limits


def _eval_checks(checks: list[Any], record: dict[str, Any]) -> list[ItemResult]:
    items: list[ItemResult] = []
    for i, check in enumerate(checks):
        if not isinstance(check, dict):
            items.append(ItemResult(f"check-{i + 1}", STATUS_INPUT_ERROR, "检查项必须是对象"))
            continue
        if "id" in check and isinstance(check["id"], str) and not check["id"].strip():
            items.append(ItemResult(f"check-{i + 1}", STATUS_INPUT_ERROR, "检查名为空"))
            continue
        annotated = dict(check)
        annotated["_id"] = _item_id(check, i)
        try:
            items.append(_eval_one(annotated, record))
        except ValueError as exc:
            items.append(ItemResult(annotated["_id"], STATUS_INPUT_ERROR, str(exc)))
    return items


def _summarize(items: list[ItemResult], input_errors: list[str]) -> tuple[bool, int, list[str]]:
    """返回 (overall_pass, exit_code, 可能追加的 input_errors)。"""
    errors = list(input_errors)
    has_input_error = any(it.status == STATUS_INPUT_ERROR for it in items) or bool(errors)
    required = [it for it in items if it.status != STATUS_SKIP]
    overall = (
        not has_input_error
        and bool(required)
        and all(it.status == STATUS_PASS for it in required)
    )
    if has_input_error:
        code = EXIT_INPUT_ERROR
    elif overall:
        code = EXIT_OK
    else:
        code = EXIT_NOT_PASS
    if not required and not has_input_error:
        # 全部 skip 且无错误：空有效集不得通过
        errors.append("有效检查项为空（全部为未检查/不适用）")
        overall = False
        code = EXIT_INPUT_ERROR
    return overall, code, errors


def run_check(record_raw: Any, requirements_raw: Any) -> CheckReport:
    """对一份记录与一份要求执行确定性检查。

    返回 CheckReport：overall_pass 仅在全部必需项通过且无输入错误时为 True；
    exit_code 为 0 / 1 / 2。
    """
    try:
        record = _as_record(record_raw)
        checks = _as_requirements(requirements_raw)
    except ValueError as exc:
        return CheckReport(
            schema=SCHEMA, overall_pass=False, exit_code=EXIT_INPUT_ERROR,
            items=[], source={}, scope="", limits="输入损坏，未执行逐项检查",
            input_errors=[str(exc)],
        )

    source, scope, limits = _meta_from_record(record)
    if len(checks) == 0:
        return CheckReport(
            schema=SCHEMA, overall_pass=False, exit_code=EXIT_INPUT_ERROR,
            items=[], source=source, scope=scope or "空要求集", limits=limits,
            input_errors=["检查要求集合为空"],
        )

    items = _eval_checks(checks, record)
    overall, code, errors = _summarize(items, [])
    return CheckReport(
        schema=SCHEMA, overall_pass=overall, exit_code=code,
        items=items, source=source, scope=scope, limits=limits,
        input_errors=errors,
    )


def render_human(report: CheckReport) -> str:
    """默认人读报告：状态与短摘录，不含完整输入原文。"""
    lines = [
        f"总体：{'通过' if report.overall_pass else '未通过'}（exit={report.exit_code}）",
        f"来源：{json.dumps(report.source, ensure_ascii=False) if report.source else '（未提供）'}",
        f"范围：{report.scope or '（未提供）'}",
        f"限度：{report.limits}",
    ]
    if report.input_errors:
        lines.append("输入错误：" + "；".join(report.input_errors))
    for it in report.items:
        ev = f"；依据={it.evidence}" if it.evidence else ""
        lines.append(f"- [{it.id}] {it.status}：{it.explanation}{ev}")
    return "\n".join(lines)


def run_files(record_path: Path, requirements_path: Path) -> CheckReport:
    """从两个 JSON 文件运行检查；缺文件或损坏 JSON 归一为输入错误（exit 2）。"""
    try:
        record_raw = load_json(record_path)
        requirements_raw = load_json(requirements_path)
    except FileNotFoundError as exc:
        return CheckReport(
            schema=SCHEMA, overall_pass=False, exit_code=EXIT_INPUT_ERROR,
            items=[], source={}, scope="", limits="输入文件缺失，未执行逐项检查",
            input_errors=[f"文件不存在：{exc.filename or exc}"],
        )
    except OSError as exc:
        return CheckReport(
            schema=SCHEMA, overall_pass=False, exit_code=EXIT_INPUT_ERROR,
            items=[], source={}, scope="", limits="输入文件不可读，未执行逐项检查",
            input_errors=[f"无法读取文件：{exc}"],
        )
    except ValueError as exc:
        return CheckReport(
            schema=SCHEMA, overall_pass=False, exit_code=EXIT_INPUT_ERROR,
            items=[], source={}, scope="", limits="输入损坏，未执行逐项检查",
            input_errors=[str(exc)],
        )
    return run_check(record_raw, requirements_raw)
