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

2. **路径语法：`.` 分隔段**（如 `应期.推测`）；段名可含中文；不支持数组下标通配（`[*]`）本期不做。缺中间节点 → 该项「失败」并指出路径；`structured` 未提供 → 「无法判断」。  
   - 否决：JSON Pointer `/a/b` 唯一语法 — 中文键与转义对调用方更吵；若未来需要再兼容。  
   - 否决：本期就做数组通配 — 无当前调用方需求（两套 schema 均无数组必检）。

3. **约束字段（可组合，缺省表示不检查该项）**：`type`（`string`/`integer`/`number`/`boolean`/`object`/`array`/`null`，可给数组表示联合，如 `["object","null"]`）、`minimum`/`maximum`（数）、`min_length`/`max_length`（字符串，按 `len(s)`＝Unicode 码点）、`enum`、`pattern`（整值匹配，非法模式→输入错误）、`min_items`/`max_items`（数组）。  
   - 否决：依赖 PyPI `jsonschema` — 重、且鼓励投机扩展；本仓无第二个调用方要完整 Draft。  
   - 否决：按「字形簇 / 显示宽度」计长 — 标准库无稳定 API；写明码点，调用方（中文）与 `len` 一致。  
   - 否决：自动把 prompt「8–14 字」写进本包默认 — 产品无关；阈值由调用方 requirements 提供。

4. **错误信息**：指出 `path`、期望约束与实际类型/标量摘要；MUST NOT 回显完整字段字符串；短标量可给定位式摘要（沿用现有摘录限度精神）。  
   - 否决：失败时打印整段 `专业断卦` — 违反默认不回显全文。

5. **版本与下游**：实现合入后发 **0.8.31**（末位 +1；非 0.9，因兼容扩展）。Yaomancy：升级钉版本 → 在其 requirements 增加 `field` 项（信心度范围、签语长度、应期类型等）→ CI 跑 `result-check`。本 change 只在帮助/verification 写步骤，不提 PR 到产品仓。  
   - 否决：直接发 0.9.0 — 无破坏性契约变更，不符合 `AGENTS.md` 升位标准。

## Risks / Trade-offs

- [调用方误以为本包内置 Yaomancy 阈值] → 帮助与限度写明「约束由 requirements 提供」；测试用合成字段名。
- [码点长度与产品「字」直觉偶有偏差（组合字符）] → 文档写清；待决是否要 grapheme（见下）。
- [联合类型与 null 应期写错成必为 object] → 示例用 `["object","null"]`；fixture 覆盖 null 与对象两种。
- [非法 `pattern` 与值不匹配混淆] → 沿用既有：编译失败=输入错误(2)，不匹配=失败(1)。

## Migration Plan

1. 实现 `field` + 测试；旧 fixtures 不改仍通过。  
2. 归档同步主规格 `run-result-check`；发版 0.8.31（bump + README CI 钉版本 + tag）。  
3. Yaomancy 自行改 requirements 与钉版本（阈值待决）。  
回滚：下游不升级或去掉 `field` 项即可；本包无数据迁移。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/result_check.py` | 修改 | +80–140 |
| `src/rulemason/cli.py`（epilog） | 修改 | +5–15 |
| `tests/test_result_check.py` + fixtures | 修改/新增 | +80–150 |

## Open Questions（待决，不挡本规划）

1. Yaomancy CI 签语长度是否严格用 prompt 的 8–14，还是放宽/只设上限？（产品 schema 无 min/maxLength）  
2. 字符串长度是否永远用 Unicode 码点，还是未来要 grapheme？  
3. `field` 是否允许一次声明多个 path（批量），还是坚持一项一路径？本期设计为一项一路径。  
4. 是否在 0.8.31 Release 说明里附一份「Yaomancy 示例 requirements 片段」（仍不入库产品字段到 `rules/`）？
