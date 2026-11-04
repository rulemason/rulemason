## ADDED Requirements

### Requirement: 代跑 openspec init 在 Windows 上可用

`init` 代跑 `openspec init` 时 SHALL 用 `shutil.which("openspec")` 找到的完整路径启动命令，使 Windows 上 npm 安装的 `openspec.cmd` 也能运行；找不到命令时照旧只接入「读」层。提示里展示的命令 SHALL 仍写 `openspec init --tools <所选> --language zh-CN`。

#### Scenario: Windows 上的 openspec.cmd
- **WHEN** Windows 上 npm 装的命令是 `C:\Users\<用户>\AppData\Roaming\npm\openspec.cmd`，在没有 `openspec/` 的项目运行 `rulemason init`，用户同意代跑
- **THEN** 以 `openspec.cmd` 的完整路径启动 `openspec init`，不报 `[WinError 2]`，之后继续完成接入

#### Scenario: macOS 与 Linux
- **WHEN** `openspec` 在 PATH 上是普通可执行文件，用户同意代跑
- **THEN** 行为与改动前相同：运行 `openspec init --tools <所选> --language zh-CN`

### Requirement: 控制台不支持颜色时不输出颜色

rulemason 的彩色输出（启动画面、计划摘要、汇报标题与待办）SHALL 只在标准输出是终端、没有设置 `NO_COLOR`、且控制台能显示 ANSI 颜色时出现。Windows 上 SHALL 先尝试为当前控制台开启 ANSI 支持，开启失败时 MUST NOT 输出颜色转义，文字照常输出。其他平台的判断与改动前相同。

#### Scenario: Windows 旧版控制台
- **WHEN** 在不支持 ANSI 的 Windows 控制台运行 `rulemason init`，开启 ANSI 支持失败
- **THEN** 输出里没有 `[38;5;…m` 这类转义，启动画面与计划摘要以无色文字显示

#### Scenario: Windows Terminal
- **WHEN** 在 Windows Terminal 运行 `rulemason init`，开启 ANSI 支持成功
- **THEN** 照常输出颜色

#### Scenario: 设置了 NO_COLOR
- **WHEN** 任意平台设置了 `NO_COLOR` 后运行 `rulemason check`
- **THEN** 不输出颜色，与改动前相同

### Requirement: update 写明补齐计划属于升级

`rulemason update` 与其试运行列出补齐计划时 SHALL 写明这些是写进项目文件的 rulemason 基础配置、升级时与副本一起提交，MUST NOT 只写「你自己的文件」；试运行结尾 SHALL 写明终端里运行 `rulemason update` 会询问是否补齐、非交互环境加 `--yes`，MUST NOT 写成要另加 `--yes` 再运行一遍。

#### Scenario: 补齐计划的说法
- **WHEN** 升级后 `openspec/config.yaml` 缺一条 design 基础条目，运行 `rulemason update --dry-run`
- **THEN** 补齐计划一行写明 `openspec/config.yaml` 将写入 rulemason 基础配置、升级时与副本一起提交；结尾写明终端里运行 `rulemason update` 会询问是否补齐，非交互环境加 `--yes`

#### Scenario: 交互确认后写入
- **WHEN** 在终端运行 `rulemason update`，补齐计划处答 y
- **THEN** 写入后汇报「已补齐」，并提醒补齐改动的文件与副本一起提交

## MODIFIED Requirements

### Requirement: rulemason key 配置 Jev 的 key

`rulemason key` SHALL 交互提示输入 key，输入不回显；写入 `~/.config/rulemason/env` 的 `TYPESAFE_API_KEY` 一行，保留文件里的其他设置；支持 POSIX 权限的平台上目录权限 SHALL 为 700、文件为 600，且写文件不跟随符号链接；没有这些能力的平台（Windows）SHALL 照常写入，汇报 MUST NOT 声称权限为 600，改为说明文件在当前用户目录下。命令 MUST NOT 接受从命令行参数或标准输入管道传入 key；非交互环境 SHALL 报错退出并说明需在终端里运行。写入后 SHALL 写明文件位置，MUST NOT 打印 key。

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
