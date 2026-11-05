## Why

常见的目录布局是一个文件夹 A 下放几个项目 b、c、d，各自是 git 仓库并各自接入 rulemason。在 A 里也接入时，A 自己没有代码，命令表识别成「ruff 无，跳过；测试 无，跳过」（scratchpad 模拟复现）。在 A 打开 AI 工具改 b 时，这张表最先进入上下文；在 b 打开时，Claude Code 也会往上加载 A 的 CLAUDE.md。检查点只说「运行命令表的 ruff」，没说是哪个项目的表，b 的 lint 与测试可能被跳过。

Claude Code 官方的多项目做法是在主要改的项目里打开工具、用 `--add-dir` 挂上相关项目；OpenSpec 用 store 与 `references:` 显式声明项目关系。两者都不把目录上下级当项目关系。rulemason 需要做的只是两件事：别引导人把文件夹当项目接入；检查点在一次会话涉及多个项目时说清以哪个项目为准。

## What Changes

- 文件夹提示：项目根识别不出语言、且至少有一个子目录因「另一个仓库」或「另一个 rulemason 项目」被跳过时，`init` 计划的「提示」与 `check` 识别表各加一行：这里像是放项目的文件夹，建议到各项目里分别接入，同时改几个项目时在主要改的项目里打开工具再挂上相关项目。只提示，不阻止接入。
- 检查点「本项目」的定义：共享检查点写明「本项目」指被改文件往上最近的 `.rulemason.yaml` 所在目录；一次改动跨多个项目时，每个项目各跑一遍检查点，命令在该项目根执行，diff 与提交按项目分开。
- README 补一小节：多个项目放在同一文件夹时怎么接入、怎么同时改几个项目（含 Claude Code 让挂上的目录加载 CLAUDE.md 的环境变量）。
- 不做：衔接 OpenSpec store（store 里的 change 让 `rulemason judge` 找到）；登记项目之间的关联；改 `update` 的输出；删除或改写已接入文件夹里的文件；阻止在文件夹里接入。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：新增一条「放项目的文件夹给出提示」。
- `workflow-gates`：新增一条「检查点以被改文件所属项目为准」。

## Impact

- 代码：`src/rulemason/shared.py`（文件夹判断与提示文字）、`init.py`（计划提示）、`check.py`（识别表一行）；对应测试。
- 共享正文：`rules/workflow-gates.md` 一句话。所有接入项目在下次 `rulemason update` 后拿到新副本；单项目用法下这句话不改变任何行为。
- 文档：`README.md` 一小节。
- 已在文件夹里接入的用户：`check` 会多出提示行，是否移除由人决定（`rulemason remove`）。
