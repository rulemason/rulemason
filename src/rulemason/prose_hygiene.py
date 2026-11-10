"""面向人读文案的确定性卫生检查（显式短名；非作者判别）。

短语与结构模式由本仓库自研。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rulemason import cjk_typography as _cjk

RULE_EM_DASH = "em_dash"
RULE_CHATBOT_CLOSER = "chatbot_closer"
RULE_SIGNPOST_OPENER = "signpost_opener"
RULE_NOT_JUST_CONTRAST = "not_just_contrast"

KNOWN_RULES = frozenset({
    RULE_EM_DASH,
    RULE_CHATBOT_CLOSER,
    RULE_SIGNPOST_OPENER,
    RULE_NOT_JUST_CONTRAST,
})

# 开箱推荐（不含 em_dash）；预设与文档默认用此列表
RECOMMENDED_RULES = (
    RULE_CHATBOT_CLOSER,
    RULE_SIGNPOST_OPENER,
    RULE_NOT_JUST_CONTRAST,
)

SEVERITY_HINT = "hint"
SEVERITY_STRICT = "strict"
KNOWN_SEVERITIES = frozenset({SEVERITY_HINT, SEVERITY_STRICT})
DEFAULT_SEVERITY = SEVERITY_HINT

DEFAULT_MAX_HITS = 50

# 自研短短语（英文大小写不敏感；中文原样）。非第三方词表拷贝。
_CHATBOT_PHRASES = (
    "i hope this helps",
    "let me know if you have any questions",
    "let me know if you'd like",
    "would you like me to",
    "you're welcome!",
    "希望对你有帮助",
    "如有疑问请随时",
    "还有什么我可以帮",
)

_SIGNPOST_PHRASES = (
    "let's dive in",
    "here's what you need to know",
    "in this article we'll",
    "without further ado",
    "in today's fast-paced",
    "让我们深入了解",
    "本文将探讨",
    "在当今快节奏",
)

_NOT_JUST_PATTERNS = (
    re.compile(r"(?is)\bnot\s+just\b.{0,80}?\bbut\b"),
    re.compile(r"(?is)\bnot\s+only\b.{0,80}?\bbut\s+(?:also\b)?"),
    re.compile(r"不只是.{0,40}?[更也]是"),
    re.compile(r"不仅仅是.{0,40}?[更也]是"),
)

_CONFIG_KEYS = frozenset({
    "id", "type", "rules", "allowlist", "path", "max_hits", "severity",
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
    """校验 prose_hygiene 配置；有错返回说明。"""
    unknown = sorted(k for k in check if not k.startswith("_") and k not in _CONFIG_KEYS)
    if unknown:
        return f"未知约束字段：{', '.join(unknown)}"
    if err := _rules_error(check.get("rules")):
        return err
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
    if "severity" in check:
        sev = check["severity"]
        if not isinstance(sev, str) or sev not in KNOWN_SEVERITIES:
            return "severity 必须是 hint 或 strict"
    return None


def preprocess(text: str) -> str:
    """复用中文排版同一套 Markdown/URL 占位，保持偏移。"""
    return _cjk.preprocess(text)


def _parse_rule_names(raw: str) -> list[str] | str:
    parts = [p.strip() for p in raw.replace("，", ",").split(",")]
    names = [p for p in parts if p]
    if not names:
        return []
    bad = sorted({n for n in names if n not in KNOWN_RULES})
    if bad:
        return f"未知规则短名：{', '.join(bad)}"
    return names


def directive_error(text: str, masked: str | None = None) -> str | None:
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


def _filter_disabled(hits: list[Hit], intervals: list[tuple[int, int, frozenset[str]]]) -> list[Hit]:
    out: list[Hit] = []
    for h in hits:
        skip = False
        for start, end, rules in intervals:
            if start <= h.offset < end and h.rule in rules:
                skip = True
                break
        if not skip:
            out.append(h)
    return out


def _apply_allowlist(hits: list[Hit], text: str, allowlist: list[str]) -> list[Hit]:
    if not allowlist:
        return hits
    spans: list[tuple[int, int]] = []
    for item in allowlist:
        start = 0
        while True:
            idx = text.find(item, start)
            if idx < 0:
                break
            spans.append((idx, idx + len(item)))
            start = idx + 1
    kept: list[Hit] = []
    for hit in hits:
        frag = text[hit.offset: hit.offset + hit.length]
        if frag in allowlist:
            continue
        hit_end = hit.offset + hit.length
        if any(hit.offset < end and start < hit_end for start, end in spans):
            continue
        kept.append(hit)
    return kept


def _hits_em_dash(masked: str) -> list[Hit]:
    hits = [Hit(RULE_EM_DASH, m.start(), 1) for m in re.finditer("\u2014", masked)]
    for m in re.finditer(r" -- ", masked):
        hits.append(Hit(RULE_EM_DASH, m.start(), 4))
    return hits


def _phrase_hits(masked: str, phrases: tuple[str, ...], rule: str) -> list[Hit]:
    hits: list[Hit] = []
    lower = masked.lower()
    for phrase in phrases:
        if any("\u4e00" <= ch <= "\u9fff" for ch in phrase):
            hay, needle = masked, phrase
        else:
            hay, needle = lower, phrase.lower()
        start = 0
        while True:
            i = hay.find(needle, start)
            if i < 0:
                break
            # 跳过占位区
            if masked[i] != _MASK:
                hits.append(Hit(rule, i, len(phrase)))
            start = i + max(len(needle), 1)
    return hits


def _hits_not_just(masked: str) -> list[Hit]:
    hits: list[Hit] = []
    for pat in _NOT_JUST_PATTERNS:
        for m in pat.finditer(masked):
            if masked[m.start()] == _MASK:
                continue
            hits.append(Hit(RULE_NOT_JUST_CONTRAST, m.start(), m.end() - m.start()))
    return hits


_RULE_FNS = {
    RULE_EM_DASH: _hits_em_dash,
    RULE_CHATBOT_CLOSER: lambda t: _phrase_hits(t, _CHATBOT_PHRASES, RULE_CHATBOT_CLOSER),
    RULE_SIGNPOST_OPENER: lambda t: _phrase_hits(t, _SIGNPOST_PHRASES, RULE_SIGNPOST_OPENER),
    RULE_NOT_JUST_CONTRAST: _hits_not_just,
}


def find_hits(
    text: str,
    rules: list[str],
    *,
    allowlist: list[str] | None = None,
) -> list[Hit]:
    """对正文跑选定规则；返回按偏移排序的命中。"""
    masked = preprocess(text)
    hits: list[Hit] = []
    seen_rules: list[str] = []
    for rule in rules:
        if rule in seen_rules:
            continue
        seen_rules.append(rule)
        fn = _RULE_FNS.get(rule)
        if fn is None:
            continue
        hits.extend(fn(masked))
    hits.sort(key=lambda h: (h.offset, h.rule))
    intervals = _disabled_intervals(text, masked, seen_rules)
    hits = _filter_disabled(hits, intervals)
    return _apply_allowlist(hits, text, list(allowlist or []))


offset_to_line_col = _cjk.offset_to_line_col
