# Design

## Context

- See `proposal.md` — Why。现有 `field`（`src/rulemason/result_check.py`）支持路径、`value_type`、`optional`、标量/数组长度等，但**无**元素级约束；路径不含 `[]`。
- 本地 Yaomancy 快照 `/tmp/yaomancy-product`（**未核实**是否等于线上 HEAD）`prompt.py` L295–308：`可做的一步` = string 数组；`待确认` = 对象数组，required `卦象所示`/`怎么确认`。
- `main` 已是 `0.8.31`（#29），**尚未**打 `v0.8.31` / 发 PyPI。

## Goals / Non-Goals

**Goals:** 最小扩展使「每元素非空字符串 / 每元素必填字符串键」可表达；失败带下标；兼容现有 `field`；与 null/缺失 skip 一致。

**Non-Goals:** 完整 Schema 引擎；grapheme；改产品仓；本期打 tag。

## Decisions

1. **推荐语法：在指向数组的 `field` 上增加 `items` 子对象**（元素约束），可选嵌套 `fields` 描述对象元素的必填子键。  
   Yaomancy 示例：
   ```json
   {"id": "steps", "type": "field", "path": "可做的一步", "value_type": "array",
    "min_items": 1, "items": {"value_type": "string", "min_length": 1}}
   {"id": "pending", "type": "field", "path": "待确认", "value_type": "array",
    "items": {"value_type": "object", "fields": {
      "卦象所示": {"value_type": "string", "min_length": 1},
      "怎么确认": {"value_type": "string", "min_length": 1}}}}
   ```
   - **否决 A：路径通配 `待确认[].卦象所示`** — 能用多条 `field` 表达必填子键且不必引入 `fields`，但：① 改路径语法、与「一项一路径且段=键名」冲突；② 数组级 `min_items` 与元素约束拆开多条，易漏；③ 嵌套数组 `a[][]` 更难读。作备选（见 Open Questions）。  
   - **否决 B：新检查类型 `array_items`** — 与 `field` 重复定位/skip 逻辑，调用方多学一个 type。  
   - **否决 C：完整 JSON Schema `items`/`required`** — 重依赖与投机扩展，超出最小范围。

2. **语义（推荐方案）**  
   - 路径先按既有规则解析到数组值；父 null/键缺失 → **skip**（与现网一致）。  
   - 值存在但非 array → **失败**（若声明了 `items` 或 `value_type` 含 array）。  
   - **空数组**：元素约束**真空通过**（无元素可失败）；若需非空，调用方另写 `min_items`。  
   - 对每个下标 `i` 将 `items` 约束作用于 `arr[i]`；对象元素上 `fields` 的每个键默认**必填**（等价 optional:false）；子键缺失 → 失败。  
   - 失败报告路径形如 `待确认[1].卦象所示`（含下标）；不回显元素全文。  
   - `items` / `fields` 内未知键、或与 `value_type` 不自洽 → **输入错误 (2)**。  
   - 嵌套数组：`items` 内可再含 `items`（有限深度即可，实现设合理上限如 4，超限配置 → 输入错误）。  
   - 无 `items` 的既有 `field` 行为不变。

3. **「必填键」不必单独 `required_keys` 关键字**：在推荐方案里，`fields` 中出现的键即必填；若选路径通配备选，则用子路径默认非 optional 即可。

4. **版本建议：保留 `0.8.31`，将本能力并入同一未发布版本后再打唯一 `v0.8.31`。**  
   - 理由：PyPI 尚无 0.8.31；消费者未钉到该号；拆成 0.8.31（无 items）+ 立刻 0.8.32 增加噪音。  
   - 否决：先 tag 0.8.31 再发 0.8.32 — 除非用户已对外承诺「0.8.31 = 仅 #28 的 field」。若已承诺，则改升 **0.8.32**（待决）。

## Risks / Trade-offs

- [`fields` 接近迷你 Schema，边界膨胀] → 本期只允许 `fields` 出现在 `items` 内且一层对象键→标量约束；禁止 `fields` 内再嵌 `fields`（嵌套对象另开 change）。  
- [空数组被误当成「元素都合格」] → 文档写明真空通过；示例带 `min_items`。  
- [下标路径与真实键名含 `[` 冲突] → 报告用合成显示路径，不把 `[i]` 写进 path 输入语法（推荐方案输入 path 仍无括号）。

## Migration Plan

1. 实现 `items`/`fields` + 测试；无 `items` 的旧 requirements 回归。  
2. 若采纳「并入 0.8.31」：本 change 合入 `main` 后**再**打 `v0.8.31`；Release 附 Yaomancy STEPS 示例。  
3. 若改升 0.8.32：先 tag 当前 main 为 v0.8.31（可选）或跳过，再 bump。  
回滚：下游不写 `items` 即可。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/result_check.py` | 修改 | +80–140 |
| `src/rulemason/cli.py` epilog | 修改 | +5–15 |
| `tests/test_result_check.py` + fixtures | 修改/新增 | +80–140 |

## Open Questions（需用户拍板）

1. 确认推荐 **`items` + `fields`**，还是改用路径通配 `[]`？  
2. 版本：确认 **并入未发布的 0.8.31**，还是 bump **0.8.32**？  
3. 空数组 + `items`：确认真空通过（推荐），还是配置了 `items` 就隐含 `min_items: 1`？  
4. `fields` 是否允许标量键上的 `optional: true`（部分键可选）？推荐允许，默认必填。
