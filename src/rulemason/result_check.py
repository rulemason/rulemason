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
CHECK_FIELD = "field"
CHECK_SKILL = "skill_present"
CHECK_SKIP = "skip"

SKILL_TYPES = frozenset({CHECK_SKILL, "skill", "skill_call", "skill_calls"})
# field 项允许的键：检查项 type 与值类型 value_type 分开，避免 JSON 键冲突
_FIELD_KEYS = frozenset({
    "id", "type", "path", "value_type", "optional",
    "minimum", "maximum", "min_length", "max_length",
    "enum", "pattern", "min_items", "max_items", "items",
})
# items 子对象允许的键（可再嵌 items；fields 仅一层；optional 只在 fields 条目）
_ITEMS_KEYS = frozenset({
    "value_type", "minimum", "maximum",
    "min_length", "max_length", "enum", "pattern",
    "min_items", "max_items", "items", "fields",
})
# fields 条目：对象元素上的标量/类型约束（禁止再嵌 fields）
_FIELD_PROP_KEYS = frozenset({
    "value_type", "optional", "minimum", "maximum",
    "min_length", "max_length", "enum", "pattern",
})
_VALUE_TYPES = frozenset({
    "string", "integer", "number", "boolean", "object", "array", "null",
})
_ITEMS_MAX_DEPTH = 4


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


def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_value_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def _parse_value_types(raw: Any) -> list[str] | None:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list) or not raw or any(not isinstance(t, str) or t not in _VALUE_TYPES for t in raw):
        return None
    return list(raw)


def _field_path_error(path: Any) -> str | None:
    if not isinstance(path, str) or not path.strip():
        return "field 要求缺少有效 path"
    if ".." in path or path.strip() != path or path.startswith(".") or path.endswith("."):
        return f"path 非法：{path}"
    if any(not seg for seg in path.split(".")):
        return f"path 非法：{path}"
    return None


def _field_shape_error(check: dict[str, Any]) -> str | None:
    if "optional" in check and not isinstance(check["optional"], bool):
        return "optional 必须是布尔值"
    for key in ("minimum", "maximum"):
        if key in check and (isinstance(check[key], bool) or not isinstance(check[key], (int, float))):
            return f"{key} 必须是数字"
    for key in ("min_length", "max_length", "min_items", "max_items"):
        if key in check and (not isinstance(check[key], int) or isinstance(check[key], bool) or check[key] < 0):
            return f"{key} 必须是非负整数"
    if "enum" in check and (not isinstance(check["enum"], list) or not check["enum"]):
        return "enum 必须是非空数组"
    if "pattern" in check and (not isinstance(check["pattern"], str) or not check["pattern"]):
        return "pattern 必须是非空字符串"
    if "pattern" in check:
        try:
            re.compile(check["pattern"])
        except re.error as exc:
            return f"字段模式非法：{exc}"
    return None


def _field_type_compat_error(check: dict[str, Any], value_types: list[str]) -> str | None:
    if not value_types:
        return None
    allows_string = bool(set(value_types) & {"string"})
    allows_number = bool(set(value_types) & {"integer", "number"})
    allows_array = "array" in value_types
    if any(k in check for k in ("min_length", "max_length", "pattern")) and not allows_string:
        return "长度/模式约束只能与 string 类型一起使用"
    if any(k in check for k in ("minimum", "maximum")) and not allows_number:
        return "数值范围约束只能与 integer/number 类型一起使用"
    if any(k in check for k in ("min_items", "max_items")) and not allows_array:
        return "数组长度约束只能与 array 类型一起使用"
    return None


def _constraint_block_error(
    block: dict[str, Any], allowed: frozenset[str], label: str,
) -> str | None:
    """校验不含 path 的约束块（items / fields 条目）。"""
    unknown = sorted(k for k in block if k not in allowed)
    if unknown:
        return f"{label} 未知约束字段：{', '.join(unknown)}"
    value_types = _parse_value_types(block.get("value_type"))
    if block.get("value_type") is not None and value_types is None:
        return f"{label} 的 value_type 必须是合法类型名或其非空数组"
    shape_err = _field_shape_error(block)
    if shape_err:
        return f"{label}：{shape_err}"
    return _field_type_compat_error(block, value_types or [])


def _fields_config_error(fields: Any, label: str) -> str | None:
    if not isinstance(fields, dict) or not fields:
        return f"{label} 的 fields 必须是非空对象"
    for key, prop in fields.items():
        if not isinstance(key, str) or not key:
            return f"{label} 的 fields 键必须是非空字符串"
        if not isinstance(prop, dict):
            return f"{label}.fields.{key} 必须是对象"
        err = _constraint_block_error(prop, _FIELD_PROP_KEYS, f"{label}.fields.{key}")
        if err:
            return err
    return None


def _items_config_error(items: Any, label: str, depth: int) -> str | None:
    if depth > _ITEMS_MAX_DEPTH:
        return f"{label} 嵌套 items 超过深度上限 {_ITEMS_MAX_DEPTH}"
    if not isinstance(items, dict):
        return f"{label} 必须是对象"
    err = _constraint_block_error(items, _ITEMS_KEYS, label)
    if err:
        return err
    value_types = _parse_value_types(items.get("value_type")) or []
    if "fields" in items:
        if value_types and "object" not in value_types:
            return f"{label} 含 fields 时 value_type 须包含 object"
        ferr = _fields_config_error(items.get("fields"), label)
        if ferr:
            return ferr
    if "items" in items:
        if value_types and "array" not in value_types:
            return f"{label} 含嵌套 items 时 value_type 须包含 array"
        return _items_config_error(items["items"], f"{label}.items", depth + 1)
    return None


def _field_config_error(check: dict[str, Any]) -> str | None:
    """校验 field 项配置；有错返回说明，否则 None。"""
    unknown = sorted(k for k in check if not k.startswith("_") and k not in _FIELD_KEYS)
    if unknown:
        return f"未知约束字段：{', '.join(unknown)}"
    path_err = _field_path_error(check.get("path"))
    if path_err:
        return path_err
    value_types = _parse_value_types(check.get("value_type"))
    if check.get("value_type") is not None and value_types is None:
        return "value_type 必须是合法类型名或其非空数组"
    shape_err = _field_shape_error(check)
    if shape_err:
        return shape_err
    compat = _field_type_compat_error(check, value_types or [])
    if compat:
        return compat
    if "items" in check:
        types = value_types or []
        if types and "array" not in types:
            return "含 items 时 value_type 须包含 array"
        return _items_config_error(check["items"], "items", 1)
    return None


def _resolve_path(structured: Any, path: str) -> tuple[str, Any | None]:
    """解析路径。返回 (kind, value)：
    ok — 取到末段值；skip — 前缀 null 或键缺失；fail — 前缀不可下降。
    """
    cursor: Any = structured
    segments = path.split(".")
    for i, seg in enumerate(segments):
        is_last = i == len(segments) - 1
        if cursor is None:
            return "skip", None
        if not isinstance(cursor, dict):
            return "fail", None
        if seg not in cursor:
            return ("ok", None) if is_last else ("skip", None)
        if is_last:
            return "ok", cursor[seg]
        cursor = cursor[seg]
        if cursor is None:
            return "skip", None
        if not isinstance(cursor, dict):
            return "fail", None
    return "fail", None


def _scalar_summary(value: Any) -> str:
    """短摘要，不回显长字符串全文。"""
    name = _json_type_name(value)
    if value is None or isinstance(value, bool):
        return name
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{name}={value}"
    if isinstance(value, str):
        return f"string 长度 {len(value)}"
    if isinstance(value, list):
        return f"array 长度 {len(value)}"
    if isinstance(value, dict):
        return f"object 键数 {len(value)}"
    return name


def _field_value_type_error(check: dict[str, Any], path: str, value: Any) -> ItemResult | None:
    """类型不符时返回失败项；通过则 None。"""
    value_types = _parse_value_types(check.get("value_type")) or []
    if not value_types or any(_matches_value_type(value, t) for t in value_types):
        return None
    return ItemResult(
        check["_id"], STATUS_FAIL,
        f"路径 {path} 类型不符：期望 {value_types}，实际 {_json_type_name(value)}",
        evidence=f"路径 {path}；{_scalar_summary(value)}",
    )


def _field_runtime_type_error(check: dict[str, Any], path: str, value: Any) -> ItemResult | None:
    """无/弱 value_type 时，约束与实际值类型不匹配 → 输入错误。"""
    cid = check["_id"]
    if any(k in check for k in ("min_length", "max_length", "pattern")) and not isinstance(value, str):
        return ItemResult(cid, STATUS_INPUT_ERROR, f"路径 {path} 的长度/模式约束仅适用于字符串")
    if any(k in check for k in ("minimum", "maximum")) and (
        isinstance(value, bool) or not isinstance(value, (int, float))
    ):
        return ItemResult(cid, STATUS_INPUT_ERROR, f"路径 {path} 的数值范围约束仅适用于数字")
    # 有 items 时非数组由 items 步骤记失败；仅长度约束时仍为输入错误
    if any(k in check for k in ("min_items", "max_items")) and not isinstance(value, list):
        if "items" in check:
            return None
        return ItemResult(cid, STATUS_INPUT_ERROR, f"路径 {path} 的数组长度约束仅适用于数组")
    return None


def _fail_path(cid: str, path: str, msg: str, value: Any) -> ItemResult:
    return ItemResult(cid, STATUS_FAIL, msg, evidence=f"路径 {path}；{_scalar_summary(value)}")


def _constrain_number(check: dict[str, Any], path: str, value: Any) -> ItemResult | None:
    cid = check["_id"]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if "minimum" in check and value < check["minimum"]:
        return _fail_path(cid, path, f"路径 {path} 小于 minimum={check['minimum']}", value)
    if "maximum" in check and value > check["maximum"]:
        return _fail_path(cid, path, f"路径 {path} 大于 maximum={check['maximum']}", value)
    return None


def _constrain_string(check: dict[str, Any], path: str, value: Any) -> ItemResult | None:
    cid = check["_id"]
    if not isinstance(value, str):
        return None
    n = len(value)  # Unicode 码点
    if "min_length" in check and n < check["min_length"]:
        return _fail_path(cid, path, f"路径 {path} 长度 {n} 小于 min_length={check['min_length']}", value)
    if "max_length" in check and n > check["max_length"]:
        return _fail_path(cid, path, f"路径 {path} 长度 {n} 大于 max_length={check['max_length']}", value)
    if "pattern" in check and re.search(check["pattern"], value) is None:
        return _fail_path(cid, path, f"路径 {path} 不匹配给定模式", value)
    return None


def _constrain_array(check: dict[str, Any], path: str, value: Any) -> ItemResult | None:
    cid = check["_id"]
    if not isinstance(value, list):
        return None
    n = len(value)
    if "min_items" in check and n < check["min_items"]:
        return _fail_path(cid, path, f"路径 {path} 数组长度 {n} 小于 min_items={check['min_items']}", value)
    if "max_items" in check and n > check["max_items"]:
        return _fail_path(cid, path, f"路径 {path} 数组长度 {n} 大于 max_items={check['max_items']}", value)
    return None


def _apply_scalar_constraints(check: dict[str, Any], path: str, value: Any) -> ItemResult | None:
    """标量/数组长度/枚举约束；通过返回 None，失败返回 ItemResult。"""
    for fn in (_constrain_number, _constrain_string, _constrain_array):
        hit = fn(check, path, value)
        if hit is not None:
            return hit
    if "enum" in check and value not in check["enum"]:
        return _fail_path(check["_id"], path, f"路径 {path} 不在枚举范围内", value)
    return None


def _typed_scalar_hit(cid: str, path: str, value: Any, constraints: dict[str, Any]) -> ItemResult | None:
    """类型 + 运行时类型 + 标量约束；通过返回 None。"""
    annotated = dict(constraints)
    annotated["_id"] = cid
    type_err = _field_value_type_error(annotated, path, value)
    if type_err:
        return type_err
    runtime_err = _field_runtime_type_error(annotated, path, value)
    if runtime_err:
        return runtime_err
    return _apply_scalar_constraints(annotated, path, value)


def _apply_fields_on_object(
    cid: str, path: str, obj: Any, fields: dict[str, Any],
) -> ItemResult | None:
    """对象元素的 fields；通过返回 None。"""
    if not isinstance(obj, dict):
        return ItemResult(
            cid, STATUS_FAIL,
            f"路径 {path} 期望 object 以核 fields，实际 {_json_type_name(obj)}",
            evidence=f"路径 {path}；{_scalar_summary(obj)}",
        )
    for key, prop in fields.items():
        child_path = f"{path}.{key}"
        if key not in obj:
            if bool(prop.get("optional")):
                continue
            return ItemResult(cid, STATUS_FAIL, f"缺少路径：{child_path}")
        hit = _typed_scalar_hit(cid, child_path, obj[key], prop)
        if hit is not None:
            return hit
    return None


def _apply_items(
    cid: str, path: str, value: Any, items: dict[str, Any],
) -> ItemResult | None:
    """数组元素约束；通过返回 None。空数组真空通过。"""
    if not isinstance(value, list):
        return ItemResult(
            cid, STATUS_FAIL,
            f"路径 {path} 声明了 items 但值不是数组（实际 {_json_type_name(value)}）",
            evidence=f"路径 {path}；{_scalar_summary(value)}",
        )
    for i, elem in enumerate(value):
        elem_path = f"{path}[{i}]"
        hit = _typed_scalar_hit(cid, elem_path, elem, items)
        if hit is not None:
            return hit
        if "fields" in items:
            ferr = _apply_fields_on_object(cid, elem_path, elem, items["fields"])
            if ferr is not None:
                return ferr
        if "items" in items:
            nested = _apply_items(cid, elem_path, elem, items["items"])
            if nested is not None:
                return nested
    return None


def _apply_field_constraints(check: dict[str, Any], path: str, value: Any) -> ItemResult:
    """对已定位的值施加标量/数组长度/枚举，以及可选的 items。"""
    hit = _apply_scalar_constraints(check, path, value)
    if hit is not None:
        return hit
    if "items" in check:
        items_hit = _apply_items(check["_id"], path, value, check["items"])
        if items_hit is not None:
            return items_hit
    return ItemResult(
        check["_id"], STATUS_PASS, f"路径 {path} 约束通过",
        evidence=f"路径 {path}；{_scalar_summary(value)}",
    )


def _locate_field_value(
    check: dict[str, Any], structured: dict[str, Any],
) -> ItemResult | tuple[str, Any]:
    """定位字段值；需提前返回时给出 ItemResult，否则 (path, value)。"""
    cid = check["_id"]
    path = check["path"].strip()
    kind, value = _resolve_path(structured, path)
    if kind == "skip":
        return ItemResult(cid, STATUS_SKIP, f"路径 {path} 的前缀为 null 或缺失，跳过")
    if kind == "fail":
        return ItemResult(cid, STATUS_FAIL, f"路径 {path} 的前缀不可下降为对象")
    optional = bool(check.get("optional"))
    if _leaf_missing(structured, path):
        if optional:
            return ItemResult(cid, STATUS_PASS, f"路径 {path} 可选且键缺失")
        return ItemResult(cid, STATUS_FAIL, f"缺少路径：{path}")
    if value is None and optional and "value_type" not in check:
        return ItemResult(cid, STATUS_PASS, f"路径 {path} 可选且为 null")
    return path, value


def _eval_field(check: dict[str, Any], structured: Any, provided: bool) -> ItemResult:
    cid = check["_id"]
    err = _field_config_error(check)
    if err:
        return ItemResult(cid, STATUS_INPUT_ERROR, err)
    if not provided:
        return ItemResult(cid, STATUS_UNKNOWN, "未提供结构化输出，无法判断字段约束")
    if not isinstance(structured, dict):
        return ItemResult(cid, STATUS_FAIL, "结构化输出不可解析为对象")
    located = _locate_field_value(check, structured)
    if isinstance(located, ItemResult):
        return located
    path, value = located
    type_err = _field_value_type_error(check, path, value)
    if type_err:
        return type_err
    runtime_err = _field_runtime_type_error(check, path, value)
    if runtime_err:
        return runtime_err
    return _apply_field_constraints(check, path, value)


def _leaf_missing(structured: Any, path: str) -> bool:
    """末段键是否不存在（显式 null 不算缺失）。"""
    cursor: Any = structured
    segments = path.split(".")
    for i, seg in enumerate(segments):
        if not isinstance(cursor, dict):
            return False
        if seg not in cursor:
            return i == len(segments) - 1
        cursor = cursor[seg]
    return False


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
    if ctype == CHECK_FIELD:
        return _eval_field(check, structured, struct_ok)
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
