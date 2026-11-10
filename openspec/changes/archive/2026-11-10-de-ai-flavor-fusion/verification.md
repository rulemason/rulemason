# Verification：de-ai-flavor-fusion

版本 bump：**0.8.34**（`src/rulemason/__init__.py` + README CI 钉）。PyPI / tag 核实：最新已发布 `0.8.33` / `v0.8.33`，`0.8.34` 未占用。

## 实现阶段（归档前）

| 步骤 | 结果 |
|---|---|
| 自动精简 | 行为保持微调：预设元组去无用字段、check docstring、remove 删种子；未改外部行为 |
| 独立审查 | pass（六条产品决策）；review 已补 hint+unknown/输入错误与 remove 种子断言；无 block |
| ruff | `uv run ruff check .` → All checks passed |
| pytest | `uv run pytest` → **725 passed**（含 prose/init/remove/CLI） |
| openspec | change `--strict` valid；`--specs --strict` 通过 |
| 前端 lint | 无前端，跳过 |
| 文案检查 | 无界面文案，跳过 |
| 付费 Jev / 判断回归 | **未跑**（用户明确暂不跑付费项） |

## 发版准备阶段

| 步骤 | 结果 |
|---|---|
| 归档 | `openspec/changes/archive/2026-11-10-de-ai-flavor-fusion/`；主规格已同步（新建 `prose-hygiene`、`agent-coding-caution`；扩展 `rulekit-cli` / `run-result-check`） |
| 版本 | `0.8.34`（PyPI/tag 未占用）；`rulemason --version` → `rulemason 0.8.34` |
| ruff / pytest | 再跑通过；pytest **725 passed** |
| openspec | `--specs --strict` 13 passed；`--archived --strict` 38 passed（含本归档）；`--all --strict` specs 通过 |
| 构建 | `uv build` → `rulemason-0.8.34-py3-none-any.whl` / `.tar.gz`；wheel/sdist 均含新规则与 `templates/result-check/*.json` |
| 干净临时环境（装 wheel） | init 分发两规则+种子；改种子后 update 不覆盖；包内 `--preset hint` 命中 exit 0（含提示）；`strict` exit 1；legacy 无 prose exit 0；非法 severity exit 2；cjk+提示 exit 1 |
| 付费 Jev / 判断回归 | **仍未跑** |

## 功能核对（真实 CLI）

见交付物 CLI 样例：

- `--preset hint` 命中 → 状态「提示」，exit **0**
- `--preset strict` 同正文 → exit **1**
- 无 `prose_hygiene` 时破折号正文不因此失败
- cjk 失败 + prose 提示 → 仍 exit **1**（提示不吞错）
- 非法 severity → exit **2**

## 与计划差异

- 相对规划：按用户确认把「显式启用」改为默认 hint 分发 + 可选 strict；`em_dash` 默认关。
- 相对候选 bb187b2：未原样推送；自研实现。
- remove 增加删除已知种子文件。
- 旧候选分支 `cursor/prose-hygiene-from-antislop-aa93` **未**混入本发布。
