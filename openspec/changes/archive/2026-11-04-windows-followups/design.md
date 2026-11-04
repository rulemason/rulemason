# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末；行号以 init-at-cwd 改动后的工作区为准）：

- 四处 git 调用都用 `text=True` 而不写 `encoding`（精简后 `changed_copy` 改用 `shared.git`，只剩 `shared.py` 启动 git）：`shared.git()`（`src/rulemason/shared.py:270`）、`has_git`（`:274`）、`ignored_files` 的 `check-ignore --stdin`（`:340`）、`judge.changed_copy` 的 `git show main:<文件>`（`src/rulemason/judge/judge.py:446`）。不写 encoding 时 Python 按系统默认编码解码，Windows 中文版是 GBK（Notion 第 71 篇的 `UnicodeDecodeError: 'gbk' codec can't decode byte 0xa6`）。解码失败发生在读取线程里，`stdout` 拿不到，`changed_copy` 便把 main 上的旧版本当成空，整份文案都算新增。
- `rulemason key` 读入后只 `strip()`，空了才拒绝，其余原样写入（`src/rulemason/key.py`）。Windows 旧控制台里 `getpass` 收到的 Ctrl+V 是一个字符 `0x16`（实测：写入后文件里的值长度 1、编码 0x16）。
- judge 读 key：先环境变量，再 key 文件，都 `strip()`（`src/rulemason/judge/judge.py:93-106` 的 `setting`）；建客户端在 `Judge._jev`（`:256-263`），SDK 在这里校验 key 并抛 `TypeSafeError`，没有人接住，于是打出堆栈。`--dry-run` 与 `--lint-only` 不走 `_jev`。
- 启动画面：`render` 只在宽度不小于 60 且 `_unicode_ok()` 时画图标与字标（`src/rulemason/banner.py:101-104`）；`_unicode_ok` 只看标准输出编码能否写出 `█▀▄`（`:125-130`）。Windows 旧控制台的编码能写出，但字体没有半格字形、且按两格宽画（第 71 篇截图）。
- judge 的 specs 小标题是 `str(p.relative_to(d))`（`src/rulemason/judge/judge.py:406`），只用于显示，规则匹配用的是另一个字段 `"specs"`。

## Goals / Non-Goals

**Goals:**
- Windows 中文版上 `judge --copy` 与 macOS 结果相同；坏 key 在写入时就挡住，漏网的在判断时给一句话。
- 旧控制台不再显示错位的图标；其他终端不变。

**Non-Goals:**
- 不替用户判断 key 是否被 Jev 接受（已有「key 被拒绝」的提示）。
- 不检测具体字体，不改图标本身。

## Decisions

1. **`shared.py` 三处 git 调用写 `encoding="utf-8"`，`changed_copy` 改用已有的 `shared.git`。** 这样只有 `shared.py` 启动 git。否决设置 `PYTHONUTF8=1` 或改 `sys` 级默认编码：影响面是整个进程，用户环境里的其他输出也会变。否决再抽一个 `run_git()` 公共函数：`has_git` 要退出码、`ignored_files` 要传 input，抽出来要么参数很多，要么只包住一半；现在每处只多一个参数，第 7 条「两行以上重复才抽」不适用。
2. **key 的合法性只看字符：去掉首尾空白后全是可打印 ASCII（`str.isascii()` 且 `str.isprintable()`）且不含空白。** `key.py` 写入前与 `judge._jev` 建客户端前共用同一个判断函数，放在 `judge.py`（key.py 已从那里取 `KEY_NAME`、`USER_ENV`）。否决按长度或前缀判断：不知道 Typesafe key 的格式，写死会误伤。否决在 judge 里接住 SDK 的 `TypeSafeError`：接住的是整类错误，也可能吞掉别的原因；在调用前先查字符更准，也能说出 key 来自哪里。
3. **判断时说出 key 的来源。** `setting` 拆出一个返回「值与来源」的版本：来源是「环境变量 TYPESAFE_API_KEY」或 key 文件的路径。只在 `_jev` 里检查，`--dry-run`、`--lint-only`、人工模式不检查。修法按来源给：来自文件提示运行 `rulemason key`，来自环境变量提示修正或删除它（环境变量优先于文件，重写文件无效；第一轮审查发现、用户确认）。否决在 `pick_provider` 里检查：dry-run 也会经过那里，没调用 Jev 时报错多余。
4. **旧控制台判断放进能否画块字符的判断（`_unicode_ok` 改名为 `_can_draw_blocks`）。** Windows 上要求环境变量里有 `WT_SESSION`（Windows Terminal）或 `TERM_PROGRAM`（VS Code 等），否则返回 False，`render` 走已有的「一行版本号」分支。否决检测控制台字体：要调更多 Windows 接口且不可靠。否决只看代码页：英文代码页下半格字形照样可能缺，宽度问题也不只出在中日韩代码页。
5. **judge 小标题改用 `as_posix()`。** 只影响显示。否决保持原样：同一份 change 在两个平台上的输出不一致，比对与截图都别扭。

## Risks / Trade-offs

- [ConEmu、ssh 登录 Windows 时没有 `WT_SESSION` 与 `TERM_PROGRAM`，即便能画也只显示一行；从 Windows Terminal 里用 `start cmd` 开出的旧控制台会继承 `WT_SESSION`，仍会画图标] → 前者只损失图标，其余文字照常；后者少见，接受。Git Bash 的 mintty 设置了 `TERM_PROGRAM`，但原生 Windows Python 在 mintty 下多半不是终端，本来就不显示启动画面。
- [key 合法性规则过严，误拒将来含其他字符的 key] → 规则与 SDK 自身的校验（只允许可打印 ASCII、不含空白）一致，不比它更严。
- [GBK 环境只能在 macOS 上用替身模拟] → 测试让未写 encoding 的 git 调用按 GBK 解码，复现原问题；发版后请 Windows 用户再跑一次 `judge --copy`。

## Migration Plan

1. 改 `shared.py`、`judge.py`、`key.py`、`banner.py`，补测试，跑 ruff 与测试。
2. 与 init-at-cwd 一起发版（版本号按发版时 PyPI 已有版本递增），发布说明写明 Windows 修复与需要实测的项。
3. 接入项目无需操作；Windows 用户升级后重跑 `judge --copy` 与 `rulemason`。

回滚：`uv tool install rulemason==<上一版>`；本次不改任何项目文件格式。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/shared.py` | 三处 git 调用加 `encoding="utf-8"` | ±3 |
| `src/rulemason/judge/judge.py` | `changed_copy` 改用 `shared.git`；key 合法性函数与来源；`_jev` 前检查；小标题 `as_posix()` | +25 / −5 |
| `src/rulemason/key.py` | 写入前检查，含 `0x16` 时提示粘贴方式 | +8 |
| `src/rulemason/banner.py` | 块字符判断加 Windows 终端条件并改名 | +6 / −2 |
| `tests/judge/test_engine.py` | GBK 替身下 `--copy` 只检查改过的条目；坏 key 的一句话提示（文件、环境变量、`--lint-only` 不检查）；小标题 `/` | +45 |
| `tests/test_key.py` | `0x16` 与夹空格不写入 | +20 |
| `tests/test_banner.py` | Windows 无终端变量时一行版本号、有 `WT_SESSION` 时画图标 | +20 |
| `tests/test_shared.py` | GBK 替身下 `ignored_files` 处理中文文件名 | +15 |
