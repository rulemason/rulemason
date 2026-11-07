# rulemason

中文 · [English](https://github.com/rulemason/rulemason/blob/main/README.en.md)

给 AI 编码工具（Claude Code、OpenCode、Cursor、Codex）的共享规则与检查点。它只管三件事：

- **规则**：AI 写方案和代码时要守的写法规矩（九条、各语言落法（Python、React）、界面文案三档、方案写法），以及碰外部平台与密钥时的纪律（读直接做、写逐次授权、删除或作废交给人，密钥不经过对话）。规则只在本仓库维护，每个项目里是一份随项目提交的只读副本，克隆项目的人、云端 agent 与 CI 不装 rulemason 也能读到。
- **检查点**：方案写完、写代码前、写完代码后，AI 按规矩自动检查——判断方案、精简代码、独立审查、lint 与测试。不走 OpenSpec 的小改动也先读主规格：动到已写的承诺才代起 change 并问你一次，其余直接改、改完跑 lint 与测试；归档时自动并入主规格，不再问。
- **判断**（可选）：用 TypeSafe 的 Jev 模型判断方案是否违反已写下的规矩，输出 pass / review / block；没有 key 时人工逐条判断。

## 安装（每台机器一次）

从 PyPI 安装（需要 [uv](https://docs.astral.sh/uv/)）：

```bash
uv tool install rulemason
rulemason --version
```

## 常用命令

| 什么时候 | 命令 |
|---|---|
| 项目第一次接入，或增减 AI 工具 | `rulemason init` |
| 以后任何时候：升级、补齐缺的配置、恢复被改的副本 | `rulemason update` |
| 看现状与下一步（CI 里也用它） | `rulemason check` |
| 配一次 Jev 的 key（只在启用判断时需要） | `rulemason key` |
| 不再使用：从项目卸载 | `rulemason remove` |
| 手动判断一个方案 | `rulemason judge --change 功能名` |
| 在 AI 工具里补项目简介、红线、命令表、启用判断 | `/rulemason` |
| 诊断全仓，或按模块清理接入前遗留 | `/rulemason cleanup` |

## 第一次接入

在要接入的目录运行（和 `openspec init` 一样，接入的就是这个目录；monorepo 要接入整个仓库，就到仓库根运行，或运行 `rulemason init <仓库根>`）：

```bash
rulemason init                              # 空格勾选工具，看一眼计划摘要（d 展开明细），确认一次后写入
rulemason init --tools claude,codex --yes   # 非交互：不提问
```

`init` 只做能确定做对的事：按项目用到的语言生成规则副本（Go 项目不会收到 Python、React 的落法）、各工具的入口、`.gitignore` 放行、ruff / ESLint 继承；有 `openspec/` 时再补方案写法规则、OpenSpec apply / archive 时给 AI 的检查点提示（`config.yaml` 的 `operations`）与项目的检查点规格。ruff 配置已继承项目里的其他配置时，把基础规则接到继承链末端那份配置里；引用的是旧位置的基础配置副本（例如卸载时移到 `lint/` 的那份）时改回 `.rulemason/` 下的副本。改不了的（例如 ruff 配置写了 `select`、继承了项目外的配置、ESLint 用了认不出的写法）只报告，写明文件、行号、原文与改法。不提交、不推送，不碰计划以外的文件。

没有 `openspec/` 时会问要不要代为运行 `openspec init`；`--yes`、拒绝或本机没有 `openspec` 命令时只接入规则与 lint，装好 OpenSpec 后运行 `rulemason update` 补齐检查点。

写完只给三行：`check` 的结论、需要你处理的事、下一步。AGENTS.md 的项目简介从 README 第一段预填，红线先写「暂无」；然后在 AI 工具里运行 `/rulemason`，核对简介、确认红线（注明出处并逐条确认）与命令表。判断条件满足而本机没有 key 时，init 结尾会问一句要不要配置（key 在 https://typesafe.ai/ 申请）。

## 多个项目放在同一个文件夹

一个文件夹下放着几个项目（例如 `products/` 下的 `app/`、`api/`，各自是 git 仓库）时，到每个项目里分别运行 `rulemason init`，文件夹本身不接入：文件夹没有代码，命令表会写成「无，跳过」，AI 在文件夹里打开时可能照它跳过各项目的 lint 与测试。在这样的文件夹里运行 `init` 或 `check`，会多一行提示。

一次要同时改几个项目时，在主要改的项目里打开 AI 工具，再把相关项目挂进来；检查点按被改文件所属的项目各跑一遍。Claude Code 挂上的目录默认不读它的 `CLAUDE.md`，要设环境变量：

```bash
cd products/app
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../api
```

## 日常

日常开发走 OpenSpec，检查点由 AI 自动运行，不用记命令：

```txt
/opsx:propose 功能名   方案写完 -> 判断：格式问题 AI 自己改，碰红线的报告给你
/opsx:apply 功能名     写代码前再判断一次，有 block 就停下等你
                       写完 -> 自动精简 -> 独立只读审查 -> ruff -> 测试 -> 前端 lint -> 文案检查
/opsx:archive 功能名   归档，提交
```

自动精简只处理本次改动里的重复、死代码、冗余抽象或过复杂逻辑，保持需求、外部行为与 API 不变；Claude Code 下这一步用内置的 `/simplify`。独立审查者拿不到文件与命令工具，只看提供给它的改动与方案；必须修的问题自动修复并重新审查，不要求你逐条审核代码。

已有大量代码的项目接入后，ruff 与前端 ESLint 往往报出很多改动前就有的问题；先在 AI 工具里运行 `/rulemason` 建立基线（ruff 自动修复 import、声明框架写法，其余按文件记为「接入前遗留」；ESLint 按文件写各自放开的规则与复杂度上限，不整条关规则、不提高全局上限；都等你确认），之后检查点只修每次改动新引入的问题。

要清这些遗留，运行 `/rulemason cleanup`。不带模块名只诊断全仓（遗留条目、临时统计的软指标、每个模块抽几个文件看精简潜力），不改文件。收尾先列出还没做完的模块，最后一行给出下一步：下一条清理命令，或先提交哪些路径。做完一个模块后，收尾指出下一个，不自动开始改。带模块名只修该模块，先列计划等你确认，可以只同意其中几条。进度不另存文件：看遗留条目还在不在，以及你的提交说明是不是 `refactor(cleanup): <模块>`。

## 看现状

```bash
rulemason check     # 只读，在项目任意子目录运行都可以
```

第一行就是结论和下一步，照着做即可，例如：

```txt
补项目信息：在 AI 工具中运行 /rulemason
接入：运行 rulemason update
接入：手动修改 web/.eslintrc.json（rulemason update 改不了）：……
日常巡检：一切一致
```

尚未接入、规则副本被改或与本机版本应生成的不一致、工具入口缺失、lint 没有继承基础规则或引用的基础配置不存在时以非 0 退出；只有版本号落后、副本内容相同时照常 0 退出。可以直接放进 CI（CI 钉的版本与项目记录一致，不会因本机升级而失败）：

```yaml
- uses: astral-sh/setup-uv@v7
- run: uv tool install rulemason==0.8.27
- run: rulemason check
```

### 给 AI 与脚本

```bash
rulemason check --json          # 结构化结果：next.code 是稳定的动作代码，text 是上面的报告全文；退出码同上
rulemason init --plan [--json]  # 只列接入计划：不写文件、不提问、不运行 openspec init
rulemason update --dry-run [--json]   # 只列升级与补齐计划，不写文件
```

`/rulemason` 读的就是 `check --json`；AI 替你接入前会先用 `init --plan` 给你看计划。

## 升级

```bash
uv tool upgrade rulemason   # 升级本机安装的 rulemason：每台机器一次
rulemason update            # 刷新项目里提交的副本与入口：每个项目一次，改动随项目提交
```

分两步，是因为一台机器上可能有好几个项目，而项目里的副本要进版本库：只需一个人运行 `rulemason update` 并提交，其他人拉取后只升级本机即可，不用再运行 `update`。两步也可以写成一行：`uv tool upgrade rulemason && rulemason update`。

`update` 直接刷新 rulemason 自己管的规则副本与入口；副本只保留本项目用得上的文件，升级到 0.8.4 之后第一次 `update` 会删掉用不到的（例如没有 React 的项目里的 `react.md`），项目后来加了语言也由它补上。你自己的文件（ruff、ESLint、`openspec/config.yaml` 等）缺了配置时，它先列出补齐计划，确认后才写，非交互环境里要加 `--yes`。之后在项目里跑一遍 lint 与测试再提交。

## 判断（可选）

配了 key 不等于启用判断：启用要在 AI 工具里运行 `/rulemason` 并说明，由它整理判断规则、你逐条确认；判断审 OpenSpec 方案、界面文案，以及不走 OpenSpec 的直接改动的「改动说明」（见下）。判断要求项目在 git 里、已归档至少 3 个 change；`rulemason check` 的「判断」一行会写明还差什么。

配 key（在自己的终端里运行，输入不显示，不会进命令历史）：

```bash
rulemason key
```

key 写在 `~/.config/rulemason/env`（权限 600），只在本机，不进任何仓库；环境变量 `TYPESAFE_API_KEY` 优先。

判断默认直连 Typesafe。直连被按地区拒绝（451）时，会自动改用本机代理，并提示一句；Linux 与 WSL 只认 `HTTPS_PROXY` 等环境变量，桌面系统里设的代理读不到。

手动运行判断：

```bash
rulemason judge --change 功能名               # 审 openspec/changes/功能名（已归档的也能直接用名字）
rulemason judge --change 功能名 --lint-only   # 只跑正则检查，不联网
rulemason judge --copy                        # 审新增或改过的界面文案（项目配了 openspec/judge.yaml 才有）
rulemason judge --change 功能名 --dry-run     # 打印将要发送的请求，不发送
rulemason judge --template judgments          # 打印启用判断用的模板（judgments、judge、judge_cases）
rulemason judge --direct 说明.md              # 审一份直接改动说明（AI 在不走 OpenSpec 改代码前自己写、自己运行）
```

**直接改动的红线**：不走 OpenSpec 的改动里，改到项目指令「红线」一节下「先走 OpenSpec 的区域」的，会先起一个最小 OpenSpec change，用现有的方案判断对照红线；这一层不依赖判断层。其余改了代码逻辑的改动，判断启用后会让 AI 先把依据写成一份固定四段的说明（要做什么、改哪些文件、主规格与检索命中、判路与理由，不贴代码，不发送源码）交判断。通用规则 `direct-route-respects-specs` 查这次改动有没有绕开主规格，红线规则可以在启用判断时问你是否也用在直接改动上。现在只给 review、不拦截，跑一段时间看分数再收紧。

项目代码也可以把引擎当库用：`from rulemason.judge import load_rules, verdict_or_pending`。

## 卸载

```bash
rulemason remove --plan   # 只看计划，不改任何文件
rulemason remove          # 列出计划，确认后卸载；非交互环境加 --yes
```

`remove` 删掉 rulemason 生成的东西：规则副本、各工具的 skill、`.rulemason.yaml`、AGENTS.md / CLAUDE.md 里的 rulemason 标记块、OpenCode 配置里指向 `.rulemason/` 的条目，以及没被改过的 `operations` 提示。ruff、ESLint 还在继承基础规则时，会把这两个文件移到项目的 `lint/` 并改好路径，lint 结果不变。手改过的副本保留；产物写法规则、项目的检查点规格、命令表和红线已是项目内容，只在汇报里列出，不删。本机装的 rulemason 不受影响，不用了再运行 `uv tool uninstall rulemason`。卸载后再接入时，`lint/` 下没改过的基础配置会改回引用 `.rulemason/` 下的副本，旧文件留给你确认后删除。

## 出了问题怎么办

rulemason 往项目里写三类东西，都由它管理，不要手改：

- **规则副本**：`.rulemason/` 与各工具目录下的 `skills/rulemason/SKILL.md`。
- **标记块**：`AGENTS.md`、`CLAUDE.md` 里 `<!-- rulemason:… -->` 与 `<!-- /rulemason:… -->` 之间的内容；块外是你自己的内容，rulemason 不碰。
- **清单**：`.rulemason.yaml`，记录选了哪些工具、rulemason 版本与每个副本的校验值。

| `check` 第一行 | 原因 | 怎么办 |
|---|---|---|
| `接入：运行 rulemason update` | 副本或标记块被手改、入口缺失、配置没补齐 | 运行 `rulemason update`；要改规矩，到本仓库改了发布新版本 |
| `接入：修改 .gitignore，放行 skills/rulemason/` | `.gitignore` 忽略了工具目录，副本提交不上去 | 改成只放行 `skills/rulemason/`；说明单独写一行，git 不支持行尾注释 |
| `接入：运行 rulemason init` | 这个目录还没接入 | 在要接入的目录运行 `rulemason init` |
| `接入：手动修改 <文件>（rulemason update 改不了）：…` | lint 配置有 rulemason 不替你决定的写法：ruff 写了 `select`、继承了项目外的配置、旧副本被改过、ESLint 写法认不出或重复引入基础规则 | 按 `rulemason check` 报告「接入 lint 继承」下写明的文件、行号与做法改，改完照提示运行 `rulemason update` 或 `rulemason check` |
| `接入：先修正 .rulemason.yaml` | 清单被改坏，读不出来 | 按提示修正，或删掉它后重新 `rulemason init` |
| `补项目信息：…` | 项目简介、红线待补 | 在 AI 工具里运行 `/rulemason` |

## 参与修改

改共享规则会影响所有接入项目：在本仓库开 OpenSpec change，在受影响的项目里验证，发布新 tag 后各项目运行 `rulemason update`。

启用提交前钩子，拦截本机绝对路径（每个 clone 一次）：

```bash
git config core.hooksPath .githooks
```

本地开发：

```bash
uv sync
uv run ruff check .
uv run pytest
```

## 许可证

[Apache-2.0](LICENSE)。版权声明见 [NOTICE](NOTICE)。
