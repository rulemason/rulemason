# Spec Delta

## MODIFIED Requirements

### Requirement: 交互运行时显示启动画面

标准输入与标准输出都是终端时，`rulemason init`（未带 `--plan`、`--json`、`--yes`）SHALL 在预检之前显示启动画面：半格像素图标（一匹奔马背上骑着一只兔，10 行、26 列）、其下空一行、半格块字标 RULEMASON 与版本号、口号「AI 写代码，也讲章法」、「只管三件事：」及读 / 守 / 查三行，末尾说明本次会做什么、先列计划确认后才写入。启动画面 MUST NOT 等待输入、MUST NOT 播放动画；其余子命令与非交互运行 MUST NOT 显示。

#### Scenario: 交互运行 init
- **WHEN** 用户在终端运行 `rulemason init`
- **THEN** 先显示启动画面与本次说明，再进入预检与工具选择

#### Scenario: 图标在字标上方
- **WHEN** 用户在宽度不小于 60 列的 UTF-8 终端运行 `rulemason init`
- **THEN** 启动画面的前 10 行是图标，第 11 行是空行，第 12 行起是 RULEMASON 字标；图标每行不超过 26 列

#### Scenario: 带参数或非交互
- **WHEN** 运行 `rulemason init --plan`、`rulemason init --tools claude --yes`，或输出被重定向
- **THEN** 不显示启动画面，输出与改动前相同
