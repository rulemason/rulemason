# Design

## Context

- See `proposal.md`。分析报告：指北 MIT、`2c2d89c8`；七条首批已人工分类。静态分析工具 未入库。
- `result-check`：`src/rulemason/result_check.py`；退出 0/1/2。
- 规则分发：`shared.COPIED_SHARED`（`src/rulemason/shared.py` L32–40）；`check.copied_rules`（`check.py` L169–182）；入口 `templates/code-style.block.md`、`claude.block.md`、`opencode.jsonc.tmpl`。
- 本仓 CI：`.github/workflows/ci.yml` 仅 `uv run ruff` + `pytest`；job 名 `test`（`openspec/specs/repo-ci/spec.md`）。
- 版本：`0.8.31`（`src/rulemason/__init__.py`）；README CI 钉同号。

## Goals / Non-Goals

**Goals:** 两层——(a) AI 可读 `rules/` 正文经 update 分发；(b) `cjk_typography` 确定性检查；本仓 CI 覆盖约定文件；样例 + **0.8.32**。

**Non-Goals:** 指北全文合规认证；默认挂进 `rulemason check` 命令；英文 README 排版门禁；专名/缩写/半角标点/争议项；第三方库代码。

## Decisions

1. **已决入口与类型名：`cjk_typography`**（同前：否决仅 pattern / 新 CLI / 默认塞进 `check` 命令）。

2. **已决七条短名与语义**（剥离后文本）：`fullwidth_digit`；`stacked_punct`（允许恰好一次 `？！`/`?!`/`！？`/`!?`）；`cjk_latin_space`；`cjk_digit_space`；`unit_space`；`degree_percent_nospace`；`fw_punct_space`。默认 units：`GB TB Gbps MB KB ms px`。

3. **已决预处理：** 围栏代码 → 行内代码 → MD 图/链**目标**剥离（**可见文案参检**）→ 裸 URL → 行内 HTML → 规则 → allowlist。

4. **已决配置形状：** `type`/`rules` 必填；可选 `units`（省略用默认）、`allowlist`、`path`；非法 → exit 2。调用方必须显式列 `rules`。

5. **已决两份新规则文件（格式同现有：首行 HTML 注释说明用途与「勿手改副本」）：**  
   - `rules/cjk-typography.md`：七条自拟短名 + 意译要求；写文档/方案/规格时遵守；注明强制手段为 `rulemason result-check` 的 `cjk_typography`。  
   - `rules/result-check-contracts.md`：若改动被某 result-check requirements 覆盖的结构化输出 schema 或 prompt，同一次 change 必须更新该 requirements JSON 与相关夹具，并跑 `rulemason result-check`；项目专属阈值只住各项目 requirements，不写进共享文件。  
   - 否决：只写进 `openspec/config.yaml` rules — 接入项目无 OpenSpec 时 AI 仍要读得到。  
   - 否决：塞进 `copy-voice.md` — 管的是界面语气，与字形空格正交。

6. **已决分发：两份均加入 `COPIED_SHARED`，且对所有接入项目复制（与 `code-style`/`workflow-gates` 同级「必复制」）。**  
   - 入口：`code-style.block.md`（及 Claude/OpenCode 模板）增加引用行：排版规则「写中文文档/方案/规格时读」；契约规则「改结构化输出或 result-check 要求时读」。  
   - `copied_rules` / 清单 / `check` 校验与现有副本逻辑一致；`update` 补齐新文件。  
   - 否决：仅前端或仅有 judgments 才复制 — 文档排版与契约不依赖前端。  
   - 对既有项目影响：多两个只读副本与入口引用行；无新强制 lint；`check` 在 `update` 前可能报缺副本（与加 `copy-voice` 同类），升级路径为 `rulemason update`。

7. **已决本仓 CI 喂数方式：在现有 `test` job 的 pytest 内跑，不另开 job 名。**  
   - 实现：测试（或测试调用的小助手）按文件读入 UTF-8 正文，构造 `record={"text": <正文>, "source": {"kind": "fixture", "id": <路径>}}` 与固定 requirements（首批七条、默认 units），调用库/`run_check`；**一文件一项或一文件一次 run**，失败信息含路径。  
   - 否决：CI 里 shell 拼巨型单 record 合并全书 — 定位差。  
   - 否决：改 job 名为非 `test` — 破坏分支保护（repo-ci 规格）。  
   - 否决：CI 调外部模型。

8. **已决 CI 覆盖文件（本仓）：** `README.md`；`rules/**/*.md`（含新建两份）。**不覆盖** `README.en.md`、`openspec/` 历史归档、代码与 JSON 夹具。  
   - 否决：扫全部 Markdown — 归档英文/引文噪声大。

9. **已决既有违规处理（与样例任务衔接）：** apply 时先跑样例。  
   - 非平凡违规 **≤20 处**：在本 change 内修好，使 CI 门禁可绿。  
   - 非平凡违规 **>20 处**：**停下**，把完整清单（路径、规则短名、位置）写入 `verification.md` 并报告用户，**未经用户确认不得开修**；不静默扩大文档重写、不擅自改 CI 为 warn。  
   - 否决：无论多少处都强行修完 — 用户确认超额时先看清单。  
   - 否决：CI 只 warn 不失败 — 门禁在清单处理完后仍为失败即红。

10. **已决本仓 CI `allowlist`：初始为空数组（或不写该键）；仅在样例跑完后，对有意保留的例外按需填入**，并在 `verification.md` 注明每条理由。  
    - 否决：实现前预置品牌白名单 — 无样例证据。  
    - 否决：无 allowlist 能力时硬改品牌官方写法。

11. **已决版本：本 change bump `0.8.32` 并合入后打 tag。** 否决 0.9.0 / 攒批。

## Risks / Trade-offs

- [既有项目 `check` 在 update 前报缺新副本] → README/升级说明写明先 `rulemason update`；与加规则文件的既有模式一致。  
- [入口块多两行，非中文项目略吵] → 标注「写中文…时读」；文件短。  
- [本仓历史中文文档大量违规] → 先样例计数；≤20 处本 change 修；>20 处停下列清单等确认。  
- [链接可见文案误报品牌] → 样例后按需填 allowlist。  
- [契约规则无机械强制] → 靠 AI 读规则 + 人工/审查；本期不做「diff schema 对 requirements」静态分析。

## Migration Plan

1. 实现检查库 + result-check 接线 + 两份 `rules/` + 分发/入口 + 本仓 pytest CI + 修违规或 allowlist + bump 0.8.32。  
2. 合入后打 `v0.8.32`；接入项目 `rulemason update`。  
回滚：去掉类型与 CI 测试；规则文件可留（只读）或随回滚删。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/cjk_typography.py` | 新增 | +120–200 |
| `src/rulemason/result_check.py` | 修改 | +40–80 |
| `src/rulemason/cli.py` | 修改 | +5–15 |
| `src/rulemason/shared.py` / `check.py` | 修改 | +10–30 |
| `src/rulemason/templates/code-style.block.md` 等入口 | 修改 | +4–12 |
| `rules/cjk-typography.md` | 新增 | +40–80 |
| `rules/result-check-contracts.md` | 新增 | +25–50 |
| `tests/test_cjk_typography*.py` + fixtures | 新增 | +120–220 |
| `src/rulemason/__init__.py` + README CI 钉 | 修改 | ~3 |
| `.github/workflows/ci.yml` | 通常不改（并入 pytest） | 0–5 |
| `verification.md` | 新增 | +40–80 |
