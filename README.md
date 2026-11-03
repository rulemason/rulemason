# rulemason

给 AI 编码工具（Claude Code、OpenCode、Cursor、Codex）的共享规则与检查点。它只管三件事：

- **规则**：AI 写方案和代码时要守的写法规矩（九条、各语言落法（Python、React）、界面文案三档、方案写法）。规则只在本仓库维护，每个项目里是一份随项目提交的只读副本，克隆项目的人、云端 agent 与 CI 不装 rulemason 也能读到。
- **检查点**：方案写完、写代码前、写完代码后，AI 按规矩自动检查——判断方案、精简代码、独立审查、lint 与测试。
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
| 在 AI 工具里补项目简介、红线、命令表，或启用判断 | `/rulemason` |

## 第一次接入

在项目根目录运行：

```bash
rulemason init                              # 交互选择工具，列出文件计划，确认一次后写入
rulemason init --tools claude,codex --yes   # 非交互：不提问
```

`init` 只做能确定做对的事：生成规则副本与各工具的入口，补齐方案写法规则、OpenSpec apply / archive 时给 AI 的检查点提示（`config.yaml` 的 `operations`）、ruff / ESLint 继承与项目的检查点规格；改不了的（例如 ruff 配置写了 `select`）只报告，不强行改写。不提交、不推送，不碰计划以外的文件。没有 `openspec/` 时会先询问并代为运行 `openspec init`。

然后在 AI 工具里运行 `/rulemason`，补项目简介、红线（注明出处并逐条确认）与命令表。

## 日常

日常开发走 OpenSpec，检查点由 AI 自动运行，不用记命令：

```txt
/opsx:propose 功能名   方案写完 -> 判断：格式问题 AI 自己改，碰红线的报告给你
/opsx:apply 功能名     写代码前再判断一次，有 block 就停下等你
                       写完 -> 自动精简 -> 独立只读审查 -> ruff -> 测试 -> 前端 lint -> 文案检查
/opsx:archive 功能名   归档，提交
```

自动精简只处理本次改动里的重复、死代码、冗余抽象或过复杂逻辑，保持需求、外部行为与 API 不变；Claude Code 下这一步用内置的 `/simplify`。独立审查者拿不到文件与命令工具，只看提供给它的改动与方案；必须修的问题自动修复并重新审查，不要求你逐条审核代码。

## 看现状

```bash
rulemason check     # 只读，在项目任意子目录运行都可以
```

第一行就是结论和下一步，照着做即可，例如：

```txt
补项目信息：在 AI 工具中运行 /rulemason
接入：运行 rulemason update
日常巡检：一切一致
```

规则副本被改、工具入口缺失、lint 没有继承基础规则、项目还是旧格式时以非 0 退出，可以直接放进 CI：

```yaml
- uses: astral-sh/setup-uv@v6
- run: uv tool install rulemason==0.8.2
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
uv tool upgrade rulemason
rulemason update
```

`update` 直接刷新 rulemason 自己管的规则副本与入口；你自己的文件（ruff、ESLint、`openspec/config.yaml` 等）缺了配置时，它先列出补齐计划，确认后才写，非交互环境里要加 `--yes`。之后在项目里跑一遍 lint 与测试再提交。

## 判断（可选）

判断要求项目在 git 里、已归档至少 3 个 change；`rulemason check` 的「判断」一行会写明还差什么。要启用时在 AI 工具里运行 `/rulemason` 并说明要启用判断，它会整理候选判断规则让你逐条确认。

配 key（在自己的终端里运行，输入不显示，不会进命令历史）：

```bash
rulemason key
```

key 写在 `~/.config/rulemason/env`（权限 600），只在本机，不进任何仓库；环境变量 `TYPESAFE_API_KEY` 优先。

手动运行判断：

```bash
rulemason judge --change 功能名               # 审 openspec/changes/功能名（已归档的也能直接用名字）
rulemason judge --change 功能名 --lint-only   # 只跑正则检查，不联网
rulemason judge --copy                        # 审新增或改过的界面文案（项目配了 openspec/judge.yaml 才有）
rulemason judge --change 功能名 --dry-run     # 打印将要发送的请求，不发送
rulemason judge --template judgments          # 打印启用判断用的模板（judgments、judge、judge_cases）
```

项目代码也可以把引擎当库用：`from rulemason.judge import load_rules, verdict_or_pending`。

## 卸载

```bash
rulemason remove --plan   # 只看计划，不改任何文件
rulemason remove          # 列出计划，确认后卸载；非交互环境加 --yes
```

`remove` 删掉 rulemason 生成的东西：规则副本、各工具的 skill、`.rulemason.yaml`、AGENTS.md / CLAUDE.md 里的 rulemason 标记块、OpenCode 配置里指向 `.rulemason/` 的条目，以及没被改过的 `operations` 提示。ruff、ESLint 还在继承基础规则时，会把这两个文件移到项目的 `lint/` 并改好路径，lint 结果不变。手改过的副本保留；产物写法规则、项目的检查点规格、命令表和红线已是项目内容，只在汇报里列出，不删。本机装的 rulemason 不受影响，不用了再运行 `uv tool uninstall rulemason`。

## 出了问题怎么办

rulemason 往项目里写三类东西，都由它管理，不要手改：

- **规则副本**：`.rulemason/` 与各工具目录下的 `skills/rulemason/SKILL.md`。
- **标记块**：`AGENTS.md`、`CLAUDE.md` 里 `<!-- rulemason:… -->` 与 `<!-- /rulemason:… -->` 之间的内容；块外是你自己的内容，rulemason 不碰。
- **清单**：`.rulemason.yaml`，记录选了哪些工具、rulemason 版本与每个副本的校验值。

| `check` 第一行 | 原因 | 怎么办 |
|---|---|---|
| `接入：运行 rulemason update` | 副本或标记块被手改、入口缺失、配置没补齐 | 运行 `rulemason update`；要改规矩，到本仓库改了发布新版本 |
| `接入：修改 .gitignore，放行 skills/rulemason/` | `.gitignore` 忽略了工具目录，副本提交不上去 | 改成只放行 `skills/rulemason/`；说明单独写一行，git 不支持行尾注释 |
| `接入：运行 rulemason init` | 这个目录（或它所在的仓库）还没接入 | 在项目根运行 `rulemason init` |
| `接入：先修正 .rulemason.yaml` | 清单被改坏，读不出来 | 按提示修正，或删掉它后重新 `rulemason init` |
| `接入：运行 rulemason init 迁移格式` | 项目还是 rulekit 0.5 的格式 | 见下一节 |
| `补项目信息：…` | 项目简介、红线待补，或有旧名残留 | 在 AI 工具里运行 `/rulemason` |

## 从 rulekit 迁移

rulemason 的前身叫 rulekit（0.5.x）。已接入 rulekit 的项目：

```bash
uv tool uninstall rulekit
uv tool install rulemason
rulemason init        # 识别 .rulekit.yaml，列出迁移计划，确认一次后迁移
rulemason check       # 看还有哪些旧名残留
```

迁移把 `.rulekit/`、`.rulekit.yaml`、`skills/rulekit/`、`<!-- rulekit:… -->` 标记块，以及 opencode、ruff、ESLint、项目检查点规格里的 `.rulekit/` 路径换成新名，结果与直接接入相同。旧副本被手改过时迁移停下并列出文件，不写任何东西。

标记块以外的旧名不会被自动修改，`check` 会列出来，在 AI 工具中运行 `/rulemason` 逐处确认后替换：

- 命令表里的 `jev-judge --change <name>` → `rulemason judge --change <name>`
- `.gitignore` 里的 `!.claude/skills/rulekit/` → `!.claude/skills/rulemason/`
- 项目测试里的 `from jev_judge import …` → `from rulemason.judge import …`

key 不用重配：`~/.config/rulemason/env` 不存在时，会读旧位置 `~/.config/jev-judge/env`；也可以运行一次 `rulemason key` 写到新位置。

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
