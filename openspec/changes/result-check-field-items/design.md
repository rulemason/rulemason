# Design

## Context

- See `proposal.md` — Why。现有 `field`（`src/rulemason/result_check.py`）支持路径、`value_type`、`optional`、标量/数组长度等，但**无**元素级约束；路径不含 `[]`。
- 本地 Yaomancy 快照 `/tmp/yaomancy-product`（**未核实**是否等于线上 HEAD）`prompt.py` L295–308：`可做的一步` = string 数组；`待确认` = 对象数组，required `卦象所示`/`怎么确认`。
- `main` 已是 `0.8.31`（#29），**尚未**打 `v0.8.31` / 发 PyPI。

## Goals / Non-Goals

**Goals:** 最小扩展使「每元素非空字符串 / 每元素必填字符串键」可表达；失败带下标；兼容现有 `field`；与 null/缺失 skip 一致。

**Non-Goals:** 完整 Schema 引擎；grapheme；改产品仓；本期打 tag；路径通配 `[]`。

## Decisions

1. **已决语法：在指向数组的 `field` 上增加 `items` 子对象**（元素约束），对象元素用嵌套 **`fields`** 描述子键约束。  
   Yaomancy 示例：
   ```json
   {"id": "steps", "type": "field", "path": "可做的一步", "value_type": "array",
    "min_items": 1, "items": {"value_type": "string", "min_length": 1}}
   {"id": "pending", "type": "field", "path": "待确认", "value_type": "array",
    "items": {"value_type": "object", "fields": {
      "卦象所示": {"value_type": "string", "min_length": 1},
      "怎么确认": {"value_type": "string", "min_length": 1}}}}
   ```
   - **否决：路径通配 `待确认[].卦象所示`** — ① 改路径语法、与「一项一路径且段=键名」冲突；② 数组级 `min_items` 与元素约束拆开多条，易漏；③ 嵌套数组更难读。仅作否决备选记录，**不再作为待选项**。  
   - **否决：新检查类型 `array_items`** — 与 `field` 重复定位/skip 逻辑。  
   - **否决：完整 JSON Schema** — 重依赖与投机扩展。

2. **已决语义**  
   - 路径先按既有规则解析到数组值；父 null/键缺失 → **skip**。  
   - 值存在但非 array → **失败**（声明了 `items` 时）。  
   - **空数组 + `items`：元素约束真空通过**；非空**仅**由调用方显式 `min_items` 强制（不因写了 `items` 而隐含 `min_items: 1`）。  
   - 对每个下标 `i` 施加 `items`；`fields` 中列出的键**默认必填**；条目可设 **`optional: true`** 使该键缺失时不失败。  
   - 失败报告路径形如 `待确认[1].卦象所示`；不回显元素全文。  
   - `items` / `fields` 内未知键或与类型不自洽 → **输入错误 (2)**。  
   - 嵌套数组：`items` 内可再含 `items`（实现设深度上限，超限 → 输入错误）。  
   - 无 `items` 的既有 `field` 行为不变。

3. **「必填键」不引入单独 `required_keys` 关键字**：`fields` 中出现且未标 `optional: true` 的键即必填。

4. **已决版本：并入未发布的 `0.8.31`**（不 bump；本 change 合入 `main` 后打**唯一** `v0.8.31`）。  
   - 否决：先 tag 再发 0.8.32 — PyPI 尚无 0.8.31，拆版本增加噪音。

## Risks / Trade-offs

- [`fields` 接近迷你 Schema，边界膨胀] → 本期只允许 `fields` 出现在 `items` 内且一层对象键→标量约束；禁止 `fields` 内再嵌 `fields`。  
- [空数组被误当成「元素都合格」] → 文档与帮助写明真空通过；非空靠 `min_items`。  
- [报告路径含 `[i]` 与真实键名混淆] → `[i]` 仅用于失败说明，不进入 path 输入语法。

## Migration Plan

1. 实现 `items`/`fields`（含 `fields` 内 `optional`）+ 测试；无 `items` 旧 requirements 回归。  
2. 合入 `main` 后打 **`v0.8.31`**（不另升 0.8.32）；Release 附 Yaomancy STEPS 示例。  
回滚：下游不写 `items` 即可。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/result_check.py` | 修改 | +80–140 |
| `src/rulemason/cli.py` epilog | 修改 | +5–15 |
| `tests/test_result_check.py` + fixtures | 修改/新增 | +80–140 |

## 已决事项（原 Open Questions）

1. 语法：**`items` + nested `fields`**（路径通配已否决）。  
2. 版本：**并入未发布的 0.8.31**，稍后统一打 `v0.8.31`。  
3. 空数组 + `items`：**真空通过**；非空只靠 `min_items`。  
4. `fields` 条目允许 **`optional: true`**；未标则必填。
