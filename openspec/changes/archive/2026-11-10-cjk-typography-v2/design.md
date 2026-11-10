# Design

## Context

- 基线：`main` `9217a78` / 0.8.32；模块 `src/rulemason/cjk_typography.py`；接线 `result_check.py`；规则 `rules/cjk-typography.md`；CI `tests/test_repo_cjk_typography_ci.py`。
- 行为来源：附件 `autocorrect-analysis.md`（autocorrect MIT，`e1a75da`）。实现**不得**打开或复制 autocorrect 源码/正则/词表/配置；短名与例句自拟。
- 只读试跑（本仓 `README.md` + `rules/**/*.md`，自拟探测器）：现有 7 条、B5、B6、B10 收窄前后、B11 增量均为 **0** 命中。

## Goals / Non-Goals

**Goals：** 第一期 B1、B3、B4、B10、B11、B5、B6；规则层同步；本仓 CI 开新规则；0.8.33；README/PR 致谢。

**Non-Goals：** 修复模式；文件扫描 CLI；B7–B9、B12–B15；Yaomancy 同步（另开）；复制 autocorrect。

## Decisions

1. **已决范围与版本：** 上列第一期；**0.8.33**；合入后是否打 tag/发 PyPI 再问用户。否决 0.9.0（非破坏性增强）。

2. **已决干净室：** 只按报告行为写规格与自拟例句；短名 snake_case；配置沿用 requirements JSON（`rules`/`units`/`allowlist`/`path`）。否决移植上游正则或 `.autocorrectrc` 键名。

3. **推荐 · 关闭注释写法（待决 OQ-1）：**  
   - 语法：HTML 注释 `<!-- rulemason-disable -->` / `<!-- rulemason-disable rule1, rule2 -->`，配对 `<!-- rulemason-enable -->` 或 `<!-- rulemason-enable rule1 -->`。  
   - **允许不带规则名**：裸 `disable` 关闭当前已启用的全部规则，至裸 `enable` 或文末。  
   - 带名时只关闭列出的短名；未知短名 → 配置/输入错误（与非法 `rules` 一致，exit 2）。  
   - 被关闭区间用现有 U+E000 遮罩，保持偏移。  
   - 否决：仿上游注释语法文件；否决仅支持「必须带规则名」（反例段落常需整段关）。

4. **已决 · 全量命中报告与兼容：**  
   - 失败时 `explanation` 含**真实总数**；若截断则明确写「显示前 N / 共 T」；`evidence` 为 JSON 对象字符串，含 `hit_total`、`hits_truncated`、`hits`（每项 `rule,line,column,offset,length`，1-based 行列，原文偏移）。可选配置 `max_hits`（正整数，默认 50）。  
   - **退出码不变**：有命中 → 1；非法配置 → 2；全过 → 0；既有 item 字段名保留。  
   - 否决：为多命中改 exit 语义；否决默认回显正文片段；否决把截断列表表述成「全部」。

5. **推荐 · B5 半角标点集（待决 OQ-3）：**  
   - 短名 `halfwidth_punct_cjk`：匹配「汉字 + 下列半角之一 + 汉字」：`, ; : ! ?`（不含 `.`、不含 `,` 的全角形式）。  
   - 不含 `.`：版本号、文件名、省略号风险（报告 C5）。  
   - 不含半角括号（归 B7，本期不做）。  
   - 否决：一期就含 `.`；否决改写为自动替换。

6. **已决 B6 短名拆分：** `fullwidth_alpha`（U+FF21–FF3A、FF41–FF5A）、`ideographic_space`（U+3000）；不改 `fullwidth_digit`。否决并入 `fullwidth_digit`（会改变已启用该短名的项目语义）。

7. **已决 B10：** 直接改默认，不设开关。空格与全角标点相邻时，若空格另一侧为（遮罩后的）URL/自动链接占位、`*` 组成的强调标记边界、或表格 `|`，则不报。否决可选项（减少配置面）。

8. **已决 B11：** `_CJK` 扩为 U+3400–4DBF ∪ U+4E00–9FFF ∪ U+F900–FAFF；假名/谚文不加。

9. **已决 B4 顺序：** 在现有链上追加：`~~~` 围栏 → 缩进代码块（CommonMark：前空行或文首后，连续行首 ≥4 空格或 tab）→ 引用式链接定义 → `<https?://…>`；仍先于规则与 allowlist。HTML 注释中的 disable 在遮罩代码/URL **之后**、跑规则 **之前** 解析（注释在已遮代码块内不生效）。

10. **已决生效方式：** 新短名写入 `KNOWN_RULES` 与 `rules/cjk-typography.md`；调用方 `rules` 显式列出才启用。本仓 CI requirements **打开**新短名。Yaomancy 同步**本期不做**，另开 change。

11. **已决致谢：** README（中）加一句：行为参考 [autocorrect](https://github.com/huacnlee/autocorrect)（MIT），未复制代码；PR 说明同句。

## Open Questions（已确认 2026-11-10）

| ID | 决定 |
|---|---|
| OQ-1 | 允许裸 disable 关全部；带名用**逗号**分隔短名 |
| OQ-2 | 退出码不变；报告含 hits；默认 max_hits=50；**必须保留真实总数并标明截断**，不得把截断列表说成全部 |
| OQ-3 | B5 仅 `,;:!?`，不含 `.` |
| OQ-4 | 缩进代码按 **CommonMark：前空行**（或文首）后连续缩进行才识别 |
| OQ-5 | 裸 enable = **恢复全部**当前关闭项 |
| OQ-6 | 行列始终按**原文**码点偏移映射 |

## Risks / Trade-offs

- [B10 放松默认] → 少数「标点旁空格贴 `|`」真问题不再报；表格误报下降优先，文档写明例外。  
- [裸 disable 滥用] → 报告/证据可含 `disabled_spans` 计数；规则层写「仅反例与特例」。  
- [B1 evidence 变长] → `max_hits` 截断；CI 日志可控。  
- [干净室被破坏] → PR/`git grep` 禁止出现上游特征路径与大段原文。

## Migration Plan

1. 实现库与接线、规则正文、CI、致谢、bump 0.8.33。  
2. 合入后**询问**是否打 `v0.8.33` / 发 PyPI。  
3. Yaomancy 另 change 决定是否把新短名写入其 requirements。  
回滚：revert；旧项目未列新短名则几乎无感（除 B10/B4/B11/报告形状）。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计 |
|---|---|---|
| `src/rulemason/cjk_typography.py` | 改 | +80–140 |
| `src/rulemason/result_check.py` | 改 | +40–70 |
| `rules/cjk-typography.md` | 改 | +15–30 |
| `tests/test_cjk_typography.py` 等 | 改/增 | +120–200 |
| `tests/test_repo_cjk_typography_ci.py` | 改 | +5–15 |
| `README.md` | 致谢 | +3–8 |
| `__init__.py` + README CI 钉 | 0.8.33 | ~3 |
| `verification.md` | 增 | +40–60 |
