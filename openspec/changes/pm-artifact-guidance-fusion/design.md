# Design

## Context

基线：`main` @ `71564ca`（0.8.34）。来源钉死：

| 仓库 | commit |
|---|---|
| [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | [`9af7bfd`](https://github.com/phuryn/pm-skills/commit/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef) |
| [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills) | [`cfcb697`](https://github.com/deanpeters/Product-Manager-Skills/commit/cfcb697f14b8891d8b3ec43c16c3547df3e70e13) |
| [morluto/rea](https://github.com/morluto/rea)（分析工具） | [`99d00d1`](https://github.com/morluto/rea/commit/99d00d1041e9dd66736239c5f607c7178938c118) |

REA 免费静态：`analyze-javascript-application`（本地 JS/Electron 惰性语法图；不执行代码）。两仓主体是 Markdown 技能；REA **不能**替代人工读技能正文。用户确认范围 **A+B**。

## Goals / Non-Goals

- Goals：自研产品产物规矩自动分发；可选结构预设；`must_contain`/`pattern` 安全支持 `severity=hint`；文档标明分发 ≠ 自动检查。
- Non-Goals：REA/付费 API 运行时；搬全套 PM 技能；把成功指标「看起来合理」当通过；新子命令；默认判断红线。

## Decisions（已确认）

1. **融合面：工程交接产物，不是 PM OS**  
   只收「可检验标准 / 非目标 / 证据边界 / 验收可测」进入共享规矩。否决：marketplace、GTM、简历、财务基准库、竞品情报流水线。

2. **许可证策略**  
   - MIT `pm-skills`：行为启发，自研规矩，归因 commit。
   - CC BY-NC-SA `Product-Manager-Skills`：**不复制**其 SKILL/模板；想法层独立改写 + 注明未再分发。

3. **落地形态 A+B**  
   - **A**：`rules/product-artifact-caution.md`，`COPIED_SHARED` 必复制，入口注明阅读场合。
   - **B**：包内预设，用**既有** `pattern` 检查约定小节标题；不新增 check type。
   - **C**：不做。

4. **hint 兼容增强（审查 0.8.34）**  
   - 0.8.34：`STATUS_HINT` 仅 `prose_hygiene`；`must_contain`/`pattern` 缺省失败。
   - 增强：二者可选 `severity`；**缺省 `strict`**（旧行为）；显式 `hint` → 提示不单独非零；非法 → exit 2；不得吞旧失败/无法判断。
   - `field` / `cjk_typography` / `must_not_contain` 本轮不加 severity。

5. **预设选择（无新命令、无歧义）**  
   - `--preset hint|strict` 及 `prose-hygiene.*` → 文案卫生（旧语义）。
   - `--preset product-artifact.hint|product-artifact.strict` → 产物结构。
   - 种子文件名与预设 id 对齐；项目种子优先。

6. **默认章节集合（最小中英）**  
   - 非目标：`非目标|不在范围内|Out of Scope|Non-goals?`
   - 成功/验收：`成功标准|验收标准?|Success Criteria|Acceptance`
   - 标题锚定 `^#{1,6}`；围栏内假标题为已知边界，文档声明，不自动剥代码。

7. **执行入口**  
   仅 `rulemason result-check`。`check`/`init`/`update` 不跑产物扫描。种子仅首次写入。不进默认 judge 红线。

8. **退出码**  
   提示不单独非零；失败/无法判断/输入错误仍非零。

## Risks / Trade-offs

- [把「有小节标题」当成「需求质量合格」] → 文档与报告标明结构提示 ≠ 产品正确性。
- [CC-NC-SA 误拷] → diff 审查禁止 PMS 正文。
- [围栏内假标题] → 标题锚定 + 限制文档；不改全局剥码语义。
- [偷换 `--preset hint`] → 短名固定绑定 prose-hygiene。

## Migration Plan

- 前向：update 补规矩与缺失种子；用户已有种子/requirements 不覆盖。
- 回滚：删规矩与预设即可；未声明检查的项目无感。
- 未声明 `severity` 的 `must_contain`/`pattern`：仍失败（与 0.8.34 前一致）。

## Open Questions

无（A+B、关键词集合、不进红线均已确认）。
