## Why

一个接入项目用了三天，没人知道判断层要单独搭：已归档 60 个 change、本机早有 key，判断条件一开始就满足，却一次提示都没出现过。所有提示都是围着「有没有 key」设计的：

- `init` 结尾：本机有 key 就什么都不说；
- 归档后：只在「已归档正好 3 个、本机没有 key」时提示一次。接入时就有 60 个归档的项目永远碰不到「正好 3 个」；
- `/rulemason` 补项目信息：明确要求判断「保持可选，未启用」，结束时不问；
- 日常巡检：「用户没有提出就不做」；
- 唯一一句提示在 `check` 识别表第 13 行左右。

另外，就算启用了，判断也只审 OpenSpec 方案与界面文案。用户不知道这一点，容易以为配了 key、搭了判断层就能覆盖所有改动。

## What Changes

- `init` 结尾：本机已有 key、判断条件已满足、还没启用时，多输出一行：条件已满足，判断只审 OpenSpec 方案与界面文案，要启用在 AI 工具里运行 `/rulemason` 并说明要启用判断。只是一行说明，不提问。
- `check` 识别表加一行「接入后归档 change」（接入日期之后归档的个数），供归档提示与 skill 判断用。
- 归档后的提示改为：判断条件已满足、还没启用，并且「已归档正好 3 个」或「接入后第一次归档」时，提示一次。本机没有 key 就提示配 key；已有 key 就提示运行 `/rulemason` 启用。两种都附一句覆盖范围。
- `/rulemason` 补项目信息完成时：判断条件已满足、还没启用，就在汇报末尾问一次「要不要下一次接着整理判断规则」，并说明判断只审方案与文案；接入后还没起过 change 时照实说明「启用后暂时用不上」。只问不做，本次仍不进入整理。
- README「判断」一节写明：配 key 不等于启用，启用要经 `/rulemason` 整理判断规则；判断只审方案与文案。
- 不做：在 `check` 第一行或每次运行时提示；记录「用户拒绝过」的状态；让判断也审直接改动（另一个 change `direct-edit-judgment`）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：修改「init 结尾引导配置 key」（已有 key 时也给一行启用说明）；新增「识别表写接入后归档数」。
- `workflow-gates`：移除「归档够 3 个时提示一次配置 key」，新增「归档后提示一次启用判断」。
- `rules-layer-setup`：修改「阶段一接入代码规矩与 gates」（补项目信息完成时问一次是否整理判断规则）。

## Impact

- 代码：`src/rulemason/init.py`（`guide_key`）、`src/rulemason/check.py`（识别表一行）；共享正文 `rules/workflow-gates.md`「归档」第 5 步；`skills/rulemason/SKILL.md` 第 2 节；`README.md`；对应测试。
- 接入项目：`rulemason update` 后拿到新的检查点与 skill 副本；不改任何项目文件格式。
