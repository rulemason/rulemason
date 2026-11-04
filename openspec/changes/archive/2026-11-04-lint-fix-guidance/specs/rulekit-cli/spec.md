## ADDED Requirements

### Requirement: 识别旧位置的基础配置副本

ruff 的 `extend` 或 ESLint 的引入指向项目内另一份同名基础配置（`ruff-base.toml` 或 `eslint-base.mjs`，不在 `.rulemason/lint/` 下）时，该文件内容与 `.rulemason/lint/` 下的副本相同，`init` 与 `update` SHALL 把路径改为指向项目内副本，作为一条「修改」进计划，并提示旧文件已无人引用、可以删除；MUST NOT 代为删除。内容不同时 MUST NOT 修改，按「改不了的 lint 项写明怎么改」报告。这一判断 SHALL 先于沿继承链处理。

#### Scenario: 卸载后再接入
- **WHEN** 项目运行过 `rulemason remove`，`ruff.toml` 写 `extend = "lint/ruff-base.toml"`，之后运行 `rulemason init --yes`
- **THEN** `ruff.toml` 改为 `extend = ".rulemason/lint/ruff-base.toml"`，汇报写明 `lint/ruff-base.toml` 已无人引用、可以删除，「需要你处理」里没有 ruff 项，`lint/ruff-base.toml` 仍在

#### Scenario: 旧副本被改过
- **WHEN** `ruff.toml` 继承 `lint/ruff-base.toml`，其内容与 `.rulemason/lint/ruff-base.toml` 不同
- **THEN** 不改任何文件，说明写明先运行 `diff lint/ruff-base.toml .rulemason/lint/ruff-base.toml` 看差异、把要保留的设置写进 `ruff.toml`、把 `ruff.toml` 该行改为继承 `.rulemason/lint/ruff-base.toml`，最后运行 `rulemason update`

#### Scenario: check 的口径
- **WHEN** 接入只剩 `ruff.toml` 继承内容相同的 `lint/ruff-base.toml`
- **THEN** check 报该配置继承的是旧位置的基础配置副本，第一行的下一步是「运行 rulemason update」

#### Scenario: ESLint 引入旧位置副本
- **WHEN** `apps/admin-web/eslint.config.js` 只从 `../../lint/eslint-base.mjs` 引入，该文件与 `.rulemason/lint/eslint-base.mjs` 内容相同
- **THEN** init 计划把这条路径改为 `../../.rulemason/lint/eslint-base.mjs`，文件里只保留一条基础规则引入

### Requirement: check 报 ESLint 重复引入基础规则

一份 ESLint 配置既引入了 `.rulemason/lint/eslint-base.mjs`，又引入了其他位置的同名基础规则时，`check` SHALL 在「接入 lint 继承」报「重复引入基础规则」并以非 0 退出；`init` 与 `update` MUST NOT 自动删除任一引入，说明 SHALL 写明旧引入所在行号与原文，以及配置里使用它的那一项所在行号与原文，删去这两处后运行 `rulemason check`。

#### Scenario: 同时引入两份
- **WHEN** `apps/admin-web/eslint.config.js` 第 2 行从 `../../lint/eslint-base.mjs` 引入 `legacyBase`，第 3 行从 `../../.rulemason/lint/eslint-base.mjs` 引入 `rulemasonBase`，第 9 行是 `{ rules: legacyBase },`
- **THEN** check 报该文件重复引入基础规则并以非 0 退出，说明写明删去第 2 行与第 9 行，`init --yes` 不修改该文件

### Requirement: ruff 沿继承链接上基础配置

ruff 配置已用 `extend` 继承了别的配置、但没有接上 `.rulemason/lint/ruff-base.toml` 时，`init` 与 `update` SHALL 沿 `extend` 找到继承链末端那份配置（相对路径按所在配置文件的目录解析），在末端配置里加入继承项目内基础配置的一行，作为一条「修改」进计划。链上原有的 `extend` MUST 保持不变。末端在项目外、读不出、链上有循环或任一配置写了 `select` 时 MUST NOT 修改，按「改不了的 lint 项写明怎么改」报告。

#### Scenario: 两层继承
- **WHEN** 项目 `ruff.toml` 写 `extend = "config/ruff-shared.toml"`，该文件存在且没有 `extend` 与 `select`
- **THEN** init 计划的「修改」含 `config/ruff-shared.toml`，写入后它继承 `../.rulemason/lint/ruff-base.toml`，`ruff.toml` 逐字不变，「需要你处理」里没有这一项

#### Scenario: 三层继承
- **WHEN** `ruff.toml` 继承 `a.toml`，`a.toml` 继承 `b.toml`，`b.toml` 没有 `extend`
- **THEN** 只有 `b.toml` 被加入继承基础配置的一行

#### Scenario: 两份配置共用末端
- **WHEN** `apps/api/ruff.toml` 与 `apps/worker/ruff.toml` 都继承项目根的 `ruff-common.toml`
- **THEN** 计划只修改 `ruff-common.toml` 一次，两份子配置都不改

#### Scenario: 继承链有循环
- **WHEN** `a.toml` 继承 `b.toml`，`b.toml` 又继承 `a.toml`
- **THEN** init 不修改任何 ruff 配置，在「需要你处理」写明循环经过的文件

#### Scenario: 已接上时不再改
- **WHEN** 继承链末端已继承 `.rulemason/lint/ruff-base.toml`，再次运行 `rulemason update --yes`
- **THEN** 计划中没有任何 ruff 配置

### Requirement: check 沿继承链判断 ruff 是否接上

`check` 判断一份 ruff 配置是否接上基础配置时 SHALL 沿 `extend` 查整条继承链：链上任一配置继承了项目内的 `ruff-base.toml` 副本即为接上；判断 `select` 时 SHALL 同样查整条链。链上配置指向不存在的文件时 SHALL 报「引用的基础配置不存在」或继承链中断，并写明是哪一份配置的哪个引用。

#### Scenario: 末端接上即为接上
- **WHEN** `ruff.toml` 继承 `config/ruff-shared.toml`，后者继承 `../.rulemason/lint/ruff-base.toml`
- **THEN** check 的「接入 lint 继承」没有问题，退出码不受 ruff 影响

#### Scenario: 链上的 select
- **WHEN** `ruff.toml` 继承 `config/ruff-shared.toml`，后者写了 `select`
- **THEN** check 报 `config/ruff-shared.toml` 写了 `select` 会覆盖基础规则，并以非 0 退出

### Requirement: 改不了的 lint 项写明怎么改

`init`、`update` 与 `check` 报告改不了的 lint 项时，SHALL 先写一行摘要（文件与原因），再分行写：要改的文件与行号、该行原文、可选做法（每种做法写出改后的原文）、改完运行的命令。覆盖：ruff 配置写了 `select`（做法为改成 `extend-select` 或删去该行）、继承链走到项目外（做法为把该行改成继承项目内副本，并提醒把需要的设置复制进项目）、继承链循环、旧位置副本被改过、ESLint 重复引入、ESLint 配置格式认不出。说明 MUST NOT 给出用 `sed` 等命令直接改文件的一行命令。

#### Scenario: ruff.toml 写了 select
- **WHEN** 项目 `ruff.toml` 第 3 行是 `select = ["E", "F"]`，运行 `rulemason init --yes`
- **THEN** 「需要你处理」写明 `ruff.toml` 第 3 行与原文 `select = ["E", "F"]`，列出「改为 `extend-select = ["E", "F"]`」与「删去这一行」两种做法，最后写「改完运行：rulemason update」

#### Scenario: 继承了项目外的配置
- **WHEN** `ruff.toml` 第 1 行是 `extend = "~/configs/ruff.toml"`
- **THEN** 说明写明 `ruff.toml` 第 1 行与原文、改后的原文 `extend = ".rulemason/lint/ruff-base.toml"`，提醒把 `~/configs/ruff.toml` 里需要的设置复制进 `ruff.toml`，并写「改完运行：rulemason update」

#### Scenario: ESLint 配置格式认不出
- **WHEN** `web/eslint.config.js` 不是认得出的三种导出写法
- **THEN** 说明写明在该文件第一条 `import` 之前加入的引入原文，以及加到导出配置数组第一项的 `{ rules: rulemasonBase },`

#### Scenario: 老格式 .eslintrc
- **WHEN** 项目只有 `web/.eslintrc.json`
- **THEN** 说明写明 rulemason 只接扁平配置，先运行 `npx @eslint/migrate-config web/.eslintrc.json` 生成 `eslint.config.mjs`，再运行 `rulemason update`

## MODIFIED Requirements

### Requirement: init 可重复运行，冲突只报告

对已接入且未改动的项目重复运行 `init` SHALL 不产生任何文件改动。遇到无法安全写入的情况（ruff 配置仍写 `select`、无法识别的 ESLint 配置格式、标记块不成对），`init` MUST 跳过该文件并在汇报中说明，不强行改写。

#### Scenario: 第二次运行
- **WHEN** init 成功后立即再次运行 `rulemason init --yes`
- **THEN** 汇报「没有需要改动的文件」，工作区无变化

#### Scenario: ruff 配置写了 select
- **WHEN** 项目 `pyproject.toml` 的 `[tool.ruff.lint]` 写了 `select`
- **THEN** init 不改该文件，汇报写明 `select` 所在的行号与原文、会覆盖基础规则，并给出改为 `extend-select` 或删去该行两种做法，由用户处理

### Requirement: check 第一行给结论与下一步

`rulemason check` 输出的第一行 SHALL 是结论与下一步要做的事，下一步 SHALL 按原因给出具体命令或动作，同时有多个原因时按以下顺序取第一个：清单无效 → 先修正清单；尚未接入 → `rulemason init`；生成副本被 `.gitignore` 忽略 → 修改 `.gitignore` 放行 `skills/rulemason/`；副本或标记块与模板不一致、副本与本机应生成的不一致、入口缺失、配置待补齐 → `rulemason update`；接入只剩 update 改不了的 lint 项 → 第一行写明手动修改的文件，具体行号、原文与做法写在报告里；项目信息待补 → `/rulemason`。只有版本号落后时第一行 SHALL 附一句，不改变下一步。阶段名 SHALL 使用：接入、补项目信息、日常巡检；判断相关为可选的「整理判断规则」「启用判断」。`next.code` MUST NOT 再出现 `legacy`、`migrate`、`fix_residue`。

#### Scenario: 刚接入的项目
- **WHEN** 刚运行完 `rulemason init`，项目简介与红线待补
- **THEN** 第一行写「补项目信息：在 AI 工具中运行 /rulemason」

#### Scenario: 副本被忽略
- **WHEN** skill 副本被 `.gitignore` 忽略
- **THEN** 第一行的下一步是修改 `.gitignore` 放行 `skills/rulemason/`，而不是 `rulemason update`

#### Scenario: 一切就绪
- **WHEN** 项目接入完整、项目信息已补、没有任何偏离
- **THEN** 第一行写「日常巡检：一切一致」，退出码为 0

#### Scenario: 只剩手动 lint 项
- **WHEN** 接入只剩 `apps/client-web/eslint.config.js` 一项，其写法 update 无法自动改
- **THEN** 第一行写「接入：手动修改 apps/client-web/eslint.config.js」，报告的「接入 lint 继承」下列出要加的引入与数组项，第一行不写「运行 rulemason update」

#### Scenario: 能沿继承链补齐时不算手动项
- **WHEN** 接入只剩 `ruff.toml` 继承项目内 `config/ruff-shared.toml`、末端尚未接上基础配置
- **THEN** 第一行的下一步是「运行 rulemason update」

#### Scenario: 只有版本号落后
- **WHEN** 项目一切一致，记录 0.8.4，本机 0.8.5 生成的副本内容相同
- **THEN** 第一行写「日常巡检：一切一致」并附「版本号落后（0.8.4 → 0.8.5），副本内容相同」

### Requirement: remove 保持 lint 可用

ruff 或 ESLint 配置仍引用 `.rulemason/lint/` 下的副本时，`rulemason remove` SHALL 把被引用的副本移到项目根的 `lint/` 目录，并把各配置中的引用改为指向新位置的相对路径，使 lint 结果不变。`lint/` 中已有同名而内容不同的文件时 SHALL 停下，不写任何文件。

#### Scenario: Python 项目卸载后 ruff 照常
- **WHEN** 项目 `ruff.toml` 写着 `extend = ".rulemason/lint/ruff-base.toml"`，运行 `rulemason remove --yes`
- **THEN** `lint/ruff-base.toml` 内容与原副本相同，`ruff.toml` 改为 `extend = "lint/ruff-base.toml"`，`.rulemason/` 不再存在

#### Scenario: 继承链末端引用副本
- **WHEN** `ruff.toml` 继承 `config/ruff-shared.toml`，后者写着 `extend = "../.rulemason/lint/ruff-base.toml"`，运行 `rulemason remove --yes`
- **THEN** `config/ruff-shared.toml` 改为 `extend = "../lint/ruff-base.toml"`，`ruff.toml` 逐字不变，`lint/ruff-base.toml` 与原副本相同

#### Scenario: 子目录里的 ESLint 配置
- **WHEN** `web/eslint.config.mjs` 写着 `import rulemasonBase from "../.rulemason/lint/eslint-base.mjs"`
- **THEN** 卸载后改为 `"../lint/eslint-base.mjs"`，`lint/eslint-base.mjs` 与原副本相同

#### Scenario: 目标已被占用
- **WHEN** 项目已有内容不同的 `lint/ruff-base.toml`
- **THEN** `rulemason remove` 说明冲突并以非 0 退出，项目中没有任何文件变化
