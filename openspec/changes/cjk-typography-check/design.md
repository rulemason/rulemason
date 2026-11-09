# Design

## Context

- See `proposal.md` — Why。分析报告（本机上传 `cn-copywriting-analysis`）：指北仓库 MIT、`2c2d89c8`；首批规则与假阳性共性已人工分类。REA 仅作外部分析工具，**未**并入本仓库。
- 现有 `result-check`（`src/rulemason/result_check.py`）：检查类型含 `must_contain` / `pattern` / `field` 等；退出码 0/1/2；默认报告不回显全文（见 `openspec/specs/run-result-check/spec.md`）。
- `copy-voice` + `judge` 管自然度与禁感叹号等，与字形空格正交（`rules/copy-voice.md`）。
- 版本：`main` 上包版本为 `0.8.31`（`src/rulemason/__init__.py`）。

## Goals / Non-Goals

**Goals:** 在 `result-check` 增加可配置的中文排版确定性检查；首批规则可开关；预处理剥离易误伤片段；失败带规则短名与位置；非法配置 exit 2；自研实现。

**Non-Goals:** 完整指北合规认证；CSS 字距；专名大小写 / 生造缩写 / 高假阳半角标点；争议链接两侧空格与简体引号（默认可选另议）；把本检查默认塞进 `rulemason check`；复制指北长文或第三方库代码。

## Decisions

1. **已决入口：新 `result-check` 类型 `cjk_typography`（名称可在 Open Question 微调）**  
   - 否决：仅堆多条 `pattern` — 难表达预处理顺序、白名单与成对单位规则，requirements 难读。  
   - 否决：新 CLI 子命令 — 与「调用方交已发生记录」模型重复入口。  
   - 否决：本期改 `rulemason check` 扫仓库 Markdown — 巡检职责是副本/入口一致性；文档扫检另开 change，避免无调用方扩展。

2. **已决首批规则短名（自拟，非指北原文）与检测语义（在「剥离后文本」上）：**  
   | 短名 | 失败条件（意译） |
   |---|---|
   | `fullwidth_digit` | 出现全角数字 U+FF10–FF19 |
   | `stacked_punct` | 连续同类叹/问标点长度 ≥ 2；允许恰好一次的 `？！` 或 `?!`（顺序固定，见 Open Question） |
   | `cjk_latin_space` | 汉字与拉丁字母相邻且中间无空白 |
   | `cjk_digit_space` | 汉字与阿拉伯数字相邻且中间无空白 |
   | `unit_space` | 数字与配置单位词表项相邻且中间无空白（默认窄表） |
   | `degree_percent_nospace` | `\d` 与紧随的 ASCII 空白再 `°`/`%` |
   | `fw_punct_space` | 全角标点字符两侧紧贴 ASCII 空白 |  
   - 否决：首批塞进 `halfwidth_punct_in_cjk` — 假阳高，需英文跨度分析。

3. **已决预处理顺序（固定，不可由调用方重排）：**  
   1) 围栏代码块 → 占位；2) 行内代码；3) Markdown 图片/链接的目标 URL（保留可选可见文案供检或一并占位，见 Open Question）；4) 裸 URL；5) 行内 HTML 标签；6) 对剩余文本跑规则；7) 命中前再套用 allowlist（整段匹配则该命中作废）。  
   - 否决：调用方自带「已剥离」标记而不做剥离 — 易漏。

4. **已决配置形状（示意）：**  
   ```json
   {
     "id": "zh-type",
     "type": "cjk_typography",
     "rules": ["fullwidth_digit", "stacked_punct", "cjk_latin_space",
               "cjk_digit_space", "unit_space", "degree_percent_nospace",
               "fw_punct_space"],
     "units": ["GB", "TB", "Gbps", "MB", "KB", "ms", "px"],
     "allowlist": ["豆瓣FM"],
     "path": null
   }
   ```  
   - `rules` 非空且每项为已知短名；未知短名 / 未知键 / `units` 非字符串数组 → **输入错误 (2)**。  
   - `path` 可选：若提供则对 `structured` 上该路径的字符串取值检查（复用 field 路径解析与 skip）；缺省检 `record.text`。正文未提供 → 无法判断。  
   - 否决：无 `rules` 时默认全开 — 调用方必须显式选择，避免静默加严。

5. **已决报告：** 每项失败解释含规则短名与至少一个位置（优先「码点偏移」；多行文本可附行号）。证据不回显违规片段全文（与现有「不回显全文」一致，只给定位）。总体语义沿用既有汇总。

6. **已决版本：建议 `0.8.32`。**  
   - 否决：`0.9.0` — 未改变 init/update/check/`/rulemason` 阶段稳定性标准（见 `AGENTS.md` 版本节）；本能力为 additive。

## Risks / Trade-offs

- [Markdown 可见链接文案含品牌名仍误报] → 允许 allowlist；链接目标 URL 必须剥离。  
- [单位词表不全漏报 / 过宽误报] → 默认窄表 + 配置可覆盖；未知单位不检。  
- [英文整句夹在中文段落中触发中英空格] → 首批仍检相邻对；完整英文句边界留给后续或 allowlist。  
- [与 `copy-voice` 感叹号禁用重叠观感] → 本检查管「叠用」与空格字形；感叹号是否禁用仍由 copy-voice/lint。  
- [投机做仓库级 `check` 扫文档] → 明确 Non-goal，另开 change。

## Migration Plan

1. 实现模块 + `result-check` 接线 + 测试夹具；发 **0.8.32**；README/`--help` 补类型说明。  
2. 调用方在 requirements 显式加入 `cjk_typography` 才生效。  
回滚：去掉该类型检查项即可；旧 requirements 不受影响。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/cjk_typography.py`（名可微调） | 新增 | +120–200 |
| `src/rulemason/result_check.py` | 修改 | +40–80 |
| `src/rulemason/cli.py` epilog | 修改 | +5–15 |
| `tests/test_cjk_typography.py` + fixtures | 新增 | +100–180 |

## Open Questions（需用户决定）

1. 类型正式名：`cjk_typography` vs `zh_typography`？  
2. 允许的叹问组合：仅 `？！` / `?!`，还是也允许 `！？` / `!?`？  
3. Markdown 链接的**可见文案**是否参与检查（目标 URL 已剥离）？  
4. 本期是否附带「对本仓库 `rules/*.md` / README 跑一次样例」的文档任务，还是严格只交付库能力？  
5. `unit_space` 默认单位表最终名单？  
6. 合入后是否立刻发 0.8.32，还是攒批？
