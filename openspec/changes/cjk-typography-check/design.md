# Design

## Context

- See `proposal.md` — Why。分析报告（本机上传 `cn-copywriting-analysis`）：指北仓库 MIT、`2c2d89c8`；首批规则与假阳性共性已人工分类。REA 仅作外部分析工具，**未**并入本仓库。
- 现有 `result-check`（`src/rulemason/result_check.py`）：检查类型含 `must_contain` / `pattern` / `field` 等；退出码 0/1/2；默认报告不回显全文（见 `openspec/specs/run-result-check/spec.md`）。
- `copy-voice` + `judge` 管自然度与禁感叹号等，与字形空格正交（`rules/copy-voice.md`）。
- 版本：`main` 上包版本为 `0.8.31`（`src/rulemason/__init__.py`）；README CI 示例钉 `rulemason==0.8.31`。

## Goals / Non-Goals

**Goals:** 在 `result-check` 增加可配置的中文排版确定性检查类型 `cjk_typography`；首批规则可开关；预处理剥离易误伤片段；失败带规则短名与位置；非法配置 exit 2；自研实现；对本仓库 README 与 `rules/` 跑一次样例并记录结果；合入后发 **0.8.32**。

**Non-Goals:** 完整指北合规认证；CSS 字距；专名大小写 / 生造缩写 / 高假阳半角标点；争议链接两侧空格与简体引号；把本检查**默认**挂进 `rulemason check` 巡检；复制指北长文或第三方库代码；因样例扫出本仓文档问题而大改文档（仅汇报；平凡笔误可顺手改）。

## Decisions

1. **已决入口与类型名：`result-check` 类型 `cjk_typography`**  
   - 否决：`zh_typography` — 与 Unicode 中日韩混排语义更贴的是 `cjk_` 前缀。  
   - 否决：仅堆多条 `pattern` — 难表达预处理顺序、白名单与成对单位规则。  
   - 否决：新 CLI 子命令 — 与「调用方交已发生记录」模型重复。  
   - 否决：本期把本检查默认塞进 `rulemason check` — 巡检职责是副本/入口一致性；样例用 `result-check` 离线跑即可。

2. **已决首批规则短名（自拟）与检测语义（在「剥离后文本」上）：**  
   | 短名 | 失败条件（意译） |
   |---|---|
   | `fullwidth_digit` | 出现全角数字 U+FF10–FF19 |
   | `stacked_punct` | 连续叹/问标点长度 ≥ 2；允许恰好一次的 `？！`、`?!`、`！？`、`!?`（四种各算一次合法组合，不得再叠） |
   | `cjk_latin_space` | 汉字与拉丁字母相邻且中间无空白 |
   | `cjk_digit_space` | 汉字与阿拉伯数字相邻且中间无空白 |
   | `unit_space` | 数字与单位词表项相邻且中间无空白 |
   | `degree_percent_nospace` | `\d` 与紧随的 ASCII 空白再 `°`/`%` |
   | `fw_punct_space` | 全角标点字符两侧紧贴 ASCII 空白 |  
   - 否决：首批塞进 `halfwidth_punct_in_cjk` — 假阳高。  
   - 否决：只允许 `？！`/`?!` — 用户确认四种顺序均合法。

3. **已决预处理：链接可见文案参检，目标剥离**  
   固定顺序：1) 围栏代码 → 占位；2) 行内代码；3) Markdown 图片/链接的**目标 URL**（保留可见文案供检）；4) 裸 URL；5) 行内 HTML 标签；6) 对剩余文本跑规则；7) allowlist（整段匹配则作废该命中）。  
   - 否决：可见链接文案一并占位 — 用户确认可见文案须检查。  
   - 否决：调用方自带「已剥离」而不做剥离。

4. **已决默认 `units`：`GB` `TB` `Gbps` `MB` `KB` `ms` `px`**（配置可覆盖；未列入的单位不检）。  
   - 否决：更大通用单位表 — 易误伤缩写。

5. **已决配置形状：**  
   ```json
   {
     "id": "zh-type",
     "type": "cjk_typography",
     "rules": ["fullwidth_digit", "stacked_punct", "cjk_latin_space",
               "cjk_digit_space", "unit_space", "degree_percent_nospace",
               "fw_punct_space"],
     "units": ["GB", "TB", "Gbps", "MB", "KB", "ms", "px"],
     "allowlist": ["豆瓣FM"]
   }
   ```  
   - 省略 `units` 时用上述默认表。`rules` 非空且均为已知短名；未知短名 / 未知键 / 非法 `units`/`allowlist` → **输入错误 (2)**。  
   - 可选 `path`：对 `structured` 字符串取值（field 路径与 skip）；缺省检 `record.text`。  
   - 否决：无 `rules` 时默认全开。

6. **已决报告：** 失败解释含规则短名与至少一个码点偏移（或多行时行号）；不回显违规全文。

7. **已决本仓样例任务：** apply 末用 `result-check`（或等价库调用）对本仓库 `README.md` / `README.en.md`（若检中文段）与 `rules/**/*.md` 跑首批规则，结果写入 `verification.md`；发现问题先列出；**不**为清零而大改文档，平凡笔误可顺手改。  
   - 否决：不做样例 — 用户要求留下自检证据。

8. **已决版本：本 change 含 bump 至 `0.8.32`**（`src/rulemason/__init__.py` + README CI 钉版本），合入后立刻打 `v0.8.32` 发 PyPI。  
   - 否决：`0.9.0` — 未达 `AGENTS.md` 的 0.9 入口稳定标准。  
   - 否决：攒批另开 bump change — 用户要求合入后马上发。

## Risks / Trade-offs

- [Markdown 可见链接文案含品牌名仍误报] → allowlist；目标 URL 必须剥离。  
- [单位词表不全漏报 / 过宽误报] → 默认窄表已决；配置可覆盖。  
- [英文整句夹中文触发中英空格] → 首批仍检相邻对；用 allowlist 或后续再开边界分析。  
- [与 `copy-voice` 感叹号禁用观感重叠] → 本检查只管叠用与空格字形。  
- [本仓样例扫出大量历史文案问题] → verification 列表；不大改文档。

## Migration Plan

1. 实现模块 + `result-check` 接线 + 测试 + 本仓样例记录 + bump **0.8.32**。  
2. 合入 `main` 后打 **`v0.8.32`** 发 PyPI。  
回滚：调用方去掉该类型；版本回退另议。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/cjk_typography.py` | 新增 | +120–200 |
| `src/rulemason/result_check.py` | 修改 | +40–80 |
| `src/rulemason/cli.py` epilog | 修改 | +5–15 |
| `src/rulemason/__init__.py` | 修改 | 1 |
| `README.md`（及英文 CI 钉版本若有） | 修改 | ~2 |
| `tests/test_cjk_typography.py` + fixtures | 新增 | +100–180 |
| `verification.md`（含本仓样例结果） | 新增 | ~40–80 |
