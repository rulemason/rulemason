# Tasks

## 1. 元素级约束核心

- [x] 1.1 为 `field` 增加 `items` 与对象元素 `fields`（条目默认可选填，可 `optional: true`）：配置校验；逐元素约束；失败含下标；空数组真空通过（非空只靠 `min_items`）；非数组失败；父 null/缺失 skip；无 `items` 不变。验证：pytest 覆盖字符串元素通过/失败带下标、对象缺必填键失败、`fields` 中 optional 键缺失仍通过、空数组通过、非数组失败、父缺失 skip、非法配置→exit 2、旧 field 回归各至少一例。
- [x] 1.2 合成 Yaomancy STEPS 夹具（`可做的一步` / `待确认`）验收。验证：合法数据 exit 0；空串步骤或缺必填 `怎么确认` 时非 0。

## 2. 文档与回归

- [x] 2.1 更新 `result-check --help`：`items`/`fields`、空数组真空通过、`min_items` 管非空、失败下标、`fields` 默认可选填与 optional。验证：帮助可检索 `items` 与空数组或真空相关字样。
- [x] 2.2 全量 ruff + pytest；写 `verification.md`（写明并入未发布 **0.8.31**、合入后统一打 `v0.8.31`）。验证：汇报含测试数字；tasks 无提前勾选。

## Workflow follow-up

- 归档同步主规格 `run-result-check`。
- 合入后打唯一 `v0.8.31`（不升 0.8.32）；Release 可附 STEPS 示例；不入库 `rules/`。
