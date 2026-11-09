"""本仓 CI：对 README.md 与 rules/**/*.md 跑 cjk_typography（经现有 pytest test job）。"""
from __future__ import annotations

from pathlib import Path

import pytest

from rulemason import cjk_typography as cjk
from rulemason.result_check import EXIT_OK, STATUS_FAIL, run_check

ROOT = Path(__file__).resolve().parents[1]
ALL_RULES = sorted(cjk.KNOWN_RULES)


def _targets() -> list[Path]:
    files = [ROOT / "README.md"]
    files.extend(sorted((ROOT / "rules").rglob("*.md")))
    return files


def _requirements() -> dict:
    # allowlist 初始为空：不写该键
    return {
        "schema": 1,
        "checks": [{"id": "zh", "type": "cjk_typography", "rules": ALL_RULES}],
    }


@pytest.mark.parametrize("path", _targets(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_repo_markdown_cjk_typography(path: Path):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    report = run_check(
        {"text": text, "source": {"kind": "fixture", "id": rel}},
        _requirements(),
    )
    if report.exit_code != EXIT_OK:
        item = report.items[0]
        assert item.status == STATUS_FAIL
        pytest.fail(f"{rel}: {item.explanation}")


def test_ci_targets_exclude_english_readme_and_archives():
    rels = {p.relative_to(ROOT).as_posix() for p in _targets()}
    assert "README.md" in rels
    assert any(r.startswith("rules/") for r in rels)
    assert "README.en.md" not in rels
    assert not any("openspec/" in r for r in rels)
    assert "allowlist" not in _requirements()["checks"][0]
