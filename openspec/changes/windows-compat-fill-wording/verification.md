# Verification：windows-compat-fill-wording

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。本机是 macOS，Windows 行为只能用替身测试，未在真实 Windows 上核实的部分在文末列出。

## 写代码前检查点

`rulemason judge --change windows-compat-fill-wording`：pass 3 / review 0 / block 0。

## 1. 自动精简与独立审查

**自动精简（`/simplify`，四路并行）**，只采纳行为保持的修改：

- 采纳：openspec 用例并入原有 `test_new_dir_agrees_to_openspec_init`，用 `subprocess.run` 的 spy 断言以 which 结果启动，删去自造的 `openspec.cmd` 脚本；Windows 控制台替身简化，用 `windows_ansi.__wrapped__()` 绕过缓存；空行修正。
- 跳过：`import ctypes` 改回函数内导入（当时的理由是启动快约 3 毫秒，属于性能优化，按规矩不采纳；后来独立审查以正确性理由提出，已改，见下）；测试引用 `update.FILL_TITLE` 而不写原文（测试有意锁定输出文字）。
- 修复深度方向：`git` 以名字启动在 Windows 上会补 `.exe`，不受影响；`select.py` 的转义只在有 termios 时运行；无需改动。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：block 1，review 7，全部修复：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | review：skill 只在巡检一节写了补齐属于升级，`update` 一行没写；认定「新增条目是基础版」用「与基础版的差异一致」，但 check 只查基础条目有没有缺，项目追加的不报 → `update` 一行补半句；认定依据改为 update 输出的补齐计划，或与安装包基础版逐字比对 |
| 正确性 | review：Windows 上 `os.open` 默认文本模式，与 `fdopen` 各转一次换行会叠成 `\r\r\n`、每写一次空行翻倍（未核实）→ 并上 `O_BINARY`；顶层 `import ctypes` 在缺 libffi 的 Python 上会让整个包导入失败 → 改回函数内导入；试运行没有补齐计划时也说「会询问是否补齐」→ 只在有补齐计划时说；`GetStdHandle` 未设返回类型 → 设 `restype` |
| 安全 | pass（`--tools` 先经白名单校验，传给 `.cmd` 的参数都是固定值） |
| 代码质量 | review：测试替身用 `or` 串副作用 → 改为具名函数与小类 |
| 测试 | review：缺「win32 且不是终端时不调控制台接口」「只试一次」→ 新增两条 |
| 变更卫生 | block：proposal 写了接入项目的真名 → 改为「某接入项目」 |

第二轮：block 0，review 4。按规则修完后只跑 ruff 与测试，不审第三轮：

- 句柄设了 `restype` 但传回 `GetConsoleMode` / `SetConsoleMode` 时仍按 int 传 → 包成 `ctypes.c_void_p(handle)`。
- skill 的定位命令写死了 POSIX 下 uv tool 的目录层级 → 改用 `find "$(uv tool dir)/rulemason" -path "*_shared/openspec-base/*.yaml"`（本机实测能找到两份基础版），找不到时以 `rulemason update --dry-run` 的补齐计划为准。
- design 决策 4、5 与 tasks 2.2 没跟上新依据 → 同步。
- key 测试断言 `"600" not in out` 可能被临时目录里的数字误伤 → 改为 `"权限 600" not in out`。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：514 passed（改动前 504）。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案（命令行输出文字由测试锁定）。

## 6. 额外步骤

改了 `skills/`，在项目甲、乙、丙用本分支开发版与已安装的 0.8.13 对比 `update --dry-run --json`：`fill` 与 `notes` 完全相同，开发版只多出 skill 副本与 `.rulemason.yaml` 的刷新；文字输出结尾为新说法。

## 与 design 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/key.py` | +8 / −3 | +8 / −3 | |
| `src/rulemason/init.py` | +3 / −2 | +4 / −2 | |
| `src/rulemason/shared.py` | +20 / −2 | +19 / −2 | |
| `src/rulemason/update.py` | +4 / −3 | +8 / −5 | 多出没有补齐计划时的另一种结尾；未超出一倍 |
| `skills/rulemason/SKILL.md` | +3 / −1 | +2 / −1 | 巡检一节的说明写成一条长句 |
| `tests/test_key.py` | +20 | +10 | |
| `tests/test_init.py` | +15 | +9 | 并入原有用例 |
| `tests/test_banner.py` | +25 | +68 / −1 | 两轮审查补「不是终端不调接口」「只试一次」与控制台替身类；超出一倍，原因如上 |
| `tests/test_update.py` | +10 / −2 | +15 / −3 | |
| `tests/test_templates.py` | +5 | +9 | |

## 偏差与发现

- **未在 Windows 上核实**：用完整路径启动 `openspec.cmd`、`SetConsoleMode` 开启 ANSI、`O_BINARY` 下 key 文件的换行。发布说明请 Windows 用户实测 `rulemason key`、代跑 `openspec init` 与旧控制台显示，结果回写 Notion 第 71 篇。
- **Python 3.12.0 的 `shutil.which`** 在 Windows 上可能返回 npm 生成的无扩展名脚本（3.12.1 修复），已写进 design Risks（未核实）。
- **`import ctypes` 的位置**：精简时以性能理由不采纳改回函数内；独立审查以「缺 libffi 的 Python 会整体导入失败」的正确性理由提出后改回函数内，函数 docstring 写明原因。
- **发布说明要写**：Windows 三处修复；update 补齐计划与试运行结尾的新说法；skill 认出升级产出的方法。
