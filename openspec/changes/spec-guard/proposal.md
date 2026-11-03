## Why

主规格只在走 OpenSpec 时起作用：用户的小改动不走 OpenSpec，AI 改代码时不会去读主规格，已经承诺的行为可能被悄悄改掉；多人协作时大方向因此跑偏。归档时 OpenSpec 每次都问「是否同步主规格」，用户不理解这一问，又不得不答。判断层的启用提示只在 init 与 check 里出现，项目归档够 3 个 change 时没有人提醒。

## What Changes

- 检查点覆盖范围从「每个 OpenSpec change」扩到「每次改代码」：不走 OpenSpec 时，AI 改代码前先读相关主规格，按四条路处理：
  - 动到主规格已写的条目 → AI 代起最小 change（proposal、规格增量、一两条 tasks，不写 design），停一次等用户确认，之后照常全套检查点并归档；
  - 与主规格冲突 → 停下问用户；
  - 主规格没写到，或不改行为（修 bug 对齐规格、重构）→ 直接改；
  - 汇报写明读了哪些主规格、判在哪条路。
- 不起 change 的直接改动，改完只跑命令表的 ruff 与测试（改了前端加跑前端 lint），不跑精简与独立审查。
- 归档不再问：AI 自查 tasks 全部完成、`verification.md` 已写后，运行 `openspec archive <name> --yes` 并入主规格，再 `openspec validate --specs --strict`；自查不过或校验失败才停下，用人话说明。
- 归档后已归档数正好是 3、判断未启用且本机没有 key 时，提示一次配置 key（AI 不代配）。
- AGENTS.md 的 workflow-gates 入口块改为「改代码前也读检查点文件」；没有 OpenSpec 的项目入口块写明只适用「改完跑 ruff 与测试」。
- 不做：主规格没写到的小改动补写规格；直接修改主规格文件而不起 change；改 `openspec/config.yaml` 的 operations 基础版（OpenSpec 不允许靠它跳过提问，且会让所有接入项目报差异）；判断层的计数式催促；改项目里已有的 `openspec/specs/workflow-gates/spec.md`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `workflow-gates`：新增「不走 OpenSpec 改代码前先读主规格」「直接改动改完只跑 ruff 与测试」「归档自查后直接并入主规格」「归档够 3 个时提示一次配置 key」四条 requirement；「检查点正文只住本仓库」补入口块在改代码前也引用检查点的要求。

## Impact

- 共享正文：`rules/workflow-gates.md`（所有接入项目运行 `rulemason update` 后生效）。
- 模板：`src/rulemason/templates/workflow-gates.block.md`、`workflow-gates-no-openspec.block.md`（接入项目的标记块随 update 刷新）。
- 本仓库：`AGENTS.md` 的 Workflow gates 一节、`README.md` 检查点说明、相关测试。
- 发版 0.8.6；接入项目升级后 check 会报副本与标记块需要 update。
