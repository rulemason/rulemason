# Spec Delta

## MODIFIED Requirements

### Requirement: 交互运行时显示启动画面

标准输入与标准输出都是终端时，`rulemason init`（未带 `--plan`、`--json`、`--yes`）SHALL 在预检之前显示启动画面：半格像素图标（一匹奔马背上骑着一只兔，11 行、26 列）、其下空一行、半格块字标 RULEMASON 与版本号、口号「AI 写代码，也讲章法」、「只管三件事：」及读 / 守 / 查三行，末尾说明本次会做什么、先列计划确认后才写入。启动画面 MUST NOT 等待输入、MUST NOT 播放动画；其余子命令与非交互运行 MUST NOT 显示。

#### Scenario: 交互运行 init
- **WHEN** 用户在终端运行 `rulemason init`
- **THEN** 先显示启动画面与本次说明，再进入预检与工具选择

#### Scenario: 图标在字标上方
- **WHEN** 用户在宽度不小于 60 列的 UTF-8 终端运行 `rulemason init`
- **THEN** 启动画面的前 11 行是图标，第 12 行是空行，第 13 行起是 RULEMASON 字标；图标每行不超过 26 列

#### Scenario: 带参数或非交互
- **WHEN** 运行 `rulemason init --plan`、`rulemason init --tools claude --yes`，或输出被重定向
- **THEN** 不显示启动画面，输出与改动前相同

### Requirement: 启动画面按终端能力降级

设置了 `NO_COLOR` 时启动画面 MUST NOT 输出颜色转义，图标 SHALL 以单一前景色画出。终端宽度小于 60 列，或标准输出的编码无法写出块字符时，MUST 不画图标与字标，改为一行「rulemason 版本号」，其余文字照常显示。有颜色时，图标里的马 SHALL 用天空蓝系的 256 色，兔身 SHALL 用白色 256 色，使两只动物在暗底终端上能分辨。

#### Scenario: NO_COLOR
- **WHEN** 设置 `NO_COLOR=1` 后在终端运行 `rulemason init`
- **THEN** 启动画面不含 ANSI 颜色转义，图标与字标仍以块字符画出

#### Scenario: 终端太窄
- **WHEN** 终端宽度为 50 列
- **THEN** 不显示图标与字标，只显示「rulemason 版本号」与口号、三行说明

#### Scenario: 马蓝兔白
- **WHEN** 未设置 `NO_COLOR`，在终端运行 `rulemason`
- **THEN** 马的像素带天空蓝系的 256 色转义，兔身的像素带白色 256 色转义；同一字符位上下两种颜色时，上像素做前景、下像素做背景画出
