# Design

## Context

- anti-slop（MIT，`3b75daa`）启发了候选 `prose_hygiene`（`bb187b2`，未批准发布）。
- multica-ai/andrej-karpathy-skills（`2c60614`）是 **Karpathy-Inspired 社区整理**，非官方；实质为编码四原则 Markdown；声明 MIT 但无 LICENSE 文件。
- 用户要求：先方案确认再实现；提升去 AI 味可与 prose_hygiene 融合，但不得预设 skills 为写作工具。

## Goals / Non-Goals

- Goals：双轨方案（文案确定性检查修订 + 编码规则层）；可解释；显式启用；兼容旧 API；列出待决项。
- Non-Goals：本轮写代码；作者识别；禁破折号=去 AI 味；自动改事实；付费模型；推送候选。

## Decisions（方案级，实施仍待确认）

1. **双轨而非单类型塞入**  
   - 否决：把 K1–K4 做成 `prose_hygiene` 短名——不可静态可靠检测。  
   - 否决：新建「去 AI 味」万能检查——宣传过度、误报高。
2. **文案轨保留三短名推荐；`em_dash` 不进推荐默认**  
   - 否决：维持四规则同等推荐——破折号误报与「去 AI 味」叙事冲突。  
   - 否决：大词表 buzzword 检测——易复制第三方词表、伪装可靠。
3. **编码轨仅规则层自研意译**  
   - 否决：复制 CLAUDE.md / SKILL.md 正文进仓库——许可文件缺失 + 单点正文重复。  
   - 否决：alwaysApply 式强制——与 rulemason「场合阅读」模型不合。
4. **默认永不全局阻塞**；配置须显式 `rules`；无 `--fix`。
5. **实施入口**：用户确认后新开实现分支自 `main`，不以推送 `bb187b2` 原样代替确认。

## Risks / Trade-offs

- [用户仍想保留 em_dash 强拦] → 对策：列为高级可选并写误报说明，不进推荐组合。
- [编码规矩必复制增加副本噪音] → 对策：决策项可选「仅有 OpenSpec/代码项目复制」；首荐全量必复制但标明场合。
- [缺 LICENSE 文件的引用风险] → 对策：只行为启发与链接归因，不嵌对方文件。

## Migration Plan

- 前向：确认后实现；旧项目不写 `prose_hygiene` 则无感。  
- 回滚：去掉新规则文件分发与检查短名即可；候选分支可保留不合并。  
- 相对 `bb187b2`：用修订提交或新分支替代「原样四规则推荐」。

## Open Questions

见 artifacts `02-fusion-recommendation.md` 五条用户决策（短名、必复制、实施分支、许可证策略、是否采纳双轨）。
