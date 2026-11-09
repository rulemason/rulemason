# Tasks

## 1. 核心核对库

- [x] 1.1 新增结果检查模块（建议 `src/rulemason/result_check.py` 或同级包目录）：定义记录/要求输入形状、五项状态枚举、逐项结果与汇总结构；验证：模块可导入，空要求集返回输入错误且汇总不得通过。
- [x] 1.2 实现文本必须包含 / 禁止包含 / 模式核对（含非法模式→输入错误、缺正文→无法判断）；验证：`pytest` 覆盖通过、失败、无法判断、输入错误四类各至少一例。
- [x] 1.3 实现结构化可解析与必填字段核对（缺输出→无法判断；缺字段指出字段名；不以正文出现字段名冒充）；验证：针对合成解读 JSON（对齐 `OUTPUT_SCHEMA` 字段名，自维护夹具）的 pytest 用例通过。
- [x] 1.4 实现总体通过条件与 Skill 项拒绝逻辑（要求含 Skill 出现类→输入错误且不得通过；不适用/未检查不充通过）；验证：pytest 断言含 Skill 要求时为输入错误（退出码设计为 2）、该项状态不是「通过」，且混合「一项失败其余通过」时总体未通过。
- [x] 1.5 实现来源/范围/限度字段与默认报告（不回显全文，可短摘录）；验证：单元测试断言默认渲染不含完整输入原文，JSON 结果含限度说明。

## 2. CLI 入口

- [x] 2.1 在 `cli.py` 注册独立子命令（设计名 `result-check`，若最终命名不同须与帮助一致），参数接收记录与要求路径；验证：`rulemason result-check --help`（或最终名）可用，且 `rulemason check --help` 输出未改语义。
- [x] 2.2 实现退出码：`0` 仅总体通过；`1` 失败或无法判断；`2` 输入错误；机器可读 JSON 写 stdout 或约定标志；验证：用临时夹具跑三条命令，断言退出码与 JSON `overall` 一致；对比 `rulemason check --json` 的 `schema` 仍为 1。

## 3. 离线验收夹具与文档

- [x] 3.1 在 `tests/` 加入合成「产品解读结构化输出」fixture（可对照 Yaomancy `interpret.json` 形状，不运行时依赖产品仓路径）；验证：该夹具在「必填字段齐全 + 禁词未出现」时总体通过，人为缺字段或插入禁词时非 0 退出。
- [x] 3.2 在包文档或命令帮助中写明：首场景、本期排除 Skill、fixture≠真实会话、可选日后消费 eval 报告的映射提示（不接 CI）；验证：帮助原文含上述要点的可检索关键字。

## 4. 回归与边界

- [x] 4.1 确认 `init`/`update`/`check`/`judge` 相关既有测试仍通过；验证：`uv run pytest` 全绿（或至少既有命令测试无新增失败）。
- [x] 4.2 按 `rules/workflow-gates.md` 跑判断、ruff、测试，写 `verification.md`；验证：汇报列出各步结果，且 tasks 无提前勾选实现项。

## Workflow follow-up

- 归档前将 delta 同步进 `openspec/specs/run-result-check/`（走 archive 流程，不在本期 planning 勾选）。
- 接入项目若要用：由其自行改脚本/CI；本 change 不改 Yaomancy。
- 编程 agent harness / RR-05 另开 change，需先有采集证据。
