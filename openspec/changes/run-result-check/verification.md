# verification：run-result-check（apply 后）

## 命令用法（已实现）

```bash
rulemason result-check --record <记录.json> --requirements <要求.json>
rulemason result-check --json --record <记录.json> --requirements <要求.json>
rulemason result-check --help
```

退出码：`0` 总体通过；`1` 失败或无法判断；`2` 输入错误。`--json` 写 stdout（自有 `schema: 1`），不改 `check --json`。

## 任务勾选依据

| 任务 | 验证 | 结果 |
|---|---|---|
| 1.1–1.5 | `uv run pytest tests/test_result_check.py` | 通过（含空要求、文本四态、结构化、Skill→2、不回显全文） |
| 2.1–2.2 | 同上 CLI 用例 + `result-check --help` / `check --json` schema=1 | 通过 |
| 3.1–3.2 | fixture `tests/fixtures/result_check/` + 帮助关键字 | 通过 |
| 4.1 | `uv run pytest -q --tb=line` | **664 passed in 17.56s**（`/tmp/pytest-full3.log`） |
| 4.2 | 本文件；判断 / ruff / 精简 / 独立审查 | 见下 |

此前曾有一次全量卡住：日志停在 ~32%，子进程 `git commit` → `/exec-daemon/ssh-keygen -Y sign` 假死（本机 `commit.gpgsign=true`）。**不是实现逻辑在推进。** 已杀掉该进程；在 `tests/conftest.py` 与 `tests/judge/test_engine.py` 的测试提交加 `-c commit.gpgsign=false` 后全量一次跑完。更早一次定向 **19 passed** 仅覆盖 result-check 相关，**不等于**全绿。

## Workflow gates

1. **自动精简**：去掉无意义注释；抽出 `_text_needles`；`_excerpt` 按规格改为「定位优先、摘录须严格短于全文」；未做行为改变的性能改写。
2. **独立审查**：材料 `/tmp/review-run-result-check/package.md`；第 1 轮 overall `needs_fix`（损坏 JSON/缺文件未归一 exit 2）；修复后再审 **overall: pass**（剩可选 review：pattern 信任边界已写进 `--help`）。
3. **判断**（Jev，非人工冒充）：`rulemason judge --change run-result-check` → **pass 3 / review 0 / block 0**（`jev-1.14.0`，见 `/tmp/judge-final.log`）。
4. **ruff**：`uv run ruff check .` → All checks passed。
5. **测试**：全量 **664 passed**（见上）。前端 lint / 文案检查：无，跳过。
6. **额外步骤**：未改 `rules/` / `lint/` 共享正文的接入项目验证项，跳过。
7. **OpenSpec**：`openspec validate run-result-check --strict` → Change valid。

## 相对 design 行数

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/result_check.py` | 250–400 | 360 | 在估计内 |
| `src/rulemason/cli.py` | +30–50 | +42 | 在估计内 |
| `tests/test_result_check.py` | 200–300 | 285 | 在估计内 |
| README / 帮助 | +40–80 | README 各 +1 行 + epilog | 主说明在 `--help` epilog，未超倍 |

另：`banner.py`、`tests/test_banner.py`、`tests/conftest.py`、`tests/judge/test_engine.py` 为命令表对齐与测试仓禁用签名，未单列在 design 表。

## 已知限制

- 未实现 design 决策 7 的「显式标志输出完整原文」；规格只约束默认不回显全文，默认路径用字段定位，仅当摘录窗口严格短于全文才附片段。不宣称自动脱敏。
- 模式核对信任调用方正则，无超时沙箱（`--help` 已写明）。
- 不含 RR-05 / Skill 检查实现 / 采集器 / Hook；不改 Yaomancy、check/update/judge 语义。
- **未 push / 未开 PR / 未 archive**（按用户要求 apply 后停在已实现待审）。

## 变更文件摘要

- 新增：`src/rulemason/result_check.py`，`tests/test_result_check.py`，`tests/fixtures/result_check/*`
- 修改：`src/rulemason/cli.py`，`src/rulemason/banner.py`，`README.md`，`README.en.md`，`tests/test_banner.py`，`tests/conftest.py`，`tests/judge/test_engine.py`，`openspec/changes/run-result-check/tasks.md`，本文件
