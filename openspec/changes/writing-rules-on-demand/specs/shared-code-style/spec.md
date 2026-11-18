## MODIFIED Requirements

### Requirement: 项目在 Code style 标题下引用共享规矩

接入项目的通用指令 SHALL 保留 `## Code style` 标题，并在 rulemason 标记块内引用 `.rulemason/rules/` 下的九条与对应语言落法副本。项目 SHALL 在标记块外保留自己的样板路径、语言落法位置与豁免说明。选了 Claude Code 时，`CLAUDE.md` SHALL 导入通用指令与常驻的共享正文副本（九条、适用的语言落法、编码审慎、检查点），使会话开始即加载；OpenCode 新生成的配置 SHALL 通过 `instructions` 加载相同副本；Cursor 与 Codex SHALL 通过 `AGENTS.md` 读取。中文排版、result-check 契约、文案卫生、产品产物四份 SHALL 只在 Code style 块里列出并写明阅读场合，MUST NOT 被导入 `CLAUDE.md` 或写进新生成的 OpenCode `instructions`。

#### Scenario: 引入后 AI 读到完整规矩
- **WHEN** Claude Code、OpenCode、Cursor 或 Codex 在已接入项目中开始会话
- **THEN** 所选工具从项目内的通用指令或其原生入口读到 rulemason 的九条原则、语言落法与项目样板路径

#### Scenario: 判断规则仍能找到上层规矩
- **WHEN** 项目判断规则写 `enforces: L0/Code style`
- **THEN** 通用指令中存在 `## Code style`，判断层不报「enforces 指向不存在的上层规则」

#### Scenario: 本仓库与项目不在同一父目录
- **WHEN** 项目被单独 clone 到任意位置，附近没有 rulemason 仓库
- **THEN** 所选工具照常读到九条副本，不需要读取项目外文件

#### Scenario: 写代码的会话不加载写作类规则
- **WHEN** 选了 Claude Code 的项目运行 `rulemason init`
- **THEN** `CLAUDE.md` 的 rulemason 块不导入 `cjk-typography.md`、`result-check-contracts.md`、`prose-hygiene.md`、`product-artifact-caution.md`，`AGENTS.md` 的 Code style 块列出这四份并写明各自的阅读场合

#### Scenario: 已有 OpenCode 配置里还有这四项
- **WHEN** 已接入项目的 OpenCode `instructions` 里有这四份规则，运行 `rulemason update`
- **THEN** 配置文件不被改写，`update` 列出可以手动删去的这几项；`rulemason check` 不因它们多出来或被删去而报错

### Requirement: 常驻规则正文有字数上限

`rules/` 中每次会话常驻加载的正文（`code-style.md`、`python.md`、`react.md`、`agent-coding-caution.md`、`workflow-gates.md`）合计 SHALL 不超过 10100 个字符，由本仓库的测试检查。超出时 MUST 先合并或删掉已有句子再加新句，MUST NOT 只为通过测试而调高上限。

#### Scenario: 加规则后超限
- **WHEN** 某次改动给 `workflow-gates.md` 加了一节，五份文件合计变为 10420 个字符
- **THEN** 本仓库测试失败，改动须同时删减已有正文直到合计不超过 10100

#### Scenario: 写作类规则不计入
- **WHEN** `prose-hygiene.md` 增加了一段
- **THEN** 字数上限的测试不受影响
