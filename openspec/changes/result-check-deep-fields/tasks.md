# Tasks

## 1. 字段核对核心

- [ ] 1.1 在 `result_check` 新增 `field` 检查类型：按 `.` 路径取值；支持 `type`（含联合数组）、`minimum`/`maximum`、`min_length`/`max_length`（Unicode 码点）、`enum`、`pattern`、`min_items`/`max_items`；缺 `structured`→无法判断；路径缺失或约束不符→失败；非法 pattern→输入错误。验证：pytest 覆盖通过、范围失败、长度失败、嵌套缺失、null 联合、非法模式、无 structured 各至少一例。
- [ ] 1.2 失败/依据信息不回显完整字段原文；`structured_keys` 与旧 fixture 行为不变。验证：旧 `interpret_ok`+`requirements_ok` 仍 exit 0；长字符串失败时人读报告不含该字段全文。

## 2. CLI 与文档

- [ ] 2.1 更新 `result-check --help` epilog：说明 `field`、长度按码点、与旧 requirements 兼容、约束由调用方提供。验证：帮助可检索 `field`、码点或长度、兼容相关字样。

## 3. 回归与发版准备说明

- [ ] 3.1 全量 `uv run ruff check .` 与 `uv run pytest` 通过；按 `workflow-gates` 写 `verification.md`（含建议发版 0.8.31 与 Yaomancy 接入步骤提纲，不改产品仓）。验证：汇报含测试数字；tasks 无提前勾选。

## Workflow follow-up

- 归档时同步主规格 `run-result-check`。
- 发版 0.8.31（bump + README CI 钉版本 + `v0.8.31` tag）由维护者在 apply 合入后执行；Yaomancy 阈值与示例 requirements 片段见 design 待决，不在本 tasks 勾选。
