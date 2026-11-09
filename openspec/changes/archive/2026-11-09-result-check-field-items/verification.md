# Verification：result-check-field-items

版本：**并入未发布的 0.8.31**（本 change 不 bump；合入 `main` 后统一打唯一 `v0.8.31`，不升 0.8.32）。

## 实现摘要

- `field` 支持 `items`：逐元素约束；对象元素用 `fields`（键默认必填，可 `optional: true`）。
- 空数组 + `items` 真空通过；非空靠显式 `min_items`。
- 非数组 + `items` → 失败；父 null/缺失 → 未检查/不适用；非法 `items`/`fields` → 输入错误 (2)。
- 失败路径含下标，如 `待确认[1].怎么确认`。
- 无 `items` 的既有 field 行为不变；包版本仍为 `0.8.31`。

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 自动精简 | 抽出 `_typed_scalar_hit`；去掉 `_eval_field` 与 `_apply_items` 重复的非数组分支；`items` 块不再允许无语义的 `optional` |
| 独立审查（第 1 轮） | block 2（缺 `verification.md`，本文件补齐）；review 若干（已修：`optional` 仅 fields；补非数组+`min_items`+`items`、深度超限用例） |
| 独立审查（第 2 轮） | 剩余 review 为可选覆盖（嵌套 items 成功路径等），不改方案；无未消 block |
| ruff | `uv run ruff check .` → All checks passed |
| 测试 | `uv run pytest` → **679 passed** |
| 前端 lint | 无前端，跳过 |
| 文案检查 | 无界面文案，跳过 |
| 额外步骤 | 改动未触及 `rules/` / `lint/`；`openspec validate --all --strict` → 10 passed；`rulemason check` → 日常巡检一切一致 |
| Jev | `rulemason judge --change result-check-field-items` → **pass 3 / review 0 / block 0** |

## Yaomancy STEPS 样例退出码

| 样例 | 命令要点 | exit |
|---|---|---|
| 正 | `steps_ok.json` + `requirements_steps.json` | **0** |
| 负 | `steps_bad.json`（空串步骤；缺 `怎么确认`） | **1** |
| 非法配置 | `requirements_steps_invalid.json` | **2** |

## 行数对照（design 估计）

| 文件 | 估计 | 实际（约） | 说明 |
|---|---|---|---|
| `src/rulemason/result_check.py` | +80–140 | ~+150 | 配置校验 + 运行时 helpers；略超估计仍 <2× |
| `src/rulemason/cli.py` | +5–15 | +2 | 两行 epilog |
| `tests/` + fixtures | +80–140 | 测试 ~+140 + 4 fixtures | 在范围内 |

## 未做 / 留给 follow-up

- 不归档、不推送、不打 tag、不发 PyPI（按本次指示）。
- 归档时同步主规格 `run-result-check`；合入后打 `v0.8.31`。
