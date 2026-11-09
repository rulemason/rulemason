# Tasks

## 1. 核心检测库

- [ ] 1.1 新增自研模块 `cjk_typography`：固定预处理（围栏/行内代码、MD 图链**目标**剥离、可见文案保留、裸 URL、行内 HTML）；实现短名 fullwidth_digit、stacked_punct（允许恰好一次的 `？！`/`?!`/`！？`/`!?`）、cjk_latin_space、cjk_digit_space、unit_space（默认 units：GB TB Gbps MB KB ms px）、degree_percent_nospace、fw_punct_space；allowlist；返回短名 + 码点偏移。验证：单测覆盖正/反例、四种叹问组合通过、组合后再叠失败、代码/URL 剥离、链接可见文案参检、默认 units 各至少一例。
- [ ] 1.2 禁止从 Promptfoo / Rea / Cedar / Ruler / pangu / autocorrect 拷代码；模块内不出现指北长文摘录。验证：源码检索无上述项目路径或大段指北原文。

## 2. 接入 result-check

- [ ] 2.1 接线 type `cjk_typography`：配置校验（未知短名/键/空 rules/非法 allowlist/units→输入错误）；无正文→无法判断；可选 path 复用 field 定位与 skip；省略 units 用默认表。验证：pytest 覆盖 exit 0/1/2、path skip、默认 units。
- [ ] 2.2 失败解释含规则短名与位置，不回显全文；旧 requirements 回归仍通过。验证：断言解释与 evidence 不含整段原文；既有 `requirements_ok` 类夹具仍 exit 0。
- [ ] 2.3 更新 `result-check --help`：`cjk_typography`、rules、预处理（可见链接文案参检）、allowlist、默认 units 与 °/%。验证：帮助可检索 `cjk_typography` 与 allowlist。

## 3. 本仓样例与发版

- [ ] 3.1 用 `result-check`（或库调用）对本仓库 `README.md` 与 `rules/**/*.md` 跑首批规则；结果写入 `verification.md`（路径、规则短名、位置）；发现问题先列出，不大改文档（平凡笔误可顺手）。验证：verification 含样例命令与结论表。
- [ ] 3.2 版本 bump 至 **0.8.32**：`src/rulemason/__init__.py` 与 README（及英文若有）CI 钉 `rulemason==0.8.32`。验证：`rulemason --version` 为 0.8.32；README 检索无残留 0.8.31 钉版本。
- [ ] 3.3 全量 ruff + pytest；写完 `verification.md`（含已决 Open Questions 取值与样例结果）。验证：汇报含测试数字；tasks 无提前勾选。
