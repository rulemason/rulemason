## ADDED Requirements

### Requirement: key 含无效字符时给一句话提示

`rulemason judge` 要调用 Jev 时，读到的 key 去掉首尾空白后含空白、不可打印或非 ASCII 字符（与 `rulemason key` 写入时的检查一致），SHALL 以非 0 退出，用一句以「✗」开头的话说明 key 含无效字符、来自环境变量 `TYPESAFE_API_KEY` 还是哪个文件，并按来源给出修法：来自文件时提示运行 `rulemason key` 重新输入（含 `0x16` 时补「用右键或 Ctrl+Shift+V 粘贴」）；来自环境变量时提示修正或删除该环境变量（环境变量优先于文件，重写文件无效）。MUST NOT 打印 Python 堆栈。不调用 Jev 时（`--dry-run`、`--lint-only`、人工模式）不检查。

#### Scenario: key 文件里是控制字符
- **WHEN** `~/.config/rulemason/env` 里 `TYPESAFE_API_KEY` 的值是控制字符 `0x16`，没有设置环境变量，运行 `rulemason judge --change x`
- **THEN** 输出一行说明 key 含不可打印字符、来自该文件，提示运行 `rulemason key` 重新输入，退出码非 0，没有 Python 堆栈

#### Scenario: 环境变量里的 key 有空格
- **WHEN** 环境变量 `TYPESAFE_API_KEY` 的值中间夹着一个空格，运行 `rulemason judge --change x`
- **THEN** 输出一行说明 key 含空白、来自环境变量 `TYPESAFE_API_KEY`，提示修正或删除这个环境变量（不提示运行 `rulemason key`），退出码非 0，没有 Python 堆栈

#### Scenario: 只跑正则
- **WHEN** key 文件里是控制字符 `0x16`，运行 `rulemason judge --change x --lint-only`
- **THEN** 照常输出正则检查结果，不因 key 报错
