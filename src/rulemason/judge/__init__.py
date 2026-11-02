"""Jev 判断引擎的库接口：名称与各项目原先 judge.py 一致，项目只需改 import 一行。"""
from rulemason.judge.judge import (
    JEV_MODEL,
    SHORT_LABEL,
    Judge,
    Rule,
    change_files,
    enforces_exists,
    label_len,
    lexicon,
    lint_copy,
    lint_design,
    load_rules,
    pick_provider,
    verdict,
    verdict_or_pending,
)

__all__ = [
    "JEV_MODEL",
    "SHORT_LABEL",
    "Judge",
    "Rule",
    "change_files",
    "enforces_exists",
    "label_len",
    "lexicon",
    "lint_copy",
    "lint_design",
    "load_rules",
    "pick_provider",
    "verdict",
    "verdict_or_pending",
]
