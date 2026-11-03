# Design

## Context

- `init.ask_tools` 打印编号清单、读一行输入；`default_tools` 按已有工具目录预勾；`render_plan` 把新增 / 修改 / 删除逐个打印；`report` 写入后打印整份 `check` 报告；`ensure_openspec` 在没有 `openspec/` 时问一句，`--yes` 直接代跑 `openspec init`。
- `shared.generated_files(tools)` 固定复制 `COPIED_SHARED` 的 7 个文件；`check.copy_issues` 已按清单记录的集合比对，`language_rules` 已按语言决定入口块引用哪几份落法；`update.run` 复用 `plan_copies`，并删除「清单记录过、不再生成且未改」的副本。
- `check.judge_label` 给出判断一行；`PENDING_MARKS` 决定下一步是否指向 `/rulemason`；`key.run` 是不回显输入的唯一实现。
- `banner.py` 有 `_paint` 与颜色常量，`COMMANDS` 是不带参数时的常用命令表。仓库没有任何 `termios` 用法，也没有第三方终端库。

## Goals / Non-Goals

**Goals:**

- `init` 交互路径：选工具、看计划、看结果三步都只给必要信息；非交互与 `--plan` / `--json` 输出不变。
- 副本、占位符、`.gitignore`、key 四件事不再把活留给用户。
- 不加依赖；Windows 与非终端有退路。

**Non-Goals:**

- `update`、`check`、`remove` 的输出格式；识别与检查口径（init-ux-2）；启动画面图形。

## Decisions

### 1. 选择器用标准库 `termios` + `tty` 自写，Unix 以外退回编号输入

新建 `src/rulemason/select.py`：`choose(options, checked, detected)` 把终端切到 cbreak 模式读单键，上下键（`\x1b[A/B`）或 j / k 移动，空格切换，`a` 全选，回车确认，`q` 或 Ctrl-C 取消；每次按键重画 N 行（光标上移 N 行再输出）。`termios` 导入失败（Windows）或标准输入不是终端时抛 `Unsupported`，`init.ask_tools` 捕获后走现在的编号输入。约 70 行。

**否决：** 用 `questionary` 或 `prompt_toolkit`。启动画面时定过不加依赖；这两个库会连带装入十几个包，只为一个四选项的列表。

**否决：** 用 `curses`。整屏接管，和启动画面、后面的计划输出不好衔接；Windows 同样没有。

### 2. 计划摘要在交互确认时显示，`d` 展开后再问一次

`render_plan` 拆成 `render_summary`（分类计数 + 修改 / 删除逐个 + 需要处理 + 未提交数）与原 `render_plan`（完整清单）。`print_plan` 交互时用摘要，提示 `[y/N/d]`；读到 `d` 打印完整清单再问一次；`--plan` 与 `remove` 仍用完整清单。分类按路径前缀：`.rulemason/rules/` → 规则副本，`skills/rulemason/` → skill，`.rulemason/lint/`、ruff / ESLint / `config.yaml` / 规格 → 配置，`AGENTS.md` / `CLAUDE.md` / `opencode.jsonc` / `.gitignore` / 清单 → 入口。

**否决：** 展开后直接视为看过、不再问。少一次按键，但用户看完明细后没有反悔的机会。

### 3. 写入后只给结论与待办

`report` 改为：`check` 第一行、`plan.notes` 转成「需要你处理」（ESLint 的 note 附要粘贴的 `import` 与 `{ rules: rulemasonBase }` 两段）、下一步。整份报告由 `rulemason check` 提供。颜色函数 `_paint` 与常量从 `banner.py` 移到 `shared.py`（`paint(text, code)`，内部看 `NO_COLOR` 与 `isatty`），`banner` 与 `init` 共用。

**否决：** 保留整份报告但折叠。终端没有折叠；看结论的人只要第一行，要细节的人会跑 `check`。

### 4. 没有 OpenSpec 时分层接入，`--yes` 不代跑 `openspec init`

`ensure_openspec` 改为返回「是否有 openspec」：交互仍问；`--yes`、拒绝或命令不存在时返回 False，`plan_fill` 按 `shared.has_openspec` 跳过 `plan_artifact_rules`、`plan_operations`、`plan_workflow_spec`，AGENTS.md 的 workflow-gates 块改用「未接 OpenSpec」版本模板（说明检查点未启用与补齐方法），结尾加一行说明。`update` 发现 `openspec/` 出现后，按现有补齐逻辑写入缺的三样并把块换回正常版本。为了让这种项目 `check` 退出 0，`check` 在没有 `openspec/` 时不算「接入 产物写法」层，识别表的 openspec 一行写明「方案检查点未启用」——这是 init-ux-2「检查点未启用」那一项的最小版，提前做了。

**否决：** 没有 `openspec/` 就停止。Go 项目、脚本项目拿不到规则和 lint，启动画面说的「三件事」一件都做不了。

**否决：** 保持 `--yes` 代跑。脚本和 CI 里悄悄写入 24 个文件，是这次反馈里最意外的一条。

### 5. 副本按语言生成，清单是副本集合的唯一依据

`check.copied_rules(root, files)` 按 `has_python`、`react_dirs`、已有的 ESLint 配置、前端目录与「判断已启用」选取 `COPIED_SHARED` 的子集，`generated_files(tools, rules)` 据此生成；`code-style`、`workflow-gates`、`README` 固定。ESLint 基础配置在有 React 目录**或已有 ESLint 配置**时复制：有的前端不是 React 却继承了 eslint-base（实施时发现，比方案写的「只随 React」多一个条件）。`check.copy_issues` 本来就按清单比对，不用改；`update` 用同一函数重算，多出的文件靠现有「不再生成且未改的旧副本」逻辑删除。README 模板列出的副本清单改成按实际生成的文件写。

**否决：** 全部复制、只是入口不引用。36K 里一大半用不上，用户问「这工具给我做了什么」时答不上来。

### 6. 预填简介，红线写「暂无」，保留命令表占位

新建 `AGENTS.md` 时读 README（`README.md` / `README.rst` / `README`），取第一个非标题、非徽章、非空的段落，按句号 / 问号 / 感叹号切到两句。红线一节写「暂无」。`PENDING_MARKS` 不变，命令表的「自动识别，请确认」保证 `check` 下一步仍是 `fill_project_info`；skill 第二阶段把第 1 步改为核对预填简介，第 2 步照旧问一次红线。

**否决：** 红线也留占位。AI 第一次读到的项目指令里就有「待补充」，和预填简介的目的相反；问一次红线交给 skill 做更合适。

### 7. key 引导只在三个条件同时满足时问一次

写入完成后：交互且无 `--yes`、`judge.find_key()` 为空、`check.judge_label` 判定条件已满足 → 问一句，y 则调用 `key.run()`；否则按条件给一行提示。所有提示带申请地址。`judge_label` 在条件满足且无 key 时加「本机未配置 key：运行 rulemason key」。`banner.COMMANDS` 加 `("rulemason key", "配置判断用的 Jev key（本机一次）")`。

**否决：** 每次 init 都问。key 是机器级的，项目级的 init 每次都问会很快被当成噪音。

### 8. `.gitignore` 放行作为计划里的修改

`plan_fill` 新增 `plan_gitignore`：skill 副本会被忽略时，在 `.gitignore` 末尾追加说明行与放行链：git 不允许在父目录被排除时再包含子项，所以从被忽略的那一级目录起，每一级先 `!目录/` 再 `目录/*`，最后 `!<副本目录>/` 与 `!<副本目录>/**`（文件级规则如 `*.md` 也能放行）；`.rulemason/` 与各 skill 目录都按此处理。走同一次确认；写入后 `check` 的 `fix_gitignore` 不再出现。

**否决：** 继续只在 `check` 里提示。这是能确定做对的事，让用户手改一行文件没有意义。

## Risks / Trade-offs

- [cbreak 模式下程序异常退出，终端留在无回显状态] → 用 `try/finally` 恢复 `termios` 设置，Ctrl-C 也走 finally。
- [方向键转义序列在个别终端不是 `\x1b[A`] → 同时接受 j / k；读到不认识的序列忽略。
- [README 第一段不是简介（比如一行 logo 图片或徽章）] → 跳过含 `![`、`<img`、`http` 开头的段落；仍取不到就保留占位。
- [按语言复制后，现有接入项目下次 `update` 会删掉用不到的副本，用户以为丢了东西] → `update` 汇报里已有「删除」一节；README 升级一节写明这一点。
- [`copy-voice` 的条件「有前端目录」在纯后端项目为假，之后启用判断时才补] → `update` 在判断启用后会补上，启用判断的 skill 步骤提醒先 `update`。
- [终端颜色在 `init` 被管道接走时污染日志] → `paint` 只在标准输出是终端且无 `NO_COLOR` 时上色。

## Migration Plan

1. 本仓库实现与测试；在临时目录各试一次：交互 init（含 `d` 展开、空格选工具）、`--yes` 无 openspec、Go 项目、有 README 的项目、`.gitignore` 挡副本。
2. 三个接入项目临时 worktree 跑 `update --dry-run`，确认只多出「删除用不到的副本」与 skill 副本刷新；`check` 退出码不变。
3. 归档，发 0.8.4。

回滚：revert；接入项目再跑一次 `update` 会把副本集合补回全量。

## 文件与估计行数

| 文件 | 变化 | 估计行数 |
|---|---|---|
| `src/rulemason/select.py` | 新增：单键多选 | +70 |
| `src/rulemason/init.py` | 选择器接入、摘要、收尾、分层、预填、gitignore、key 引导 | +120 / −40 |
| `src/rulemason/shared.py` | 按语言生成副本、`paint` | +30 / −5 |
| `src/rulemason/check.py` | 判断一行加 key 提示 | +6 |
| `src/rulemason/update.py` | 调用新的 `generated_files` | +4 / −2 |
| `src/rulemason/banner.py` | 颜色函数迁出、常用命令加一行 | +3 / −12 |
| `src/rulemason/templates/` | AGENTS 模板红线「暂无」、workflow-gates 块的未接 OpenSpec 版本、README 副本清单 | +15 / −3 |
| `skills/rulemason/SKILL.md` | 第二阶段第 1、4 步 | ~4 |
| `README.md` | 第一次接入、升级一节 | ~10 |
| `tests/test_select.py` | 新增：按键序列驱动 | +60 |
| `tests/test_init.py`、`test_update.py`、`test_check.py`、`test_banner.py`、`test_templates.py`、`test_shared.py` | 新场景用例与断言更新 | +140 / −30 |
