## REMOVED Requirements

### Requirement: 启动画面按终端能力降级

**Reason**: 兔身白色在浅底终端上看不见；场景名「马蓝兔白」随配色一起改，OpenSpec 不允许在 MODIFIED 里改场景名，故整条换成下面的新 requirement。

**Migration**: 由「启动画面按终端能力降级与配色」接替，降级规则逐字不变，只有兔子的配色与场景名改变。

## ADDED Requirements

### Requirement: 启动画面按终端能力降级与配色

设置了 `NO_COLOR` 时启动画面 MUST NOT 输出颜色转义，图标 SHALL 以单一前景色画出。终端宽度小于 60 列、标准输出的编码无法写出块字符，或在 Windows 上既不在 Windows Terminal（没有 `WT_SESSION`）也不在 VS Code 一类终端（没有 `TERM_PROGRAM`）时，MUST 不画图标与字标，改为一行「rulemason 版本号」，其余文字照常显示。有颜色时，图标里的马 SHALL 用天空蓝系的 256 色，兔身 SHALL 用樱粉系的 256 色、兔的阴影深一档，使兔与马的色相分得开，兔身在暗底与浅底终端上都清楚。

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

#### Scenario: 马蓝兔粉
- **WHEN** 未设置 `NO_COLOR`，在终端运行 `rulemason`
- **THEN** 马的像素带天空蓝系的 256 色转义，兔身的像素带樱粉系的 256 色转义；同一字符位上下两种颜色时，上像素做前景、下像素做背景画出
