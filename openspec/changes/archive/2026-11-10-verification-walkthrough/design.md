# Design

## Context

- rulemason 基线：`main` @ `f2c46355c1f8d61237a5d433cf4fa3da551d02b5`（0.8.35）。出处：`git rev-parse HEAD` / `git log -1`。
- 已有：`rules/product-artifact-caution.md`（验收可测、结构≠质量、init 只分发）；`result-check` 的 `severity=hint|strict` 与 `product-artifact.*` 预设（`src/rulemason/cli.py`、`shared.py`）。
- 上游双仓（不可融合）：
  - （已省略外部链接） @ `（已省略）`（archived，MIT）
  - （已省略外部链接） @ `（已省略）`（默认分支 `next`；另有 release `main` tip `（已省略）…`，本轮 静态分析工具 未覆盖该 tip）
- 静态分析工具包 6.8.0 @ `（已省略）…`；`静态 JS 分析命令（已省略专名）` 仅 JS；MD 工作流靠人工抽样。证据：`/opt/cursor/artifacts/（分析证据目录）/`。
- 动机与范围见 `proposal.md` Why / What Changes；完整映射见 artifacts 中文分析。

## Goals / Non-Goals

**Goals:**

- 把 外部调研材料「验证走查」原则改造成自研短规矩，并经 init/update 分发。
- 提供可选结构预设，复用既有 CLI 与 severity，默认 hint。
- 保持 0.8.35 兼容；文档写清「不复制外部正文」。

**Non-Goals:**

- 不引入 外部调研材料 运行时、命令套件、SDK、MCP、`.planning/`、自动扫仓。
- 不在本期实现 REQ-ID 强制清单（见 Open Questions）。
- 不把 OpenSpec 替换成 外部调研材料 五步环实现。

## Decisions

1. **并入 `product-artifact-caution` 增补走查原则，另立 capability 名管预设边界**  
   理由：走查文仍是工程交接产品产物；独立长文易重复「证据边界」条文。  
   否决：新建完整 `rules/verification-walkthrough-caution.md` 作为唯一正文——增加必复制文件与重复原则，收益不足（若用户确认要独立文件可改）。

2. **新预设只做小节标题存在性，默认 hint**  
   理由：与 `product-artifact.*` 同模式，避免悄悄抬高门禁。  
   否决：在 `rulemason check` 中自动扫 `**/UAT.md`——违反「分发≠执行」与用户配置保留。

3. **不 vendoring、不复制 外部调研材料 模板；不写入外部来源标识**  
   理由：MIT 允许自研参考，但 verbatim 模板会变成再分发与漂移源。  
   否决：subtree/vendor `外部验证走查调研对象/templates/*`——许可证可再分发但仍会绑死上游结构与体积。

4. **分析主源默认 外部验证走查调研对象 `next@（已省略）`；实现前再确认 tip**  
   理由：默认分支与本轮 静态分析工具/人工阅读一致。  
   否决：默默以 archived 外部归档调研对象 或未分析的 `main@（已省略）` 为唯一真源——会造成错误融合或证据缺口。

5. **无新 CLI 子命令**  
   理由：复用 `result-check --preset`。  
   否决：新增 `rulemason verify-walk`——扩大命令面且易被理解成自动执行器。

## Risks / Trade-offs

- [结构命中被当成验收通过] → 规矩与预设说明重复「结构≠质量」
- [范围膨胀成 外部调研材料 编排器] → Non-goals 与任务清单拒收运行时/命令套件
- [选错上游 tip] → 实现前确认 next vs main；不在规矩正文写入外部来源标识
- [用户已有自定义种子被覆盖] → 沿用「仅缺失时种入」策略
- [与 product-artifact 预设标题词重叠导致噪音] → 走查预设用可区分同义词表；夹具覆盖

## Migration Plan

1. 用户确认本方案（含上游 tip 与是否要独立规矩文件）后才 apply。
2. 合并后发小版本（最后一位 +1）；`init`/`update` 拉取新规矩；旧项目多种子不覆盖。
3. 回滚：还原规矩与预设登记提交；已种入项目的种子文件需项目自行删除（工具不强制删用户文件）。

## 文件与估计行数

| 文件 | 估计 |
|---|---|
| `rules/product-artifact-caution.md` | +20–30 |
| `src/rulemason/templates/result-check/verification-walkthrough.hint.json` | ~25–40 |
| `src/rulemason/templates/result-check/verification-walkthrough.strict.json` | ~25–40 |
| `src/rulemason/shared.py` | +8–15 |
| `src/rulemason/cli.py` | +4–10 |
| 相关测试 | +80–150 |
| OpenSpec 主规格同步（归档时） | 视 delta |

## Open Questions

无（用户已确认：并入 `product-artifact-caution`；REQ-ID 本期推迟）。
