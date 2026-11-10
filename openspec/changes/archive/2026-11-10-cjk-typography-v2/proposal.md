# Proposal

## Why

`cjk_typography`（0.8.32）只报首个命中、无行列号，Markdown 预处理与汉字区间仍有盲区，`fw_punct_space` 对表格竖线等误报偏严；缺少半角标点夹汉字、全角字母/全角空格规则，以及可临时关闭检查的注释。对照 autocorrect（MIT，`e1a75da`）的**行为摘要**（分析报告），用干净室自研增强，不复制其代码。

## What Changes

- **B1**：失败时列出全部命中（规则、行、列、长度）与总数；仍不回显全文；退出码语义保持 0/1/2。
- **B3**：Markdown HTML 注释 `rulemason-disable` / `rulemason-enable`（规则层说明 + 检查层遮罩）。
- **B4**：预处理补 `~~~` 围栏、缩进代码块、引用式链接定义、`<https://…>` 自动链接。
- **B10**：收窄 `fw_punct_space` 为默认：空格另一侧为 URL 占位、`**` 或表格 `|` 时不报。
- **B11**：汉字区间加扩展 A（U+3400–U+4DBF）与兼容区（U+F900–U+FAFF）。
- **B5**：新规则 `halfwidth_punct_cjk`（两汉字间半角标点，不含句点）。
- **B6**：新规则 `fullwidth_alpha`、`ideographic_space`（不改 `fullwidth_digit`）。
- 更新 `rules/cjk-typography.md`；本仓 CI 打开新规则；版本 **0.8.33**；README/PR 致谢 autocorrect（仅行为参考）。
- **不做**：修复模式、文件扫描子命令、括号/代码贴汉字/专有名词等第二期项；本期不同步 Yaomancy（规划注明，另开）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `run-result-check`：报告形状、预处理、禁用注释、汉字区间、`fw_punct_space` 收窄、新检查短名。
- `cjk-typography`：共享规则正文增短名与禁用注释约定。
- `repo-ci`：本仓 pytest 启用新短名。

## Impact

- 代码：`cjk_typography.py`、`result_check.py`、相关测试与本仓 CI 夹具；`rules/cjk-typography.md`；README 致谢；`__init__.py` → 0.8.33。
- 兼容：既有 `rules` 显式列表的项目不自动启用新短名；只开旧规则时行为除 B1/B4/B10/B11/`fw_punct_space` 收窄外不变。B1 的 JSON/人类报告字段扩展，退出码不变。
- 下游：Yaomancy 是否打开新规则另开 change。
