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

KNOWN_RULES = frozenset({
    RULE_FULLWIDTH_DIGIT,
    RULE_STACKED_PUNCT,
    RULE_CJK_LATIN_SPACE,
    RULE_CJK_DIGIT_SPACE,
    RULE_UNIT_SPACE,
    RULE_DEGREE_PERCENT_NOSPACE,
    RULE_FW_PUNCT_SPACE,
})

DEFAULT_UNITS = ("GB", "TB", "Gbps", "MB", "KB", "ms", "px")

_ALLOWED_INTERROBANG = frozenset({"？！", "?!", "！？", "!?"})
_CJK = r"\u4e00-\u9fff"
_LATIN = r"A-Za-z"
_DIGIT = r"0-9"
_FW_DIGIT = r"\uff10-\uff19"
# 常见全角标点（不含全角数字）
_FW_PUNCT = (
    "，。！？；：、"
    "（）【】《》「」『』"
    "\u201c\u201d\u2018\u2019"  # “”‘’
)
_STACK_CHARS = set("!?！？")

_CONFIG_KEYS = frozenset({"id", "type", "rules", "units", "allowlist", "path"})


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
    return None


# 占位符须不是空白、汉字、拉丁、数字或全角标点，避免剥离本身诱发规则命中
_MASK = "\ue000"


def _mask_span(chars: list[str], start: int, end: int) -> None:
    for i in range(start, end):
        chars[i] = _MASK


def _mask_regex(chars: list[str], text: str, pattern: re.Pattern[str], group: int = 0) -> None:
    for m in pattern.finditer(text):
        _mask_span(chars, m.start(group), m.end(group))


def preprocess(text: str) -> str:
    """按固定顺序把易误伤片段替换为空格，保持码点长度与偏移。"""
    chars = list(text)
    # 1) 围栏代码块
    _mask_regex(chars, text, re.compile(r"```[\s\S]*?```"))
    # 2) 行内代码
    _mask_regex(chars, text, re.compile(r"`[^`\n]+`"))
    # 3) Markdown 图片/链接目标（保留可见文案）
    # ![alt](url) / [text](url) — 只遮 url
    _mask_regex(chars, text, re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)"), group=1)
    _mask_regex(chars, text, re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)"), group=1)
    # 4) 裸 URL
    _mask_regex(chars, text, re.compile(r"https?://[^\s<>\])\"']+"))
    # 5) 行内 HTML 标签
    _mask_regex(chars, text, re.compile(r"</?[A-Za-z][^>\n]*>"))
    return "".join(chars)


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
    hits: list[Hit] = []
    for m in re.finditer(f"[{_CJK}][{_LATIN}]|[{_LATIN}][{_CJK}]", text):
        hits.append(Hit(RULE_CJK_LATIN_SPACE, m.start(), m.end() - m.start()))
    return hits


def _hits_cjk_digit(text: str) -> list[Hit]:
    hits: list[Hit] = []
    for m in re.finditer(f"[{_CJK}][{_DIGIT}]|[{_DIGIT}][{_CJK}]", text):
        hits.append(Hit(RULE_CJK_DIGIT_SPACE, m.start(), m.end() - m.start()))
    return hits


def _hits_unit_space(text: str, units: list[str]) -> list[Hit]:
    if not units:
        return []
    ordered = sorted({u for u in units if u}, key=len, reverse=True)
    hits: list[Hit] = []
    for unit in ordered:
        pat = re.compile(rf"(?<![A-Za-z0-9])(\d+)({re.escape(unit)})(?![A-Za-z0-9])")
        for m in pat.finditer(text):
            # 数字与单位相邻（中间无空白）——模式本身要求紧贴
            hits.append(Hit(RULE_UNIT_SPACE, m.start(), m.end() - m.start()))
    return hits


def _hits_degree_percent(text: str) -> list[Hit]:
    return [
        Hit(RULE_DEGREE_PERCENT_NOSPACE, m.start(), m.end() - m.start())
        for m in re.finditer(r"\d[ \t]+[°%]", text)
    ]


def _hits_fw_punct_space(text: str) -> list[Hit]:
    hits: list[Hit] = []
    fw = re.escape(_FW_PUNCT)
    for m in re.finditer(rf"[ \t][{fw}]|[{fw}][ \t]", text):
        hits.append(Hit(RULE_FW_PUNCT_SPACE, m.start(), m.end() - m.start()))
    return hits


_RULE_FNS = {
    RULE_FULLWIDTH_DIGIT: lambda t, _u: _hits_fullwidth_digit(t),
    RULE_STACKED_PUNCT: lambda t, _u: _hits_stacked_punct(t),
    RULE_CJK_LATIN_SPACE: lambda t, _u: _hits_cjk_latin(t),
    RULE_CJK_DIGIT_SPACE: lambda t, _u: _hits_cjk_digit(t),
    RULE_UNIT_SPACE: _hits_unit_space,
    RULE_DEGREE_PERCENT_NOSPACE: lambda t, _u: _hits_degree_percent(t),
    RULE_FW_PUNCT_SPACE: lambda t, _u: _hits_fw_punct_space(t),
}


def _apply_allowlist(hits: list[Hit], original: str, allowlist: list[str]) -> list[Hit]:
    if not allowlist:
        return hits
    # 预计算每个 allowlist 项的所有出现区间 [start, end)
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
        # 命中与白名单出现区间有任何重叠则豁免（品牌串边界上的中英相邻）
        hit_end = hit.offset + hit.length
        if any(hit.offset < end and start < hit_end for start, end in spans):
            continue
        kept.append(hit)
    return kept


def find_hits(
    text: str,
    rules: list[str],
    *,
    units: list[str] | None = None,
    allowlist: list[str] | None = None,
) -> list[Hit]:
    """对正文跑选定规则；返回按偏移排序的命中（已套用 allowlist）。"""
    masked = preprocess(text)
    unit_list = list(units) if units is not None else list(DEFAULT_UNITS)
    hits: list[Hit] = []
    for rule in rules:
        fn = _RULE_FNS.get(rule)
        if fn is None:
            continue
        hits.extend(fn(masked, unit_list))
    hits.sort(key=lambda h: (h.offset, h.rule))
    return _apply_allowlist(hits, text, list(allowlist or []))
