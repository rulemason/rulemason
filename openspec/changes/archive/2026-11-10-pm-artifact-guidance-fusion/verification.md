# Verification — pm-artifact-guidance-fusion

基线：`main` @ `71564ca`（0.8.34）。实现分支：`cursor/pm-artifact-guidance-impl-aa93`。实现提交：`5258e72`。
发版准备目标：**0.8.35**（fetch + PyPI 核实当时最新 0.8.34 / `v0.8.34`，未占用）。
归档：`openspec/changes/archive/2026-11-10-pm-artifact-guidance-fusion/`（主规格已同步）。

## 已实现功能（真实）

- 自研 `rules/product-artifact-caution.md` 经 `init`/`update` 必复制；入口引用；不进默认判断红线。
- `must_contain`/`pattern` 可选 `severity`（缺省 `strict`）；`--preset product-artifact.hint|strict`；`--preset hint|strict` 仍为 prose-hygiene。
- 种子首次写入、幂等不覆盖；`remove` 删除；wheel/sdist 含规则与预设。

## 限制（如实）

- 结构标题存在 ≠ 实质质量 / 指标已达成。
- 不剥代码围栏（围栏内假标题可误报通过，测试锁定）。
- 无 LLM/静态分析工具 运行时；init/update 不扫仓、不检查文档。
- 限制性许可证 来源未再分发正文。

## 发版准备校验（本次实测）

| 项 | 结果 |
|---|---|
| `uv run ruff check .` | 通过 |
| `uv run pytest` | **743 passed** |
| `openspec validate --specs --strict` | 14 passed |
| `openspec validate --all --strict` | 14 passed（归档后无 active change） |
| `openspec validate --archived --strict` | 39 passed（含本归档） |
| `uv build` → `rulemason-0.8.35` wheel/sdist | 含 `product-artifact-caution.md` 与预设 JSON |
| 干净 venv 安装 wheel | init 分发 + 种子幂等不覆盖；hint exit0 / strict exit1；`--preset hint` 仍 prose；旧 must_contain fail=1；非法 severity=2 |
| `rulemason check`（本仓库） | 各层齐全；提示 verification 需写到审查（下节已记） |
| 付费 Jev / 判断回归 | **未跑** |

## 审查

实现阶段做过独立只读审查：requirements/correctness/security/quality/tests 为 pass；采纳空白行与 must_contain hint 单测补强。围栏假标题误报为已文档化边界，未当缺陷改。

## 计划差异

- 结构预设 id 为 `product-artifact.*`，不偷换 `--preset hint|strict`。
- 验收同义词：`验收(?:标准)?`。
- 本阶段：归档 + 0.8.35 bump + PR；**不合并不打 tag 不直传 PyPI**。

## 产物

- `artifacts/before-after.md`、`configs-and-limits.md`、`cli-samples.txt`、`full.patch`
