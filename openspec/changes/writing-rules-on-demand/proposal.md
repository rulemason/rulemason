## Why

接入项目的 Claude Code 每次会话都导入 9 份规则，OpenCode 的 `instructions` 也是同样 9 份。其中中文排版、result-check 契约、文案卫生、产品产物这 4 份只在写中文文档、改结构化输出、写给人读的文案或写交接产物时才用得上，`AGENTS.md` 里本来也写了各自的阅读场合，却在写代码的会话里一并读进来。另外，检查点「归档」第 5 步用一长段条件判断要不要提示启用判断，这些条件 `rulemason check` 本来就算得出来，写在规则里既占常驻字数，又要 AI 自己算。

## What Changes

- 新生成的 Claude 入口块与 OpenCode 配置不再导入上述 4 份规则，只保留九条、语言落法、编码审慎与检查点。4 份规则仍复制进 `.rulemason/rules/`，只在 `AGENTS.md` 的 Code style 块里列出并写明阅读场合。
- `AGENTS.md` Code style 块里这几行只写阅读场合，去掉命令用法（`--preset` 名称、「init/update 只分发不扫仓」等），因为这一块每次会话都会读。
- 已接入项目运行 `rulemason update` 后，Claude 入口块随标记块刷新；已有的 OpenCode 配置不自动删条目，`update` 列出可以手动删去的 4 项。
- `rulemason check` 在判断条件刚满足（已归档正好 3 个，或接入后归档正好 1 个）、尚未启用时，在报告第一行下面给一条启用提示：没有 key 时提示配置 key 与申请地址，有 key 时提示在 AI 工具里运行 `/rulemason`，都附一句判断审什么。
- 检查点「归档」第 5 步改为：归档后运行 `rulemason check`，有启用判断的提示就在汇报末尾转述一次。
- 常驻规则字数上限从 10300 降到 10100。
- 本仓库自己的 `CLAUDE.md` 与 `AGENTS.md` 的 Code style 列表同步。
- 不做：不搬走 `prose-hygiene.md`、`product-artifact-caution.md` 正文里的工具说明（按需加载后它们不占常驻字数，且主规格要求写这些内容）。
- 不做：不改写用户已有 OpenCode 配置里的 `instructions`。
- 不做：不改这 4 份规则的复制方式与 `check` 的副本比对。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `shared-code-style`：入口只导入常驻规则，写作类规则按阅读场合读；字数上限改为 10100。
- `rulekit-cli`：中文排版与 result-check 契约两份规则只在 `AGENTS.md` 的 Code style 块里引用；`check` 在判断条件刚满足时给出启用提示。
- `workflow-gates`：归档后的判断层提示改为转述 `check` 的提示。

## Impact

- 改：`src/rulemason/templates/claude.block.md`、`opencode.jsonc.tmpl`、`code-style.block.md`；`src/rulemason/check.py`（启用提示）、`src/rulemason/init.py`（OpenCode 多余条目的提示）；`rules/workflow-gates.md`；本仓库 `CLAUDE.md`、`AGENTS.md`；相关测试。
- 已接入项目 `rulemason update` 后，`CLAUDE.md` 与 `AGENTS.md` 的 rulemason 标记块会变化，需随升级一起提交。
