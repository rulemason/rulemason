## Why

0.8.14 在 Windows 10 中文版上实测（Notion 第 71 篇），三处修复都通过了，又测出五个问题：

- `rulemason judge --copy` 比对错了：`git show main:<文件>` 没指定编码，Windows 中文版按 GBK 解码 UTF-8 中文失败（`UnicodeDecodeError: 'gbk' codec can't decode byte 0xa6`），读不到 main 上的旧版本，把 122 条文案全当成「新增」送检（`src/rulemason/judge/judge.py:446`）。`src/rulemason/shared.py:270`、`:274`、`:340` 调 git 也没写编码。
- 在 `rulemason key` 的提示处按 Ctrl+V，窗口没有粘贴，只把控制字符 `0x16` 写进了 key 文件；`key` 没有检查就写入（`src/rulemason/key.py`）。
- 之后 `rulemason judge` 用这把 key 建客户端，打出一大段 Python 报错（`API key must contain only printable ASCII characters without whitespace`），没说 key 是从环境变量还是文件读到的、怎么修（`src/rulemason/judge/judge.py:256-263`）。
- 启动画面在 Windows 旧控制台（conhost，包括其中运行的 PowerShell）里不完整：`▀ ▄` 半格字符在控制台字体里没有字形，显示成方框，又按两格宽画，马、兔与字标被拉宽错位。只检查了宽度与编码（`src/rulemason/banner.py:104`、`:125-130`）。
- judge 输出里 specs 的小标题在 Windows 上是 `specs\character-annotation\spec.md`（`src/rulemason/judge/judge.py:406`），与其他平台不一致。

## What Changes

- 调用 git 时一律按 UTF-8 读写（`encoding="utf-8"`），`judge --copy` 在 Windows 上只检查相对 main 改过的条目。
- `rulemason key` 写入前检查：key 只能是可打印 ASCII、不含空白；不合格不写入，以非 0 退出并说明原因，含 `0x16` 时提示「用右键或 Ctrl+Shift+V 粘贴」。
- `rulemason judge` 读到的 key 含空白或不可打印字符时，一行说明 key 来自环境变量 `TYPESAFE_API_KEY` 还是哪个文件、怎么修，以非 0 退出，不打印堆栈。
- 启动画面：Windows 上只在 Windows Terminal（有 `WT_SESSION`）或 VS Code 一类终端（有 `TERM_PROGRAM`）里画图标与字标，其他情况与终端太窄时一样只显示一行「rulemason 版本号」。
- judge 输出里文件路径统一用 `/`。
- 不做：为 Windows 加 CI 运行（另开）；检查 key 的格式以外的有效性（是否被 Jev 接受，已有提示）；从剪贴板读取 key 的新参数；改启动画面的图形本身。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：`rulemason key` 写入前检查 key 的字符；启动画面在 Windows 旧控制台不画图标；新增「调用 git 按 UTF-8 读写」。
- `judge-engine`：key 含空白或不可打印字符时给一句话提示。

## Impact

- 代码：`src/rulemason/shared.py`（三处 git 调用）、`src/rulemason/judge/judge.py`（`git show`、key 检查与提示、路径分隔符）、`src/rulemason/key.py`、`src/rulemason/banner.py`；对应测试用替身模拟 Windows（GBK 默认编码、`sys.platform`、环境变量）。
- 接入项目：升级后无需操作；Windows 用户 `judge --copy` 结果会变少（只剩真正改过的条目）。
