---
name: rulemason
description: 在已运行 rulemason init 的项目里补齐需要理解项目的部分（项目简介、红线、命令表确认），解读 rulemason check 的结果，或在用户要求时启用判断、做存量清理。用户要接入、补全、巡检 rulemason、启用判断或批量清理既有违规时使用。
---

# /rulemason：补项目信息、巡检、启用判断与存量清理

rulemason 管三件事：**规则**（写法规矩）、**检查点**（方案与代码前后的自动检查）、**判断**（用 Jev 判断方案是否违反规矩，可选）。共享规则只在 rulemason 仓库编辑；接入（生成规则副本、工具入口、基础配置）由 `rulemason init` 完成，升级与补齐由 `rulemason update` 完成。本 skill 只做需要理解项目的事。

## 不可违反

- **先识别后动手**：第 1 步 `rulemason check --json` 的 `next.code` 决定做什么，不凭印象判断阶段，也不按文字措辞匹配。
- **一次只做一件事**：做之前列出要新增、修改的文件，用户同意后才写。
- **红线与判断规则由用户确认**：候选要注明出处（README、`openspec/config.yaml` 的 context、某个已归档方案，或「rulemason 常见红线」及触发它的文件）；没确认的不写。
- **不改 rulemason 标记块**：`<!-- rulemason:… -->` 与 `<!-- /rulemason:… -->` 之间的内容、`.rulemason/` 与各工具的 skill 副本都是生成的，由 `rulemason update` 刷新，本 skill 不改。
- **不提交、不推送**：工作区里用户已有的改动一律不碰；汇报末尾列出本次改了哪些文件。
- **巡检只报告**：日常巡检不改任何文件；唯一的例外是用户确认的 ruff 基线计划与 ESLint 基线计划（见「5. 建立 ruff 基线」「6. 建立 ESLint 基线」）。

## 1. 识别

1. 先确认本机有 `rulemason` 命令，且 `rulemason --version` 不低于项目 `.rulemason.yaml` 里 `rulemason:` 记录的版本；没有命令或版本更低时，给出安装命令 `uv tool install rulemason`（已装旧版本时用 `uv tool upgrade rulemason`；需要与清单记录的版本一致时用 `uv tool install --force rulemason==<版本>`），然后停下。
2. 在项目根目录（或任意子目录）运行 `rulemason check --json`，把 `text`（报告全文）原样放进汇报；`next.action` 是给人看的下一步，`next.code` 决定这次做什么。命令以非 0 退出且输出不是 JSON 时（例如「rulemason check 失败：openspec/config.yaml 不是合法的 YAML…」），原样转述这条提示，请用户修正对应文件，然后停下：

| `next.code` | 这次做什么 |
|---|---|
| `init` | 提示用户在项目根运行 `rulemason init`（没有 `openspec/` 时它会先询问）。停下，项目已归档再多 change 也一样。用户要你代为接入时，先运行 `rulemason init --plan` 把计划给用户看（不写任何文件），用户同意并选定工具后再运行 `rulemason init --tools <所选> --yes` |
| `fix_manifest` | 说明清单读不出来的原因（见 `layers` 的「接入 工具入口」），请用户修正，或删掉后重新 `rulemason init`。停下 |
| `fix_gitignore` | 列出要改的 `.gitignore` 规则（只放行 `skills/rulemason/`，说明单独写一行），用户确认后修改，再运行 `rulemason check --json` |
| `update` | 提示用户运行 `rulemason update`；可先用 `rulemason update --dry-run` 给用户看计划。它列出「补齐计划」时，在终端里运行会询问是否补齐，由用户答 y；非交互环境（包括你代为运行）才加 `--yes`。补齐写进项目文件的内容属于这次升级，提交时与副本一起带上。停下 |
| `manual_lint` | 接入只剩 `rulemason update` 改不了的 lint 项：`next.action` 写了要改的文件与摘要，把 `layers` 的「接入 lint 继承」里各项的行号、原文与做法列给用户；有几种做法时由用户选，用户同意后照改，再运行 `rulemason check --json`。不要让用户重跑 update |
| `fill_project_info` | 第 2 步 |
| `upgrade_machine` | 本机 rulemason 比项目记录的旧：按上面第 1 条给出安装命令。停下 |
| `none` | 第 3 步；用户说要启用判断时做第 4 步。`next.action` 附有「版本号落后」时，提一句可运行 `rulemason update` 更新记录 |

## 2. 补项目信息

先列文件计划（要新增、修改的文件，修改写明改哪一段；「其余 N 个未提交改动不变」），用户同意后再写。

1. **项目简介**：`rulemason init` 已从 README 第一段预填了简介；把它念给用户核对，用户要改才改。仍是「待 /rulemason 补充」时按 README 与代码写一两句话替换。
2. **红线候选**：init 把红线一节写成「暂无」，这里仍要问一次：从 README、`openspec/config.yaml` 的 `context` 里找出「绝对不能做的事」，每条注明出处；再按项目里实际存在的东西提常见红线，出处写「rulemason 常见红线（触发文件）」，没有对应的东西就不提：
   - 有数据库访问（ORM、迁移目录、数据库连接配置）：「线上数据库只读，迁移与改数据由人执行」
   - 有部署脚本或 CI 发布流程：「不代为发布到生产，发布由人触发」
   - 有区分生产环境的配置（如 `.env.production`、`settings/prod.*`、`config/production.*`）：「生产凭据只给人用，AI 会话不使用生产写权限」

   所有候选逐条请用户确认、改写或删除；没有找到也要问用户一句。确认的替换「暂无」写进「## 红线（不可违反）」；用户说没有就保留「暂无」。`context` 本身不改。
3. **样板与豁免**：在 Code style 标记块之后写本项目样板文件路径、语言落法位置与 ruff 豁免文件。
4. **命令表**：向用户展示「本项目命令表（自动识别，请确认）」中的命令，按用户确认或修改后的内容写入，并去掉「自动识别，请确认」。判断与文案检查保持「可选，未启用」。
5. **项目工作流规格**：init 或 update 汇报 `openspec/specs/workflow-gates/spec.md` 需要合并时，检查是否已有「Apply 后自动精简并审查」或语义等价的 requirement；缺失则按 rulemason 的 workflow-gates 规格模板合并该 requirement，已有但漏了关键行为只补缺失内容，完整时不重复添加。保留项目的 Purpose、其他 requirements 与 scenarios，规格只引用 `.rulemason/rules/workflow-gates.md`，MUST NOT 复制共享检查点正文。结构异常无法安全合并时停下并报告。
6. **验证**（结果写进汇报）：运行命令表里的 ruff 与测试；ruff 报出问题时转到「5. 建立 ruff 基线」；有前端时也运行命令表的前端 lint，报出基础规则的问题时转到「6. 建立 ESLint 基线」；没经用户确认**不改代码**；再运行一次 `rulemason check --json`，确认 `next.code` 不再是 `fill_project_info`。
7. 提醒用户：在本项目开一次交互会话，问「九条第 9 条是什么」，确认所选工具已加载共享规则。

## 3. 日常巡检

只读，不改文件（例外见「不可违反」）。按 `rulemason check` 的结果逐项解读：一致的写「一致」；有偏离的写出文件、内容和建议怎么改（由用户决定改不改）。

- 生成副本或标记块被手改：建议把改动搬到 rulemason 仓库，再运行 `rulemason update` 恢复。
- 升级产出要一起提交：`rulemason update` 刷新的副本、`.rulemason.yaml`，以及补齐计划写进项目文件的内容（如 `openspec/config.yaml` 的 rules、operations 里新增的条目、新建的 ruff 配置）都属于这次升级。怎么认出：`rulemason update` 输出里「补齐计划」列出的文件就是；事后再看时，把 `openspec/config.yaml` 里未提交的新增条目与安装包里的基础版逐字比对：用 `uv tool` 安装的，基础版在 `find "$(uv tool dir)/rulemason" -path "*_shared/openspec-base/*.yaml"` 找到的文件里（macOS、Linux 与 Windows 的目录层级不同，用 find 不必猜路径），能找到原文就是基础版，不是项目自己加的规则。用其他方式安装、找不到这个目录时，以 `rulemason update --dry-run` 列出的补齐计划为准。巡检的「与基础版的差异」只查基础条目有没有缺，不能用来认定新增条目是基础版。汇报把认出的升级产出列为「升级产出，提交时与副本一起带上」，本 skill 不提交。
- 版本号落后、副本内容相同：可以运行 `rulemason update` 更新记录，不急。副本内容落后时 check 会在「接入 生成副本」报出并给出 `update`，不会走到这里。
- 要增减工具：建议运行 `rulemason init --tools <id,...>`，它会先列出受影响文件并等确认；取消的工具会连同入口一起删除。
- 最近归档的检查点记录有缺：说明哪个 change 缺什么，提醒下次归档前按检查点把审查与测试跑完并写进 `verification.md`；不要补写过去的汇报。这一项只看接入日期（识别表「接入日期」）之后的归档；写着「接入后尚未归档，无记录可查」时不是问题，不用处理。识别表的接入日期标着「推算」时，提一句运行 `rulemason update` 会把它记进清单。
- 主规格写法有问题：按类型转述能力路径，说明读主规格判路时会因此漏看（增量格式标题、没有 `## Requirements` 时 OpenSpec 读出的 requirement 是 0 条）；建议起一个最小 change 修正这些规格，或请用户授权直接改后运行 `openspec validate --specs --strict`。本 skill 不改规格。
- lint 脚本为占位：列出文件与原文，说明 CI 跑它等于什么都没查；建议换成真的 lint 命令并引入基础规则，之后按「6. 建立 ESLint 基线」处理既有问题。
- 运行命令表的 ruff：报出问题且 ruff 配置里还没有「接入前遗留」豁免时，按「5. 建立 ruff 基线」列出计划，用户确认后才写；已有基线、只剩少量新问题时，列出文件与规则代码即可。
- 有前端时运行命令表的前端 lint：报出基础规则的问题、或 ESLint 配置里还是旧口径的全局放宽（全局提高了复杂度上限、整条关掉基础规则）时，按「6. 建立 ESLint 基线」列出计划，用户确认后才写。
- 命令表之后仍是旧写法「红线规则：暂无。」时，提一句可改为「判断用的红线规则：暂无（判断未启用；项目红线见上文「红线」一节）」，不强制。
- 识别表「判断」一行写「可选，未启用」时，说明启用条件；用户没有提出要启用就不做第 4 步。

## 4. 启用判断（可选，用户提出时才做）

判断用 Jev 检查方案是否违反已写下的规矩。前提：项目在 git 仓库里，已归档至少 3 个 change。项目没有 git 时，说明判断层需要 git（文案检查要与主分支比较），停下，不生成判断层文件。

**4.1 整理判断规则**

1. 读 `openspec/changes/archive/` 下各 change 的 `proposal.md` 与 `design.md`，找出反复出现、且能指回已写下规矩（`AGENTS.md` 某个二级标题、`config.yaml` 的 rules 或 context、某份规格）的问题。
2. 每条候选写：规则 id（kebab-case）、要问 Jev 的一句正向陈述、`expect`、`enforces`、出现在哪几个 change。两条通用规则（写明不做什么、不做过度设计）引擎已自带，「决策附备选」由 `lint/design` 检查，都不列。
3. 已归档不足 3 个时，写明还差几个，停下。
4. 候选只写在汇报里，不建文件；等用户逐条确认。

**4.2 启用判断**（用户确认了至少一条候选规则后）

模板随安装包提供，用 `rulemason judge --template <名称>` 取得，项目里没有模板副本。

1. `openspec/judgments.yaml`：以 `rulemason judge --template judgments` 的输出为起点，只写用户确认的规则；红线规则 `thresholds` 的 block 起始为 0（只 review 不拦），文件里注明。
2. `openspec/judge.yaml`：以 `rulemason judge --template judge` 为起点；项目有界面文案才写 `copy` 段（嵌套 JSON 用 `json`，HTML 内 `const I18N` 用 `js-i18n` 加 `lang`），有项目禁词才写 `banned`。
3. 回归用例骨架：以 `rulemason judge --template judge_cases` 为起点，放在项目测试目录；每条确认的规则至少列出一个待人工标注的用例位置。
4. `AGENTS.md` 命令表中的判断与文案检查改为 `rulemason judge --change <name>`、`rulemason judge --copy`，并加一行「判断回归」，填运行回归用例的命令；命令表之后「判断用的红线规则」一行（旧写法「红线规则：…」一行同理）改为列出用户确认的规则 id（这些都在标记块之外）。
5. key：本机没有 key（`~/.config/rulemason/env` 与旧位置 `~/.config/jev-judge/env` 都没有）时，提示用户在自己的终端运行 `rulemason key`，交互输入；**不代填 key**，也不在会话里处理 key。没有 key 时判断以人工模式运行。
6. **验证**：`rulemason judge --change <一个已归档 change> --lint-only` 不报 enforces 指向不存在；有 key 时再跑一次不带 `--lint-only` 的，结果写进汇报。

## 5. 建立 ruff 基线

补项目信息第 6 步或日常巡检时，命令表的 ruff 报出问题才做；没有报出问题时汇报写「ruff 通过，无需建立基线」，不改 ruff 配置。豁免全部写在项目的 ruff 配置里（init 写的那份，`pyproject.toml` 时表名前加 `tool.ruff.`），之后检查点只修本次改动引入的问题。不用 `# noqa`，不改计划以外的代码。

1. **统计**：在命令表 ruff 的命令后加 `--statistics` 运行，按规则代码列出数量。
2. **分四类写计划**，只写在汇报里，先不改文件：
   - **可安全自动修复**（`I001` import 排序、`F401` 未用导入）：给出命令与预计数量，用户确认后才运行：
     ```bash
     ruff check <命令表里的路径> --select I001,F401 --extend-exclude __init__.py --force-exclude --fix
     ```
     计划里先把 `--fix` 换成 `--diff` 运行一次，列出会被改到的文件，并与 `git status` 对照：有用户未提交的改动时，请用户先提交，或把这些文件排除在外。不加 `--unsafe-fixes`，不对其他规则 `--fix`；排除 `__init__.py` 是因为其中的未用导入常是有意的再导出。修复后先跑命令表的测试，建议用户单独提交这一步。
   - **框架在参数默认值里调函数**（`B008`，且 `pyproject.toml` 或 `requirements*.txt` 里有 `fastapi` 或 `typer`）：在项目 ruff 配置声明，按项目实际依赖只写用得上的那组：
     ```toml
     [lint.flake8-bugbear]
     # FastAPI / Typer 约定在参数默认值里声明依赖与参数，不是可变默认值
     extend-immutable-calls = [
         "fastapi.Depends", "fastapi.Query", "fastapi.Path", "fastapi.Body", "fastapi.Header",
         "fastapi.Cookie", "fastapi.Form", "fastapi.File", "fastapi.Security",
         "typer.Option", "typer.Argument",
     ]
     ```
     计划里写明 B008 总数和这些函数各占多少；剩下的 B008 归入最后一类，用户也可以补充要声明的函数。
   - **脚本与命令行入口的 `print`**（`T201`）：项目写明的脚本目录与命令行入口文件写进 `[lint.per-file-ignores]`，注明原因，例如 `"scripts/**" = ["T201"]  # 脚本的正常输出`。
   - **其余既有问题**：前三类做完后再运行一次 ruff（加 `--output-format json`），按文件汇总剩下的规则代码，写进 `[lint.per-file-ignores]`：上方一行注释 `# 接入前遗留，改到该文件时清掉`，每个文件一行，按路径排序，只列该文件实际有的代码，路径相对 ruff 配置所在目录。已有 `per-file-ignores` 表时加在表里，不另起一张同名表；init 留下的 `〈脚本目录〉` 占位注释行一并删去。
3. **列给用户确认**：四类各自的数量、要运行的命令、会被自动修复改到的文件、要写进 ruff 配置的原文（遗留条目多时列前 20 行与总条数）。此时还没重跑，遗留条目是预估：从统计里扣掉可自动修复和已声明的部分；确认后以重跑结果为准，与预估不同的地方写进汇报。用户可以只同意一部分；不同意自动修复时，`I001`、`F401` 也按文件写进遗留豁免，代码一行不改。
4. **确认后照做**，再运行命令表的 ruff 与测试：ruff 必须通过；汇报写明修复前后的问题数、写入的豁免条目数、自动修复改了几个文件。

## 6. 建立 ESLint 基线

补项目信息第 6 步或日常巡检时，命令表的前端 lint 报出基础规则（`no-console`、`no-nested-ternary`、`no-empty`、`complexity`）的问题，或 ESLint 配置里还是旧口径的全局放宽时才做；都没有时汇报写「基础规则没有报错，无需建立 ESLint 基线」，不改 ESLint 配置。豁免全部写在引入基础规则的那份 ESLint 配置里，之后检查点只修本次改动引入的问题。不整条关规则，不提高全局复杂度上限，不另写「只查改动文件」的命令（命令行的 `--rule` 会盖过配置里按文件写的豁免），不在代码里写 `eslint-disable`，不改计划以外的代码。有几个前端目录就各做一遍。

1. **统计**：在命令表前端 lint 的命令后加 `--format json -o <临时文件>` 运行（命令是 `pnpm run lint` 这类脚本时，参数前加 `--`），按文件与规则汇总基础规则的报错；`complexity` 从消息里的「complexity of N」取每个文件的最大值。其他规则（框架规则、类型规则）的问题不在本节处理，汇报列出数量即可。
2. **分两类写计划**，只写在汇报里，先不改文件：
   - **旧口径的全局放宽**：配置里把 `complexity` 全局提高了、把某条基础规则整条设成 `"off"`，或命令表的前端 lint 用 `--rule` 重新打开规则：标着接入过渡、递减计划或没写原因的，计划删掉这些覆盖、命令表改回普通的 lint 命令，删掉后再统计一次，结果按下一类处理；项目写明了长期原因的放宽（如只对日志出口文件放开 `no-console`）不在此列，列给用户确认是否保留。
   - **按文件的遗留条目**：在配置数组里、引入基础规则的那一项之后，每个文件追加一条，只放开该文件实际违反的规则，复杂度写该文件的最大值；没超过 15 的文件不写 `complexity`。按路径排序，路径相对 ESLint 配置所在目录：
     ```javascript
     // 接入前遗留，改到该文件时清掉
     { files: ["src/pages/Detail.tsx"], rules: { "no-nested-ternary": "off", complexity: ["error", 35] } },
     { files: ["src/utils/format.ts"], rules: { "no-console": "off" } },
     ```
3. **列给用户确认**：每条规则的报错数与涉及文件数、要删掉的全局覆盖原文、要写进配置的条目原文（条目多时列前 20 行与总条数）。用户可以只同意一部分。
4. **确认后照做**，再运行命令表的前端 lint 与测试：基础规则的报错必须清零，项目自己的规则若还有报错，不在本节处理，汇报列出数量；汇报写明建基线前后的问题数、写入的条目数、删掉了哪些全局覆盖。

## 7. 存量清理（可选，用户提出时才做）

用户要批量清掉既有违规（如清掉嵌套三元、把复杂度上限降一档）时做。这是不改行为的重构，改完按检查点「不走 OpenSpec 改代码时」第 4 步跑 ruff、前端 lint 与测试。动手前列出第 1、2 步的计划（分组、共用模块、要存的指标），用户确认后再做。

1. **规划**：从 lint 的 JSON 输出或基线条目列出要清的文件，按模块分组，同一文件只属一组；清单里的文件有未提交改动时先剔除，或请用户先提交，否则改前提交对不上起点，`git diff` 核对也会混进用户的改动。每组建议 3–6 个文件，并行组数按所用工具的用量上限定，宁少勿多：一组太大难复核，并行太多容易同时被打断。多组都要用的辅助函数先规划成共用模块、在一处建好，计划里写明各组复用它；不要为了缩小改动面要求「不新建文件」，那会让同一个函数在每组各复制一份。
2. **先存证据**：动手前在改前的提交上建一个临时 worktree（`git worktree add --detach <临时目录> <改前提交>`，临时目录放在仓库外，免得 lint 把它一起扫进去），在那里跑命令表的 ruff 或前端 lint（加 JSON 输出），统计要盯的指标（如超过 15 的函数个数与最大值），结果存成一份放在 worktree 外的文件，写明提交号。前端依赖先用本机缓存离线安装，缺的才下载；装不上时停下说明，由用户决定怎么取改前数字。不要把改前代码经 stdin 交给 lint：带类型检查的配置会按路径读磁盘上的当前文件，得到的是改后的数字。
3. **代理指令**：每组同一份，按项目语言改写。只改本组清单里的文件；不动 git 状态（不提交、不暂存、不切分支、不 stash）；行为等价是硬要求，React 按 react.md「重构等价性」逐条对照；碰到读源码断言原文的测试，按检查点「改既有测试时」处理；拆函数拆到下一档以内，不刚好卡在上限；汇报写改了哪些文件、每个文件的指标改前改后，并附一处有代表性的改前改后代码。
4. **恢复**：有组中途停下（用量上限、出错）时，先用 `git diff --stat` 与清单核对哪些文件已经改完，只把没改完的交出去继续，不重做已完成的部分；证据文件不重跑。
5. **主会话复核**：在当前工作区重跑同样的指标，与证据文件对比，要盯的指标都不应变差（如超过 15 的函数个数不应变多）；React 改动按「重构等价性」抽查；本次新增的函数按名字在仓库里检索，有重复就合并进共用模块。
6. **收尾**：清干净的文件从 ruff 或 ESLint 的「接入前遗留」条目里删掉，上限降一档的同步改配置；用 `git worktree remove --force <临时目录>` 删掉临时 worktree（里面装过依赖，不加 `--force` 删不掉），再 `git worktree prune`；汇报按第 8 节写，附改前改后的指标对比。本 skill 不提交。

## 8. 汇报

按顺序：`rulemason check --json` 的 `text` → 本次做了什么 → 每项验证命令与结果 → 本次新增、修改的文件清单 → 没碰的东西（未提交改动数）→ 下一步（以 `next.action` 为准）。
