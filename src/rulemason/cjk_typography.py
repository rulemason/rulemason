"""中文混排排版的确定性检测：预处理剥离易误伤片段后，按可开关短名规则检查。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

RULE_FULLWIDTH_DIGIT = "fullwidth_digit"
RULE_STACKED_PUNCT = "stacked_punct"
RULE_CJK_LATIN_SPACE = "cjk_latin_space"
RULE_CJK_DIGIT_SPACE = "cjk_digit_space"
RULE_UNIT_SPACE = "unit_space"
RULE_DEGREE_PERCENT_NOSPACE = "degree_percent_nospace"
RULE_FW_PUNCT_SPACE = "fw_punct_space"
RULE_HALFWIDTH_PUNCT_CJK = "halfwidth_punct_cjk"
RULE_FULLWIDTH_ALPHA = "fullwidth_alpha"
RULE_IDEOGRAPHIC_SPACE = "ideographic_space"

KNOWN_RULES = frozenset({
    RULE_FULLWIDTH_DIGIT,
    RULE_STACKED_PUNCT,
    RULE_CJK_LATIN_SPACE,
    RULE_CJK_DIGIT_SPACE,
    RULE_UNIT_SPACE,
    RULE_DEGREE_PERCENT_NOSPACE,
    RULE_FW_PUNCT_SPACE,
    RULE_HALFWIDTH_PUNCT_CJK,
    RULE_FULLWIDTH_ALPHA,
    RULE_IDEOGRAPHIC_SPACE,
})

DEFAULT_UNITS = ("GB", "TB", "Gbps", "MB", "KB", "ms", "px")
DEFAULT_MAX_HITS = 50

_ALLOWED_INTERROBANG = frozenset({"？！", "?!", "！？", "!?"})
# 基本区 + 扩展 A + 兼容区
_CJK = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
_LATIN = r"A-Za-z"
_DIGIT = r"0-9"
_FW_DIGIT = r"\uff10-\uff19"
_FW_ALPHA = r"\uff21-\uff3a\uff41-\uff5a"
_HALFWIDTH_PUNCT = r",;:!?"
_FW_PUNCT = (
    "，。！？；：、"
    "（）【】《》「」『』"
    "\u201c\u201d\u2018\u2019"
)
_STACK_CHARS = set("!?！？")

_CONFIG_KEYS = frozenset({
    "id", "type", "rules", "units", "allowlist", "path", "max_hits",
})

_MASK = "\ue000"

_DIRECTIVE_RE = re.compile(
    r"<!--\s*(rulemason-(?:disable|enable))\s*([^>]*?)-->",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Hit:
    rule: str
    offset: int
    length: int


def _rules_error(rules: Any) -> str | None:
    if not isinstance(rules, list) or not rules or any(not isinstance(r, str) or not r for r in rules):
        return "rules 必须是非空字符串数组"
    bad = sorted({r for r in rules if r not in KNOWN_RULES})
    return f"未知规则短名：{', '.join(bad)}" if bad else None


def _allowlist_error(allow: Any) -> str | None:
    if not isinstance(allow, list):
        return "allowlist 必须是字符串数组"
    if any(not isinstance(a, str) or not a for a in allow):
        return "allowlist 项必须是非空字符串"
    return None


def config_error(check: dict[str, Any]) -> str | None:
    """校验 cjk_typography 配置；有错返回说明。"""
    unknown = sorted(k for k in check if not k.startswith("_") and k not in _CONFIG_KEYS)
    if unknown:
        return f"未知约束字段：{', '.join(unknown)}"
    if err := _rules_error(check.get("rules")):
        return err
    if "units" in check:
        units = check["units"]
        if not isinstance(units, list) or any(not isinstance(u, str) or not u for u in units):
            return "units 必须是非空字符串组成的数组"
    if "allowlist" in check and (err := _allowlist_error(check["allowlist"])):
        return err
    if "path" in check and check["path"] is not None:
        path = check["path"]
        if not isinstance(path, str) or not path.strip():
            return "path 必须是非空字符串"
    if "max_hits" in check:
        mh = check["max_hits"]
        if not isinstance(mh, int) or isinstance(mh, bool) or mh < 1:
            return "max_hits 必须是正整数"
    return None


def _mask_span(chars: list[str], start: int, end: int) -> None:
    for i in range(start, end):
        chars[i] = _MASK


def _mask_regex(chars: list[str], text: str, pattern: re.Pattern[str], group: int = 0) -> None:
    for m in pattern.finditer(text):
        _mask_span(chars, m.start(group), m.end(group))


def _mask_indented_code(chars: list[str], text: str) -> None:
    """CommonMark：文首或空行后，连续缩进（≥4 空格或 tab）行构成代码块。"""
    lines = text.splitlines(keepends=True)
    offset = 0
    prev_blank = True  # 文首视为块边界
    i = 0
    while i < len(lines):
        line = lines[i]
        is_blank = line.strip() == ""
        indented = bool(re.match(r"^(?: {4}|\t)", line))
        if prev_blank and indented:
            start = offset
            j = i
            end = offset
            while j < len(lines):
                lj = lines[j]
                if re.match(r"^(?: {4}|\t)", lj):
                    end += len(lj)
                    j += 1
                    continue
                if lj.strip() == "":
                    # 前瞻：其后还有缩进行则纳入，否则结束
                    k = j + 1
                    while k < len(lines) and lines[k].strip() == "":
                        k += 1
                    if k < len(lines) and re.match(r"^(?: {4}|\t)", lines[k]):
                        end += len(lj)
                        j += 1
                        continue
                    break
                break
            _mask_span(chars, start, end)
            for t in range(i, j):
                offset += len(lines[t])
            i = j
            prev_blank = True
            continue
        offset += len(line)
        prev_blank = is_blank
        i += 1


def preprocess(text: str) -> str:
    """按固定顺序把易误伤片段替换为占位，保持码点长度与偏移。"""
    chars = list(text)
    _mask_regex(chars, text, re.compile(r"```[\s\S]*?```"))
    _mask_regex(chars, text, re.compile(r"~~~[\s\S]*?~~~"))
    _mask_indented_code(chars, text)
    _mask_regex(chars, text, re.compile(r"`[^`\n]+`"))
    _mask_regex(chars, text, re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)"), group=1)
    _mask_regex(chars, text, re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)"), group=1)
    _mask_regex(chars, text, re.compile(r"^\[[^\]]+\]:\s*\S+", re.M))
    _mask_regex(chars, text, re.compile(r"https?://[^\s<>\])\"']+"))
    _mask_regex(chars, text, re.compile(r"<https?://[^>\s]+>"))
    _mask_regex(chars, text, re.compile(r"</?[A-Za-z][^>\n]*>"))
    return "".join(chars)


def _parse_rule_names(raw: str) -> list[str] | str:
    """解析逗号分隔短名；返回列表，或错误说明字符串。"""
    parts = [p.strip() for p in raw.replace("，", ",").split(",")]
    names = [p for p in parts if p]
    if not names:
        return []
    bad = sorted({n for n in names if n not in KNOWN_RULES})
    if bad:
        return f"未知规则短名：{', '.join(bad)}"
    return names


def directive_error(text: str, masked: str | None = None) -> str | None:
    """正文内关闭注释若含未知短名则返回说明。代码块内注释忽略。"""
    masked = masked if masked is not None else preprocess(text)
    for m in _DIRECTIVE_RE.finditer(text):
        if masked[m.start()] == _MASK:
            continue
        rest = m.group(2).strip()
        if not rest:
            continue
        parsed = _parse_rule_names(rest)
        if isinstance(parsed, str):
            return parsed
    return None


def _directive_events(
    text: str, masked: str,
) -> list[tuple[int, int, str, frozenset[str] | None]]:
    events: list[tuple[int, int, str, frozenset[str] | None]] = []
    for m in _DIRECTIVE_RE.finditer(text):
        if masked[m.start()] == _MASK:
            continue
        kind = m.group(1).lower()
        rest = m.group(2).strip()
        if not rest:
            rules: frozenset[str] | None = None
        else:
            parsed = _parse_rule_names(rest)
            if isinstance(parsed, str):
                continue
            rules = frozenset(parsed)
        events.append((m.start(), m.end(), kind, rules))
    events.sort(key=lambda e: e[0])
    return events


def _apply_directive(disabled: set[str], kind: str, rules: frozenset[str] | None, enabled: frozenset[str]) -> None:
    if kind.endswith("disable"):
        if rules is None:
            disabled |= set(enabled)
        else:
            disabled |= set(rules) & enabled
        return
    if rules is None:
        disabled.clear()
    else:
        disabled -= set(rules)


def _disabled_intervals(
    text: str, masked: str, enabled_rules: list[str],
) -> list[tuple[int, int, frozenset[str]]]:
    """返回 (start, end, disabled_rules) 区间；disabled_rules 为当时关闭的短名集合。"""
    intervals: list[tuple[int, int, frozenset[str]]] = []
    disabled: set[str] = set()
    cursor = 0
    enabled_set = frozenset(enabled_rules)
    for start, end, kind, rules in _directive_events(text, masked):
        if start > cursor and disabled:
            intervals.append((cursor, start, frozenset(disabled)))
        _apply_directive(disabled, kind, rules, enabled_set)
        cursor = end
    if len(text) > cursor and disabled:
        intervals.append((cursor, len(text), frozenset(disabled)))
    return intervals


def _hits_fullwidth_digit(text: str) -> list[Hit]:
    return [Hit(RULE_FULLWIDTH_DIGIT, m.start(), 1) for m in re.finditer(f"[{_FW_DIGIT}]", text)]


def _hits_stacked_punct(text: str) -> list[Hit]:
    hits: list[Hit] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] not in _STACK_CHARS:
            i += 1
            continue
        j = i + 1
        while j < n and text[j] in _STACK_CHARS:
            j += 1
        run = text[i:j]
        if len(run) >= 2 and run not in _ALLOWED_INTERROBANG:
            hits.append(Hit(RULE_STACKED_PUNCT, i, j - i))
        i = j
    return hits


def _hits_cjk_latin(text: str) -> list[Hit]:
    return [
        Hit(RULE_CJK_LATIN_SPACE, m.start(), m.end() - m.start())
        for m in re.finditer(f"[{_CJK}][{_LATIN}]|[{_LATIN}][{_CJK}]", text)
    ]


def _hits_cjk_digit(text: str) -> list[Hit]:
    return [
        Hit(RULE_CJK_DIGIT_SPACE, m.start(), m.end() - m.start())
        for m in re.finditer(f"[{_CJK}][{_DIGIT}]|[{_DIGIT}][{_CJK}]", text)
    ]


def _hits_unit_space(text: str, units: list[str]) -> list[Hit]:
    if not units:
        return []
    ordered = sorted({u for u in units if u}, key=len, reverse=True)
    hits: list[Hit] = []
    for unit in ordered:
        pat = re.compile(rf"(?<![A-Za-z0-9])(\d+)({re.escape(unit)})(?![A-Za-z0-9])")
        for m in pat.finditer(text):
            hits.append(Hit(RULE_UNIT_SPACE, m.start(), m.end() - m.start()))
    return hits


def _hits_degree_percent(text: str) -> list[Hit]:
    return [
        Hit(RULE_DEGREE_PERCENT_NOSPACE, m.start(), m.end() - m.start())
        for m in re.finditer(r"\d[ \t]+[°%]", text)
    ]


def _space_other_side_exception(text: str, space_i: int) -> bool:
    """空格另一侧为 URL 占位、强调 *、或表格 | 时豁免。"""
    left = text[space_i - 1] if space_i > 0 else ""
    right = text[space_i + 1] if space_i + 1 < len(text) else ""
    for other in (left, right):
        if other == _MASK or other == "|" or other == "*":
            return True
    return False


def _hits_fw_punct_space(text: str) -> list[Hit]:
    hits: list[Hit] = []
    fw = re.escape(_FW_PUNCT)
    for m in re.finditer(rf"[ \t][{fw}]|[{fw}][ \t]", text):
        frag = text[m.start(): m.end()]
        space_i = m.start() if frag[0] in " \t" else m.start() + 1
        if _space_other_side_exception(text, space_i):
            continue
        hits.append(Hit(RULE_FW_PUNCT_SPACE, m.start(), m.end() - m.start()))
    return hits


def _hits_halfwidth_punct_cjk(text: str) -> list[Hit]:
    return [
        Hit(RULE_HALFWIDTH_PUNCT_CJK, m.start(), m.end() - m.start())
        for m in re.finditer(f"[{_CJK}][{_HALFWIDTH_PUNCT}][{_CJK}]", text)
    ]


def _hits_fullwidth_alpha(text: str) -> list[Hit]:
    return [Hit(RULE_FULLWIDTH_ALPHA, m.start(), 1) for m in re.finditer(f"[{_FW_ALPHA}]", text)]


def _hits_ideographic_space(text: str) -> list[Hit]:
    return [Hit(RULE_IDEOGRAPHIC_SPACE, m.start(), 1) for m in re.finditer("\u3000", text)]


_RULE_FNS = {
    RULE_FULLWIDTH_DIGIT: lambda t, _u: _hits_fullwidth_digit(t),
    RULE_STACKED_PUNCT: lambda t, _u: _hits_stacked_punct(t),
    RULE_CJK_LATIN_SPACE: lambda t, _u: _hits_cjk_latin(t),
    RULE_CJK_DIGIT_SPACE: lambda t, _u: _hits_cjk_digit(t),
    RULE_UNIT_SPACE: _hits_unit_space,
    RULE_DEGREE_PERCENT_NOSPACE: lambda t, _u: _hits_degree_percent(t),
    RULE_FW_PUNCT_SPACE: lambda t, _u: _hits_fw_punct_space(t),
    RULE_HALFWIDTH_PUNCT_CJK: lambda t, _u: _hits_halfwidth_punct_cjk(t),
    RULE_FULLWIDTH_ALPHA: lambda t, _u: _hits_fullwidth_alpha(t),
    RULE_IDEOGRAPHIC_SPACE: lambda t, _u: _hits_ideographic_space(t),
}


def _apply_allowlist(hits: list[Hit], original: str, allowlist: list[str]) -> list[Hit]:
    if not allowlist:
        return hits
    spans: list[tuple[int, int]] = []
    for item in allowlist:
        start = 0
        while True:
            idx = original.find(item, start)
            if idx < 0:
                break
            spans.append((idx, idx + len(item)))
            start = idx + 1
    kept: list[Hit] = []
    for hit in hits:
        frag = original[hit.offset: hit.offset + hit.length]
        if frag in allowlist:
            continue
        hit_end = hit.offset + hit.length
        if any(hit.offset < end and start < hit_end for start, end in spans):
            continue
        kept.append(hit)
    return kept


def _filter_disabled(
    hits: list[Hit], intervals: list[tuple[int, int, frozenset[str]]],
) -> list[Hit]:
    if not intervals:
        return hits
    kept: list[Hit] = []
    for hit in hits:
        disabled = False
        for start, end, rules in intervals:
            if start <= hit.offset < end and hit.rule in rules:
                disabled = True
                break
        if not disabled:
            kept.append(hit)
    return kept


def offset_to_line_col(text: str, offset: int) -> tuple[int, int]:
    """原文码点偏移 → 1-based 行号与列号。"""
    if offset < 0:
        offset = 0
    if offset > len(text):
        offset = len(text)
    line = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    col = offset - last_nl
    return line, col


def find_hits(
    text: str,
    rules: list[str],
    *,
    units: list[str] | None = None,
    allowlist: list[str] | None = None,
) -> list[Hit]:
    """对正文跑选定规则；返回按偏移排序的命中（已套用关闭注释与 allowlist）。"""
    masked = preprocess(text)
    unit_list = list(units) if units is not None else list(DEFAULT_UNITS)
    hits: list[Hit] = []
    for rule in rules:
        fn = _RULE_FNS.get(rule)
        if fn is None:
            continue
        hits.extend(fn(masked, unit_list))
    hits.sort(key=lambda h: (h.offset, h.rule))
    intervals = _disabled_intervals(text, masked, rules)
    hits = _filter_disabled(hits, intervals)
    return _apply_allowlist(hits, text, list(allowlist or []))
