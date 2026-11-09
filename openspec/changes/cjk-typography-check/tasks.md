# Tasks

> Apply 前须用户确认 `design.md` Open Questions（类型名、叹问组合、链接可见文案、是否附文档样例任务、默认单位表、发版时机）。下列任务按 design 暂定默认编写；确认后若改名/改语义，先改规格再动手。

## 1. 核心检测库

- [ ] 1.1 新增自研排版模块：固定预处理顺序；实现首批规则短名（fullwidth_digit、stacked_punct、cjk_latin_space、cjk_digit_space、unit_space、degree_percent_nospace、fw_punct_space）；allowlist；返回短名 + 码点偏移。验证：纯函数单测覆盖正/反例与代码/URL 剥离例各至少一例。
- [ ] 1.2 禁止从 Promptfoo / Rea / Cedar / Ruler / pangu / autocorrect 拷代码；模块内不出现指北长文摘录。验证：源码检索无上述项目路径或大段指北原文。

## 2. 接入 result-check

- [ ] 2.1 接线检查类型（暂定 `cjk_typography`）：配置校验（未知短名/键/空 rules/非法 allowlist→输入错误）；无正文→无法判断；可选 path 复用 field 定位与 skip。验证：pytest 覆盖 exit 0/1/2 与 path skip。
- [ ] 2.2 失败解释含规则短名与位置，不回显全文；旧 requirements 回归仍通过。验证：断言解释与 evidence 不含整段原文；`requirements_ok` 类夹具仍 exit 0。
- [ ] 2.3 更新 `result-check --help`：类型名、rules、预处理、allowlist、单位与 °/%。验证：帮助可检索类型名与 allowlist 字样。

## 3. 回归与发版准备

- [ ] 3.1 全量 ruff + pytest；写 `verification.md`（版本建议 **0.8.32**，写明 Open Questions 最终取值）。验证：汇报含测试数字；tasks 无提前勾选。
