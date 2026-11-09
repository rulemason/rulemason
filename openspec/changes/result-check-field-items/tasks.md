# Tasks

## 1. 元素级约束核心

- [ ] 1.1 为 `field` 增加 `items`（及对象元素的 `fields`）：校验配置；对数组逐元素施加约束；失败解释含下标；空数组真空通过；非数组失败；父 null/缺失仍 skip；无 `items` 行为不变。验证：pytest 覆盖字符串元素通过/失败带下标、对象缺键失败、空数组、非数组、父缺失 skip、非法 items 配置→exit 2、旧 field 回归各至少一例。
- [ ] 1.2 合成 Yaomancy STEPS 形状夹具（`可做的一步` / `待确认`）验收通过与故意破坏失败。验证：夹具在合法数据下 exit 0；空串步骤或缺 `怎么确认` 时非 0。

## 2. 文档与回归

- [ ] 2.1 更新 `result-check --help`：说明 `items`/`fields`、空数组语义、失败下标。验证：帮助可检索 `items`。
- [ ] 2.2 全量 ruff + pytest；写 `verification.md`（含版本建议执行结果：并入 0.8.31 或改 0.8.32，以用户拍板为准）。验证：汇报含测试数字；tasks 无提前勾选。

## Workflow follow-up

- 归档同步主规格 `run-result-check`。
- 发版/tag 按 design 版本决议；Release 可附 STEPS 示例；不入库 `rules/`。
