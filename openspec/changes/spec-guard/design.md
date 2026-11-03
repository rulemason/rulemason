## Context

见 proposal.md 的 Why。现状要点：

- 检查点正文 `rules/workflow-gates.md` 开头写「这些检查点包住每一个 OpenSpec change」，四个检查点都挂在 OpenSpec 流程的节点上。
- 接入项目 AGENTS.md 的 workflow-gates 标记块（`templates/workflow-gates.block.md`）写「开始或完成 OpenSpec 方案与实现阶段时，读取并遵守该文件」，不走 OpenSpec 的改动不会触发读取。
- OpenSpec 1.15 的归档流程（`/opsx:archive`）遇到规格增量会提示「Sync now / Archive without syncing」，并明确不允许从 `operations` 提示推断「跳过提问」；`openspec archive <name> --yes` 命令行则直接合并增量并移动目录。
- `rulemason check --json` 的 `facts` 已有「已归档 change」数与「判断」一行，后者在条件满足而无 key 时写「本机未配置 key」。
- 改共享正文与模板后，接入项目运行 `rulemason update` 刷新副本与标记块；在此之前 check 报「副本与本机版本应生成的不一致」。

## Goals / Non-Goals

**Goals:**
- 不走 OpenSpec 的改动也受主规格约束，且只有改动到已写契约时才多一次确认。
- 归档对用户不再有「是否同步」这一问，但合并结果仍经校验。

**Non-Goals:**
- 不在 rulemason 命令行里实现任何判断「改动是否动到主规格」的逻辑：这是 AI 读规格后的判断，命令行只提供已有的 `check --json` 信息。
- 不改 `openspec-base/operations.yaml`。

## Decisions

### D1 规则写进检查点正文的两个新小节

`rules/workflow-gates.md` 开头改为「包住每一次改代码」，新增「不走 OpenSpec 改代码时」与「归档」两节，其余四个检查点不动。
否决：另起 `rules/spec-guard.md`。入口块、OpenCode 的 instructions 与 CLAUDE.md 都要多引用一份文件，检查点也会拆成两处，违背「检查点正文只住一处」。否决：写进 `operations`。OpenSpec 不允许靠它跳过提问，改基础版还会让所有接入项目的 check 报「检查点提示与基础版的差异」。

### D2 划线：只有动到主规格已写的条目才起 change

四条路的判断依据是相关主规格里有没有写到这次要改的行为：
- 写到了，这次要改它 → 起最小 change，停一次等确认；
- 用户要的是别的事，做法却会顺带破坏写到的条目 → 冲突，停下问；用户选改规格就按「改契约」走；
- 没写到 → 直接改；
- 不改行为 → 直接改。

读规格时先用 `openspec list --specs` 与 `openspec show <id> --type spec --json --no-scenarios` 找相关能力，再完整读命中的那一两份。
否决：凡改行为都起 change。按项目甲近两个月 36 个 feat/fix 提交估算，归档数会翻倍，主规格也会被写进文案、默认值等细节，越来越难读，确认多了还会变成不看就点。否决：AI 直接改主规格文件、不起 change。这样没有提案记录、不过判断，与并行 change 的增量也会冲突。

### D3 最小 change 的形状

最小 change 只写 proposal、规格增量与一两条 tasks，不写 design（spec-driven 中 design 本就可选）。用户确认后照常走写代码前、写完代码后两个检查点，最后按 D4 归档。
否决：最小 change 跳过检查点。它改的正是契约，审查与测试最该跑。

### D4 归档用命令行，自查加校验兜底

归档前自查：tasks 全部勾完、`verification.md` 存在。之后运行 `openspec archive <name> --yes`，再运行 `openspec validate --specs --strict`。任何一步失败都停下说明。`openspec archive` 本身会拒绝不合法的增量（如 MODIFIED 漏了原有场景名）；`validate --strict` 再查合并后的结果，例如 init-ux-2 归档时查出的一条超过 500 字的 requirement。
否决：继续走 `/opsx:archive` 的交互同步。用户正是不理解这一问，而 operations 又不能把它关掉。否决：只跑 archive、不跑 validate。合并后的主规格超长不会被 archive 拦下。

### D5 第 3 个归档时提示 key：无状态

归档后运行 `rulemason check --json`，`facts` 里「已归档 change」为 3、「判断」一行含「本机未配置 key」时提示一次。数量不是 3 就不提，所以不需要记录「提示过没有」。
否决：写状态文件记录已提示。会多一个要提交或忽略的文件，与之前「不加状态文件、不做计数式催促」的决定冲突。否决：在命令行里提示。`openspec archive` 不是 rulemason 的命令，挂不上去。

### D6 直接改动只跑 ruff 与测试

直接改动改完后，跑命令表的 ruff 与测试，改了前端时加跑前端 lint，不跑精简与独立审查。没有 `openspec/` 的项目只剩这一条，入口块也这样写。
否决：直接改动也跑全套检查点。几行改动也要起审查代理，小事变重，与 D2 的初衷相反。否决：什么都不跑。小改动最容易顺手带出回归。

### D7 入口块改为「改代码前也读」

`workflow-gates.block.md` 改为「开始 OpenSpec 方案、实现，以及不走 OpenSpec 改代码之前，读取并遵守该文件」。`workflow-gates-no-openspec.block.md` 补一句「改代码后按该文件跑 ruff 与测试」。标记块变化由 update 刷新，check 报「标记块与当前模板不一致」时下一步就是 update。
否决：只写在 CLAUDE.md 里。Cursor、Codex、OpenCode 读不到。

## Risks / Trade-offs

- [AI 把动到契约的改动误判为「主规格未覆盖」，直接改了] → 汇报必须写明读了哪几条主规格、判在哪条路，判错一眼可见，用户一句话即可纠正。
- [每次小改动都读主规格，多花时间与 token] → 先用 `--no-scenarios` 的概览定位，只完整读命中的一两份。
- [`openspec archive --yes` 绕过了交互流程里的人工确认] → 自查加 `validate --specs --strict` 兜底，任何失败都停下；规格增量本身已在方案阶段经用户确认。
- [不同 AI 工具在很小的改动前不读 AGENTS.md] → 入口块写成「改代码之前」这样明确的时机；这类工具行为不在 rulemason 能控制的范围，验证时在 Claude Code 中实测一次。
- [接入项目升级后 check 非 0，直到运行 update] → 这是 init-ux-2 定下的预期行为，汇报里提醒运行 update。

## Migration Plan

1. 实现并通过 ruff 与测试。在项目甲、乙、丙的 worktree 里运行 `rulemason update` 与 `rulemason check`，确认标记块刷新、退出码为 0。
2. 发版 0.8.6；接入项目运行 `uv tool upgrade rulemason` 后再运行 `rulemason update`。
3. 回滚：`uv tool install rulemason==0.8.5` 后运行 `rulemason update`，副本与标记块即回到 0.8.5。本次不涉及数据格式变化。

## 文件与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `rules/workflow-gates.md` | 开头范围、「不走 OpenSpec 改代码时」「归档」两节 | +40 / −2 |
| `src/rulemason/templates/workflow-gates.block.md` | 读取时机 | ±1 |
| `src/rulemason/templates/workflow-gates-no-openspec.block.md` | 补「改代码后跑 ruff 与测试」 | ±1 |
| `AGENTS.md`（本仓库） | Workflow gates 一节的读取时机 | ±1 |
| `README.md` | 检查点说明补一句直接改动与归档 | +3 / −1 |
| `tests/test_templates.py` | 正文含两节与关键约束、入口块写明改代码前读取 | +25 |
| `tests/test_init.py` | 入口块断言更新 | ±2 |
