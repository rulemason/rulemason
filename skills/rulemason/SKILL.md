---
name: rulemason
description: 在已运行 rulemason init 的项目里补齐需要理解项目的部分（项目简介、红线、命令表确认），解读 rulemason check 的结果，或在用户要求时启用判断。用户要接入、补全、巡检 rulemason 或启用判断时使用。
---

# /rulemason：补项目信息、巡检与启用判断

rulemason 管三件事：**规则**（写法规矩）、**检查点**（方案与代码前后的自动检查）、**判断**（用 Jev 判断方案是否违反规矩，可选）。共享规则只在 rulemason 仓库编辑；接入（生成规则副本、工具入口、基础配置）由 `rulemason init` 完成，升级与补齐由 `rulemason update` 完成。本 skill 只做需要理解项目的事。

## 不可违反

- **先识别后动手**：第 1 步 `rulemason check --json` 的 `next.code` 决定做什么，不凭印象判断阶段，也不按文字措辞匹配。
- **一次只做一件事**：做之前列出要新增、修改的文件，用户同意后才写。
- **红线与判断规则由用户确认**：候选要注明出处（README、`openspec/config.yaml` 的 context、某个已归档方案）；没确认的不写。
- **不改 rulemason 标记块**：`<!-- rulemason:… -->` 与 `<!-- /rulemason:… -->` 之间的内容、`.rulemason/` 与各工具的 skill 副本都是生成的，由 `rulemason update` 刷新，本 skill 不改。
- **不提交、不推送**：工作区里用户已有的改动一律不碰；汇报末尾列出本次改了哪些文件。
- **巡检只报告**：日常巡检不改任何文件。

## 1. 识别

1. 先确认本机有 `rulemason` 命令，且 `rulemason --version` 不低于项目 `.rulemason.yaml` 里 `rulemason:` 记录的版本；没有命令或版本更低时，给出安装命令 `uv tool install rulemason`（已装旧版本时用 `uv tool upgrade rulemason`；需要与清单记录的版本一致时用 `uv tool install --force rulemason==<版本>`），然后停下。
2. 在项目根目录（或任意子目录）运行 `rulemason check --json`，把 `text`（报告全文）原样放进汇报；`next.action` 是给人看的下一步，`next.code` 决定这次做什么。命令以非 0 退出且输出不是 JSON 时（例如「rulemason check 失败：openspec/config.yaml 不是合法的 YAML…」），原样转述这条提示，请用户修正对应文件，然后停下：

| `next.code` | 这次做什么 |
|---|---|
| `init` | 提示用户在项目根运行 `rulemason init`（没有 `openspec/` 时它会先询问）。停下，项目已归档再多 change 也一样。用户要你代为接入时，先运行 `rulemason init --plan` 把计划给用户看（不写任何文件），用户同意并选定工具后再运行 `rulemason init --tools <所选> --yes` |
| `fix_manifest` | 说明清单读不出来的原因（见 `layers` 的「接入 工具入口」），请用户修正，或删掉后重新 `rulemason init`。停下 |
| `fix_gitignore` | 列出要改的 `.gitignore` 规则（只放行 `skills/rulemason/`，说明单独写一行），用户确认后修改，再运行 `rulemason check --json` |
| `update` | 提示用户运行 `rulemason update`；可先用 `rulemason update --dry-run` 给用户看计划。它列出「补齐计划」时，由用户决定是否 `rulemason update --yes`。停下 |
| `manual_lint` | 接入只剩 `rulemason update` 改不了的 lint 项：`next.action` 写了要改的文件与摘要，把 `layers` 的「接入 lint 继承」里各项的行号、原文与做法列给用户；有几种做法时由用户选，用户同意后照改，再运行 `rulemason check --json`。不要让用户重跑 update |
| `fill_project_info` | 第 2 步 |
| `upgrade_machine` | 本机 rulemason 比项目记录的旧：按上面第 1 条给出安装命令。停下 |
| `none` | 第 3 步；用户说要启用判断时做第 4 步。`next.action` 附有「版本号落后」时，提一句可运行 `rulemason update` 更新记录 |

## 2. 补项目信息

先列文件计划（要新增、修改的文件，修改写明改哪一段；「其余 N 个未提交改动不变」），用户同意后再写。

1. **项目简介**：`rulemason init` 已从 README 第一段预填了简介；把它念给用户核对，用户要改才改。仍是「待 /rulemason 补充」时按 README 与代码写一两句话替换。
2. **红线候选**：init 把红线一节写成「暂无」，这里仍要问一次：从 README、`openspec/config.yaml` 的 `context` 里找出「绝对不能做的事」，每条注明出处，逐条请用户确认、改写或删除；没有找到也要问用户一句。确认的替换「暂无」写进「## 红线（不可违反）」；用户说没有就保留「暂无」。`context` 本身不改。
3. **样板与豁免**：在 Code style 标记块之后写本项目样板文件路径、语言落法位置与 ruff 豁免文件。
4. **命令表**：向用户展示「本项目命令表（自动识别，请确认）」中的命令，按用户确认或修改后的内容写入，并去掉「自动识别，请确认」。判断与文案检查保持「可选，未启用」。
5. **项目工作流规格**：init 或 update 汇报 `openspec/specs/workflow-gates/spec.md` 需要合并时，检查是否已有「Apply 后自动精简并审查」或语义等价的 requirement；缺失则按 rulemason 的 workflow-gates 规格模板合并该 requirement，已有但漏了关键行为只补缺失内容，完整时不重复添加。保留项目的 Purpose、其他 requirements 与 scenarios，规格只引用 `.rulemason/rules/workflow-gates.md`，MUST NOT 复制共享检查点正文。结构异常无法安全合并时停下并报告。
6. **验证**（结果写进汇报）：运行命令表里的 ruff 与测试，报出的问题列进汇报，**不自动修代码**；再运行一次 `rulemason check --json`，确认 `next.code` 不再是 `fill_project_info`。
7. 提醒用户：在本项目开一次交互会话，问「九条第 9 条是什么」，确认所选工具已加载共享规则。

## 3. 日常巡检

只读，不改文件。按 `rulemason check` 的结果逐项解读：一致的写「一致」；有偏离的写出文件、内容和建议怎么改（由用户决定改不改）。

- 生成副本或标记块被手改：建议把改动搬到 rulemason 仓库，再运行 `rulemason update` 恢复。
- 版本号落后、副本内容相同：可以运行 `rulemason update` 更新记录，不急。副本内容落后时 check 会在「接入 生成副本」报出并给出 `update`，不会走到这里。
- 要增减工具：建议运行 `rulemason init --tools <id,...>`，它会先列出受影响文件并等确认；取消的工具会连同入口一起删除。
- 最近归档的检查点记录有缺：说明哪个 change 缺什么，提醒下次归档前按检查点把审查与测试跑完并写进 `verification.md`；不要补写过去的汇报。
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
4. `AGENTS.md` 命令表中的判断与文案检查改为 `rulemason judge --change <name>`、`rulemason judge --copy`，并加一行「判断回归」，填运行回归用例的命令（命令表在标记块之外）。
5. key：本机没有 key（`~/.config/rulemason/env` 与旧位置 `~/.config/jev-judge/env` 都没有）时，提示用户在自己的终端运行 `rulemason key`，交互输入；**不代填 key**，也不在会话里处理 key。没有 key 时判断以人工模式运行。
6. **验证**：`rulemason judge --change <一个已归档 change> --lint-only` 不报 enforces 指向不存在；有 key 时再跑一次不带 `--lint-only` 的，结果写进汇报。

## 5. 汇报

按顺序：`rulemason check --json` 的 `text` → 本次做了什么 → 每项验证命令与结果 → 本次新增、修改的文件清单 → 没碰的东西（未提交改动数）→ 下一步（以 `next.action` 为准）。
