# Design

## Context

- See `proposal.md` — Why。现有 `structured_keys` 只查顶层键（`src/rulemason/result_check.py` 约 L189–201）。
- 退出码与状态枚举已定：0 通过 / 1 失败或无法判断 / 2 输入错误；默认报告不回显全文。
- 本地快照 `/tmp/yaomancy-product`（**未核实**是否等于线上 `yaomancy/yaomancy` HEAD；`gh` 无仓库读权限）可作字段形状参考：
  - `backend/app/interpretation/prompt.py` L65–89：`OUTPUT_SCHEMA` — `信心度` integer 1–5；`签语` string（描述写 8–14 字，schema **无** minLength/maxLength）；`应期` object|null，属性 `推测` string；required 含 结论/信心度/白话推理/专业断卦/签语。
  - 同文件 L436–446：`CHOICE_SCHEMA` — required A/B/比较/建议；`应期` 同形可 null。
  - `frontend/e2e/fixtures/interpret.json`：单事样例信心度 `3`、签语「守静待时，自有转机」、应期为 `{推测:…}`。
  - `frontend/e2e/fixtures/interpret_choice.json`：抉择样例应期 `null`。
- 产品后校验（`interpreter.py`）查措辞/签语与结论重复等，**不**强制签语字数；字数目前主要在 prompt 描述。具体 CI 阈值不写死进本包。

## Goals / Non-Goals

**Goals:**

- 通用字段路径核对：嵌套、类型、数值范围、字符串长度（Unicode 码点）、枚举、字段值正则、数组长度。
- 与现有 requirements **向后兼容**：仅含旧类型的文件行为不变。
- 零新第三方依赖；确定性、不调模型。

**Non-Goals:**

- 不实现完整 JSON Schema Draft；不做 `$ref`/`allOf`/`anyOf`/`if-then`。
- 不把 Yaomancy 字段名或阈值写进共享 `rules/`；不改产品仓。

## Decisions

1. **新增检查类型 `field`（一项一路径）**，不扩展 `structured_keys` 的 `keys` 语义。  
   - 否决：把约束塞进 `structured_keys` — 旧项只声明键名，混入约束易破坏「仅存在性」语义与既有测试。  
   - 否决：整份 `structured` 一次喂完整 JSON Schema — 等于引入 Schema 引擎与组合语法，超出本期。

2. **路径语法：`.` 分隔段**（如 `应期.推测`）；段名可含中文；不支持数组下标通配（`[*]`）本期不做；**一项一路径**。`structured` 未提供 → 「无法判断」。  
   - 否决：JSON Pointer `/a/b` 唯一语法 — 中文键与转义对调用方更吵；若未来需要再兼容。  
   - 否决：本期就做数组通配或一项多 path — 无必要，组合用多条 `field` 即可。

3. **「可为 null，非 null 时校验子字段」用两条 `field` + 路径穿越规则，不做 if-then DSL。**  
   - 父路径项：如 `path: 应期`，`value_type: ["object","null"]`，并设 `optional: true`（键缺失与 `null` 同等视为类型通过；未设 `optional` 时键缺失仍为路径失败）。  
   - 子路径项：如 `path: 应期.推测`，`value_type: string`，`min_length: 1`。  
   - **穿越规则**：解析多段路径时，若某一前缀段的值是 JSON `null`，或该前缀键缺失 → 本项记「未检查/不适用」（skip），**不**失败；若前缀存在但不是可下降的 object → 失败；若前缀为 object 而末段键缺失或约束不符 → 失败。  
   - 这样：`应期: null` 或省略时，父项（optional+联合类型）通过、子项 skip；`应期: {推测: "…"}` 时子项强制非空字符串；`应期: {}` 或 `推测: ""` → 子项失败。  
   - 否决：引入 `if`/`then`/`anyOf` 组合引擎 — 投机扩展，且本期只需 null 与对象二选一。  
   - 否决：子路径在父为 null 时记失败 — 无法表达「允许 null」。

4. **约束字段（可组合，缺省表示不检查该项）**：值类型键名为 **`value_type`**（单值或联合数组；避免与检查项 `type: field` 的 JSON 键冲突）、`optional`（仅影响「键是否必须存在」）、`minimum`/`maximum`、`min_length`/`max_length`（字符串按 `len(s)`＝Unicode 码点；**不**引入 grapheme 依赖；将来若要字形簇计长另开 change）、`enum`、`pattern`、`min_items`/`max_items`。未知约束键或约束与声明的 `value_type` 不自洽 → 输入错误。  
   - 否决：依赖 PyPI `jsonschema` — 重、且鼓励投机扩展。  
   - 否决：按字形簇 / 显示宽度计长 — 无稳定标准库 API；本期固定码点。  
   - 否决：复用检查项键名 `type` 兼表值类型 — JSON 对象不能重复键。

5. **错误信息**：指出 `path`、期望约束与实际类型/标量摘要；MUST NOT 回显完整字段字符串。  
   - 否决：失败时打印整段长文本字段 — 违反默认不回显全文。

6. **版本与下游**：合入后发 **0.8.31**。Yaomancy：钉 `==0.8.31` → 自行写 `field` 项（见下「已决接入参考」）→ CI 跑 `result-check`。**0.8.31 Release 说明附 Yaomancy 示例 requirements 片段**（只在 GitHub Release / 发版说明，**不**写入共享 `rules/`）。本 change 不改产品仓。  
   - 否决：发 0.9.0 — 无破坏性契约变更。

## Risks / Trade-offs

- [调用方误以为本包内置 Yaomancy 阈值] → 帮助写明约束由 requirements 提供；Release 示例标注「下游示例，非共享规则」。
- [码点与偶发组合字符「字」数不一致] → 文档写清；将来 grapheme 另开 change，不本期引入依赖。
- [子路径 skip 被误当成通过] → skip 不计入必需通过集（既有汇总规则）；父项 optional 联合类型仍可拦住非法类型（如应期为字符串）。
- [非法 `pattern` 与值不匹配混淆] → 编译失败=输入错误(2)，不匹配=失败(1)。

## Migration Plan

1. 实现 `field`（含 `optional` 与 null/缺父 skip）+ 测试；旧 fixtures 不改仍通过。  
2. 归档同步主规格；发版 0.8.31；Release 附 Yaomancy 示例片段。  
3. Yaomancy 自行改 requirements 与钉版本。  
回滚：下游不升级或去掉 `field` 项即可。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/result_check.py` | 修改 | +100–160 |
| `src/rulemason/cli.py`（epilog） | 修改 | +5–20 |
| `tests/test_result_check.py` + fixtures | 修改/新增 | +100–160 |

## 已决事项（原 Open Questions）

1. **Yaomancy CI 签语长度**：`min_length: 6`，`max_length: 14`（上限 14，下限放宽到 6）。  
2. **长度计量**：Unicode 码点；不引入 grapheme；将来可扩展另开 change。  
3. **粒度**：一项一路径。  
4. **Release**：附 Yaomancy 示例 requirements 片段；不入库 `rules/`。

## Yaomancy 接入参考（写进 Release 示例；非本包默认）

- `信心度`：`value_type: integer`，`minimum: 1`，`maximum: 5`。  
- `签语`：`value_type: string`，`min_length: 6`，`max_length: 14`。  
- `应期`：`value_type: ["object","null"]`，`optional: true`；另条 `应期.推测`：`value_type: string`，`min_length: 1`（父为 null/缺失时子项 skip）。  
- 单事顶层键与抉择顶层键仍可用既有 `structured_keys`。
