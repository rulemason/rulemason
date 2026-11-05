## Why

一个接入项目的存量改造（18 项修复）留下一份产品改进建议，逐条审阅后分三批落实。第一批 7 条（A1、C2、C5、B1、C4、B4、E1）全是共享正文与 skill 的改动，不加命令、不加配置项，合成一个 change。它们对应的现象：

1. ESLint 没有和 ruff 对等的「接入前遗留」基线流程。`lint/eslint-base.mjs` 的注释与主规格都在指导「上限取当前最复杂函数的值」，项目照做后复杂度上限变成 205，整条规则关掉，豁免期间新代码不受约束；手写的「只查改动文件」命令又用 `--rule` 盖过了配置里的豁免。
2. 「不走 OpenSpec 改代码时」只按能力名筛主规格，一条点名测试函数名的规格被漏掉，改动把三条 DELETE 路由加进了那个测试的白名单，直到后面补 Purpose 时才发现。
3. 读源码再断言原文的测试锁死了旧写法，代理把代码塞进测试截取的起止标记之间，是在迎合测试。
4. React 重构时反复用到的一组「看起来等价、其实不等价」检查只存在于会话里。
5. 两个会话共用工作区时 `--amend` 改写了对方的提交并被推送；中文提交信息正文超过 commitlint 的 100 字符被拦。
6. 复杂度上限从 205 降到 30，超过 15 的函数反而从 173 变成 188，8 个函数刚好停在 30。

## What Changes

- **A1 / C2**：`lint/eslint-base.mjs` 注释改口径：超出时按文件写各自上限并标「接入前遗留」，新文件按 15；拆分目标是下一档以内、不刚好卡线，递减时同时看超过 15 的函数个数。`rules/react.md` 末段随之改一句。skill 新增「建立 ESLint 基线」一节，对称于现有「建立 ruff 基线」：用 `--format json` 按文件与规则统计，按文件生成 flat config 条目并注释标记，不整条关规则、不手写「只查改动文件」的命令；已按旧口径设了全局上限的项目写明怎么改回按文件。
- **C5**：`rules/react.md` 新小节「重构等价性」六条，不出现任何 UI 库的名字。
- **B1**：检查点「不走 OpenSpec 改代码时」第 1 步加一句：把本次要改的测试函数名、路由路径、被改函数名在 `openspec/specs/` 里检索，命中的 requirement 列进判路依据；改既有测试的断言或白名单前先检索测试名，命中规格点名的测试按「冲突」停下。
- **C4**：检查点新小节「改既有测试时」：读源码断言原文的测试只能改成新写法下的等价内容，不删除、不放宽，汇报逐条列出；走与不走 OpenSpec 两条路各引用一句。
- **B4 / E1**：「提交信息」一节扩成「提交与推送」：项目有 commitlint 时按其配置换行与限长；提交只带本次计划内的文件；共享分支不用 `--amend`，补漏另开新提交；推送前单独列出待推送提交核对，与推送分两步；并行会话建议各用 `git worktree`。
- **前端 lint 只修本次引入的问题**：检查点「apply 最后一个任务做完」第 4 步原来写「运行前端 lint 并修掉问题」，没建 ESLint 基线的项目会被要求修全部既有问题；改成和 ruff 一步对称：只修本次改动引入的，既有问题列数量并建议建 ESLint 基线（实现时独立审查第 2 轮发现，用户要求一并修）。
- README「日常」里提到建立 ruff 基线的那句补上 ESLint。
- 不做：`rulemason baseline` 命令与生成块的标记识别；`specs-for --diff` 命令；`init` 识别 commitlint 或 lint-staged；`check` 报 ESLint 基线条目数；B3 查重与 C3 存量清理流程（第三批）；D1、D2、A4（第二批）；`git commit --only` 这类具体命令进共享正文。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `shared-code-style`：修改「ESLint 基础规则由项目继承」（超出时按文件写上限，不再取最大值）；新增「React 落法写明重构等价性」。
- `rules-layer-setup`：新增「既有 ESLint 问题建立基线」，与「既有 lint 问题建立基线」（ruff）并列。
- `workflow-gates`：修改「写完代码后按顺序检查并逐项汇报」（前端 lint 只修本次引入的问题）；修改「不走 OpenSpec 改代码前先读主规格」（加检索）与「提交信息格式」（commitlint、计划内文件、不 amend、推送前核对）；新增「改既有测试时保持源码文本断言等价」。

## Impact

- 共享文件：`lint/eslint-base.mjs`、`rules/react.md`、`rules/workflow-gates.md`、`skills/rulemason/SKILL.md`、`README.md`。没有 Python 代码改动。
- 接入项目：`rulemason update` 后拿到新副本；已按旧口径设全局上限的项目 `check` 不报，下一次 `/rulemason` 巡检前端 lint 报问题时走新节改成按文件。
- 验证：改了 `rules/` 与 `skills/`，要在一个有前端的接入项目上 `update` 并按新节建一次 ESLint 基线；本机那个存量改造项目的工作区当前不在接入所在的提交上，要先切过去。
