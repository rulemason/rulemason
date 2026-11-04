## ADDED Requirements

### Requirement: 调用 git 按 UTF-8 读写

rulemason 调用 git 读取输出或传入路径时 SHALL 按 UTF-8 编码，MUST NOT 依赖系统默认编码；在 Windows 中文版（默认 GBK）上，含中文的文件内容与路径 SHALL 与其他平台得到相同结果。

#### Scenario: Windows 上比对文案
- **WHEN** 在 Windows 中文版上，`web/messages/zh.json` 相对 main 只改了 3 条文案，运行 `rulemason judge --copy`
- **THEN** 只检查这 3 条，不出现 `UnicodeDecodeError`，不把整个文件当成新增

#### Scenario: 中文文件名
- **WHEN** 项目里有被 `.gitignore` 忽略的中文文件名，在 Windows 上运行 `rulemason check`
- **THEN** 判断被忽略的文件与 macOS 上结果相同

## MODIFIED Requirements

### Requirement: rulemason key 配置 Jev 的 key

`rulemason key` SHALL 交互提示输入 key，输入不回显；写入 `~/.config/rulemason/env` 的 `TYPESAFE_API_KEY` 一行，保留文件里的其他设置；支持 POSIX 权限的平台上目录权限 SHALL 为 700、文件为 600，且写文件不跟随符号链接；没有这些能力的平台（Windows）SHALL 照常写入，汇报 MUST NOT 声称权限为 600，改为说明文件在当前用户目录下。输入的 key 去掉首尾空白后 SHALL 只含可打印 ASCII 且不含空白，否则 MUST NOT 写入，以非 0 退出并说明原因；含控制字符 `0x16`（按 Ctrl+V 未粘贴）时 SHALL 提示改用右键或 Ctrl+Shift+V 粘贴。命令 MUST NOT 接受从命令行参数或标准输入管道传入 key；非交互环境 SHALL 报错退出并说明需在终端里运行。写入后 SHALL 写明文件位置，MUST NOT 打印 key。

#### Scenario: 第一次配置
- **WHEN** 本机没有 `~/.config/rulemason/env`，在终端运行 `rulemason key` 并输入 key
- **THEN** 生成该文件（权限 600，目录 700），内容含 `TYPESAFE_API_KEY=<输入的值>`，屏幕上不出现 key

#### Scenario: 更新已有的 key
- **WHEN** 文件里已有 `TYPESAFE_API_KEY=旧值` 与 `JUDGE_PROVIDER=jev`
- **THEN** 只替换 `TYPESAFE_API_KEY` 一行，`JUDGE_PROVIDER=jev` 保留

#### Scenario: 非交互运行
- **WHEN** 在没有终端的环境（如 AI 工具或 CI）运行 `rulemason key`
- **THEN** 不写任何文件，提示在终端里运行，退出码非 0

#### Scenario: Windows 上配置
- **WHEN** 在 Windows 终端运行 `rulemason key` 并输入 key
- **THEN** 写入 `%USERPROFILE%\.config\rulemason\env`，不报 `O_NOFOLLOW` 错误；汇报写明文件位置与「在当前用户目录下」，不写「权限 600」

#### Scenario: 按 Ctrl+V 没有粘贴
- **WHEN** 在 Windows 旧控制台的输入提示处按 Ctrl+V，读到的只有控制字符 `0x16`
- **THEN** 不写 key 文件，以非 0 退出，提示 key 含不可打印字符、请用右键或 Ctrl+Shift+V 粘贴后重新运行 `rulemason key`

#### Scenario: key 中间有空格
- **WHEN** 输入的 key 中间夹着一个空格
- **THEN** 不写 key 文件，以非 0 退出，说明 key 不能含空白

### Requirement: 启动画面按终端能力降级

设置了 `NO_COLOR` 时启动画面 MUST NOT 输出颜色转义，图标 SHALL 以单一前景色画出。终端宽度小于 60 列、标准输出的编码无法写出块字符，或在 Windows 上既不在 Windows Terminal（没有 `WT_SESSION`）也不在 VS Code 一类终端（没有 `TERM_PROGRAM`）时，MUST 不画图标与字标，改为一行「rulemason 版本号」，其余文字照常显示。有颜色时，图标里的马 SHALL 用天空蓝系的 256 色，兔身 SHALL 用白色 256 色，使两只动物在暗底终端上能分辨。

#### Scenario: NO_COLOR
- **WHEN** 设置 `NO_COLOR=1` 后在终端运行 `rulemason init`
- **THEN** 启动画面不含 ANSI 颜色转义，图标与字标仍以块字符画出

#### Scenario: 终端太窄
- **WHEN** 终端宽度为 50 列
- **THEN** 不显示图标与字标，只显示「rulemason 版本号」与口号、三行说明

#### Scenario: Windows 旧控制台
- **WHEN** 在 Windows 的 cmd.exe 或 conhost 中的 PowerShell 运行 `rulemason`，没有 `WT_SESSION` 与 `TERM_PROGRAM`
- **THEN** 不画图标与字标，只显示「rulemason 版本号」与口号、三行说明和常用命令

#### Scenario: Windows Terminal
- **WHEN** 在 Windows Terminal 运行 `rulemason`（有 `WT_SESSION`），宽度不小于 60 列
- **THEN** 照常画图标与字标

#### Scenario: 马蓝兔白
- **WHEN** 未设置 `NO_COLOR`，在终端运行 `rulemason`
- **THEN** 马的像素带天空蓝系的 256 色转义，兔身的像素带白色 256 色转义；同一字符位上下两种颜色时，上像素做前景、下像素做背景画出
