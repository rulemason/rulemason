# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- 子目录边界已有：`src/rulemason/shared.py:301` 的 `boundary_reason` 对含 `.git` 的子目录返回「另一个仓库」，对含 `.rulemason.yaml` 的返回「另一个 rulemason 项目」；`scan`（`shared.py:314`）返回 `Scan(files, skipped)`。init 的 `build_plan`（`src/rulemason/init.py:713`）只用 `list_files`（`shared.py:349`），拿不到 `skipped`。
- 语言识别：`check.identify`（`src/rulemason/check.py:316`）只认 Python（`.py` 文件，`check.py:206`）与 JS/TS（`package.json`），都不是时写「未识别」（`check.py:327`）。
- 已有同类提示：init 在仓库子目录运行时把 `repo_root_hint` 加进 `plan.tips`（`init.py:951`）；check 的 `render` 在没有 git 时加一行「- 提示：…」（`check.py:1117`）；`--json` 输出 `facts`（`check.py:1135`）。
- 文件夹接入后的命令表：在 scratchpad 搭 `A/` 不是 git、`b/ c/ d/` 各是 git 仓库并各自接入，再在 `A/` 运行 `rulemason init --tools claude,codex --yes`，`A/AGENTS.md` 命令表 ruff 与测试都写「无，跳过」，`check` 识别表「跳过：b（另一个仓库）、c（另一个仓库）、d（另一个仓库）」（可复现）。
- 共享检查点：`rules/workflow-gates.md:5` 定义「命令表的〈名称〉指项目指令里『本项目命令表』中名称相同的那一行」，没说哪个项目。
- Claude Code：启动时加载当前目录及以上各级的 CLAUDE.md，子目录的 CLAUDE.md 在读写其中文件时才加载；`--add-dir` 的目录默认不加载 CLAUDE.md，设 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 后加载（https://code.claude.com/docs/en/memory.md）。官方推荐在要改的子目录启动，用 `--add-dir` 挂上兄弟仓库（https://code.claude.com/docs/en/large-codebases.md）。Codex 的 `--add-dir` 是否加载该目录的 AGENTS.md：未核实。
- OpenSpec 1.16.0 的 workset 暂停了用 Claude Code、Codex 打开多个目录，原因是改动落在哪个项目说不清（`@fission-ai/openspec/dist/core/openers.js` 第 8–15 行注释）。

## Goals / Non-Goals

**Goals:**
- 在文件夹里接入或巡检的人看到一句提示，知道该到各项目里接入、怎么同时改几个项目。
- AI 在一次会话里看到几张命令表时，有一句规则说清用哪张。

**Non-Goals:**
- 不判断这个文件夹「确实」不是项目，只按可观察的两条特征提示。
- 不让 `update`、`remove` 输出这行提示。

## Decisions

1. **判断条件只用两条：识别不出语言，且 `skipped` 里有「另一个仓库」或「另一个 rulemason 项目」。** 判断函数 `folder_hint(scanned)` 放在 `shared.py`，返回提示文字或 None，init 与 check 共用；语言判断沿用 check 的 Python 与 JS/TS 两条，抽成共享函数供两边调用。否决再加「除生成文件外没有别的文件」：文件夹里常有 README、`.DS_Store`、脚本，这条会让真正的文件夹也不提示。否决只看「另一个 rulemason 项目」：b、c、d 还没接入时最需要提示，那时它们只被识别为「另一个仓库」。
2. **init 的提示在 `build_plan` 里加：`list_files` 改为 `scan`，同一次扫描拿 `files` 与 `skipped`。** `update` 自己组计划、不经过 `build_plan`（`src/rulemason/update.py:102`），因而不受影响。否决在 `init.run` 里再扫一次：多一次 `git ls-files`，没有收益。
3. **check 的提示放进 `facts`，键为「提示」，紧跟「跳过」一行。** 这样 `--json` 的 `facts` 也带上它，AI 读 JSON 也能看到。否决像「没有 git」那样只在 `render` 里加：`--json` 读不到。
4. **提示文字写成条件句，并点名工具的通用做法：** 形如「这里有独立项目 b、c、d；如果这里只是放项目的文件夹，建议到各项目里分别运行 rulemason init，同时改几个项目时在主要改的项目里打开 AI 工具，再挂上相关项目（如 `--add-dir`）」。否决写死 `claude --add-dir`：共享输出不偏向一个工具，Cursor 用多根工作区。环境变量写进 README，不放进提示：提示要短，变量只对 Claude Code 有用。
5. **「本项目」的定义加在 `rules/workflow-gates.md` 第 5 行那一段末尾，一句话。** 那段本来就在定义「命令表」「红线规则」「额外步骤」指什么。否决在各项目 AGENTS.md 的命令表上方另写：要改模板与所有已接入项目，且同一件事住两处。否决新开一节：一句话的事，单独成节让检查点变长。

## Risks / Trade-offs

- [Go、Rust 等未识别语言的项目带子模块时也会出现提示] → 提示写成「如果这里只是放项目的文件夹」，不改变计划与退出码，读到的人可以忽略。
- [共享正文变化让所有接入项目在 `update` 前显示副本版本落后] → 这是每次发版的常态，发布说明写明这一句的内容。
- [AI 仍可能用错命令表] → 规则只能说清，不能强制；在 scratchpad 的 `A/b/c` 布局用 Claude Code 实测一次在 `A/` 改 `b/` 的文件，结果写进 verification.md。

## Migration Plan

1. 改 `shared.py`、`init.py`、`check.py`、`rules/workflow-gates.md`、`README.md`，补测试，跑 ruff 与测试。
2. 在一个已接入项目运行 `rulemason update`，确认新副本只多这一句、`check` 一致；在 scratchpad 的文件夹布局验证 init 与 check 的提示。
3. 发版，发布说明写明文件夹提示与「本项目」的定义。

回滚：`uv tool install rulemason==<上一版>` 后在接入项目运行 `rulemason update`，副本回到旧文字；本次不改任何文件格式与清单结构。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/shared.py` | `folder_hint()`、共享的语言判断 | +18 |
| `src/rulemason/check.py` | 识别表加「提示」；语言判断改用共享函数 | +4 / −2 |
| `src/rulemason/init.py` | `build_plan` 改用 `scan` 并追加提示 | +4 / −1 |
| `rules/workflow-gates.md` | 第 5 行末尾一句 | +1 / −1 |
| `README.md` | 「多个项目放在同一文件夹」一小节 | +12 |
| `tests/test_shared.py` | `folder_hint` 各条件 | +30 |
| `tests/test_init.py` | 文件夹提示出现、不改计划 | +25 |
| `tests/test_check.py` | 提示出现与不出现、退出码与第一行不变、`--json` 带上 | +30 |
