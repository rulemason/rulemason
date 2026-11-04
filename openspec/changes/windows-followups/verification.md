# Verification：windows-followups

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。本机是 macOS，Windows 行为用替身测试，未在真实 Windows 上核实的部分在文末列出。

## 写代码前检查点

`rulemason judge --change windows-followups`：pass 3 / review 0 / block 0。开工前已把同分支上的 init-at-cwd 单独提交（用户同意），两个 change 各一个提交。

## 1. 自动精简与独立审查

**自动精简（`/simplify`，四路并行）**，只采纳行为保持的修改：

- 采纳：`judge.changed_copy` 改用已有的 `shared.git`（只剩 `shared.py` 启动 git，UTF-8 写在一处）；两个 judge 用例改用已有的 `_user_env`；测试空行。
- 跳过：再抽 `_run_git`（`has_git`、`ignored_files` 要用退出码与 input，design 决策 1 已否决）；只读一次 key 文件、把 SDK 导入挪到检查之后（性能类，不采纳）；把检查挪进 `api_key()`（check、init 只看有没有 key，挪进去会改变它们的输出）。
- 修复层级方向核对：`src/rulemason` 里所有 `read_text`、`write_text`、`fdopen` 都已写 `encoding="utf-8"`；代跑 openspec 的 `subprocess.run` 不捕获输出，不解码。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：block 0，review 7：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | review：design、tasks 仍写「四处 git 调用各加 encoding」→ 同步为「shared.py 三处加、changed_copy 改用 shared.git」；design 写「改名为能否画块字符」而函数没改名 → `_unicode_ok` 改名为 `_can_draw_blocks` |
| 正确性 | review：key 来自环境变量时提示「运行 rulemason key」无效（环境变量优先）→ 要改规格，已请用户决定，用户选「按来源给修法」：来自环境变量提示修正或删除它；含 0x16 时粘贴提示排在「运行 rulemason key」之前，语序倒了 → `key_problem` 只给原因，新增 `paste_hint` 接在修法之后；design Risks 对 mintty、ssh、从 Windows Terminal 开出的旧控制台描述不准 → 改写 |
| 安全 | pass（报错不回显 key 的值） |
| 代码质量 | pass |
| 测试 | review：缺 `key_problem` 直接用例、缺「已有文件不被改动」、坏 key 用例没走完整调用路径、`--lint-only` 用例的断言不起作用；小标题用例与 tasks 写法不符 → 全部补上或改写 |
| 变更卫生 | pass |

第二轮：block 0，review 3。按规则修完后只跑 ruff 与测试，不审第三轮：

- 「`_jev` 不再调 `api_key()`，空 key 会不会绕过」→ 核对：`api_key()` 仍被 check、init、`pick_provider` 调用；`pick_provider` 在没有 key 时走人工或报错，空 key 到不了 `_jev`；`project` 夹具已清掉环境变量。未改代码。
- 用展示文案判断 key 来源 → 改为直接看环境变量是否有值（与读取的优先级一致）。
- judge-engine 规格只写「空白或不可打印」，实现还拒绝非 ASCII → 规格改为「空白、不可打印或非 ASCII 字符」，与 rulekit-cli 一致。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：542 passed（本 change 之前 523）。GBK 替身用例（`judge --copy` 只检查改过的条目、`ignored_files` 中文文件名）在修复前失败、修复后通过。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案（命令行提示文字由测试锁定）。

## 6. 额外步骤

未改 `rules/`、`lint/` 或 skill，额外步骤不适用；仍在项目甲、乙、丙运行开发版与 0.8.14 的 `rulemason check`、`rulemason judge --change <最近归档的 change> --lint-only`，输出完全相同。

## 与 design 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/shared.py` | ±3 | +5 / −4 | `ignored_files` 一行拆成两行 |
| `src/rulemason/judge/judge.py` | +25 / −5 | +38 / −10 | 审查后补 `paste_hint` 与按来源给修法 |
| `src/rulemason/key.py` | +8 | +4 | |
| `src/rulemason/banner.py` | +6 / −2 | +7 / −2 | |
| `tests/judge/test_engine.py` | +45 | +42 | |
| `tests/test_key.py` | +20 | +27 | 审查后补 `key_problem` 参数化与「不改已有文件」 |
| `tests/test_banner.py` | +20 | +18 | |
| `tests/test_shared.py` | +15 | +7 | |
| `tests/conftest.py` | 未列 | +13 | GBK 替身夹具，两份测试共用 |

## 偏差与发现

- **未在 Windows 上核实**：Ctrl+Shift+V 或右键在旧控制台里配合 `getpass` 能否真正粘贴；`judge --copy` 在 Windows 中文版上的实际输出；旧控制台只显示一行版本号。发版后请 Windows 用户实测，结果写回 Notion 第 71 篇。
- **GBK 替身复现的是根因**：macOS 上按 GBK 解码在主线程直接抛出，Windows 上发生在读取线程里、表现为整份文案算新增；两个用例修复前失败、修复后通过，足以证明修复有效。
- **小标题用例在 macOS 上修复前也会通过**：反斜杠只在 Windows 的 `str(Path)` 里出现，用例的作用是锁定输出。
- **规格多了一处用户决定的改动**：key 来自环境变量时提示修正或删除环境变量，而不是运行 `rulemason key`。
- **发布说明要写**：`judge --copy` 在 Windows 上只检查改过的条目；`rulemason key` 拒绝含控制字符或空白的 key；judge 遇到坏 key 一句话说明来源与修法；Windows 旧控制台不再显示错位的图标。
