# Tasks

## 1. 字段核对核心

- [x] 1.1 在 `result_check` 新增 `field` 检查类型：按 `.` 一项一路径取值；支持 `type`（含联合）、`optional`、`minimum`/`maximum`、`min_length`/`max_length`（Unicode 码点）、`enum`、`pattern`、`min_items`/`max_items`；缺 `structured`→无法判断；前缀 null/缺键→该项 skip；末段在对象上缺失或约束不符→失败；非法 pattern→输入错误。验证：pytest 覆盖通过、范围失败、长度失败、末段缺失失败、父 null skip、父缺键 skip、optional 缺键、null 联合、非法模式、无 structured、父对象子空串失败各至少一例。
- [x] 1.2 失败/依据信息不回显完整字段原文；`structured_keys` 与旧 fixture 行为不变。验证：旧 `interpret_ok`+`requirements_ok` 仍 exit 0；长字符串失败时人读报告不含该字段全文。

## 2. CLI 与文档

- [x] 2.1 更新 `result-check --help` epilog：说明 `field`、一项一路径、码点长度、`optional` 与父 null/缺键 skip、与旧 requirements 兼容、约束由调用方提供。验证：帮助可检索 `field`、码点或长度、optional 或跳过相关字样。

## 3. 回归与发版准备说明

- [x] 3.1 全量 `uv run ruff check .` 与 `uv run pytest` 通过；按 `workflow-gates` 写 `verification.md`（含发版 0.8.31、Yaomancy 接入参考：信心度 1–5、签语 6–14、应期 optional+null 与 `应期.推测` 非空；并注明 Release 须附示例 requirements 片段且不入库 `rules/`）。验证：汇报含测试数字与上述接入要点；tasks 无提前勾选。

## Workflow follow-up

- 归档时同步主规格 `run-result-check`。
- 发版 0.8.31（bump + README CI 钉版本 + `v0.8.31` tag）与 Release 示例片段由维护者在 apply 合入后执行；不在本 tasks 勾选实现发版。
