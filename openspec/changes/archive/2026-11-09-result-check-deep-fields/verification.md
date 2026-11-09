# verification：result-check-deep-fields（apply 后）

## 实现摘要

新增检查类型 `field`：一项一路径（`.` 分隔）；`value_type`（可联合）、`optional`、`minimum`/`maximum`、`min_length`/`max_length`（Unicode 码点）、`enum`、`pattern`、`min_items`/`max_items`。前缀 null/键缺失 → 子项 skip；末段在对象上缺失 → 失败；未知约束或约束与 `value_type` 不自洽 → 输入错误（exit 2）。既有 `structured_keys` 与旧 requirements 不变。

值类型 JSON 键为 `value_type`（避免与检查项 `type: "field"` 冲突），已写入 design。

## 任务

| 任务 | 结果 |
|---|---|
| 1.1 field 核心 | pytest 覆盖通过/失败/skip/输入错误 |
| 1.2 不回显全文 + 旧 fixture | `requirements_ok` 仍 exit 0 |
| 2.1 帮助 | 含 field / value_type / 码点 / optional |
| 3.1 回归与本文件 | 见下 |

## 校验

| 命令 | 结果 |
|---|---|
| `uv run ruff check .` | exit 0 |
| `uv run pytest` | **673 passed** |
| `openspec validate --all --strict` | **10 passed**（含本 change） |
| `openspec validate result-check-deep-fields --strict` | valid |
| `rulemason check --json` | `next.code=none` |
| `rulemason judge --change result-check-deep-fields` | **3 pass / 0 review / 0 block**（jev-1.14.0） |

## 建议发版与 Yaomancy 接入（本 change 未改版本号）

1. 合入后另开 bump 至 **0.8.31**，README CI 钉版本，打 `v0.8.31`。  
2. Yaomancy：钉 `rulemason==0.8.31`，requirements 增加 field（信心度 1–5、签语 6–14、应期 optional+null 与 `应期.推测` 非空）。  
3. Release 说明附示例 requirements 片段，**不**入库 `rules/`。

## 已知限度

- 无 grapheme 计长；无完整 JSON Schema；无数组下标通配。  
- 模式无超时沙箱。  
- 不回显字段全文；不宣称自动脱敏。
