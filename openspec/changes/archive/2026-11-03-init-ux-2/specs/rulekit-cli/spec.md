## MODIFIED Requirements

### Requirement: init 补齐配置并识别命令

`init` SHALL 把共享产物写法基础版中缺少的条目补进 `openspec/config.yaml` 的 `rules`，保留 `context` 与项目追加的条目；为项目实际有的语言写 ruff 或 ESLint 继承，指向 `.rulemason/lint/`（ESLint 认 `export default [`、`export default defineConfig([`、`export default tseslint.config(` 三种写法；已有引用指向不存在或项目外的同名基础配置时改正该路径，不另加引入；新建的 ruff 配置在只有一个 Python 目录且 Python 文件都在其中时放进该目录）；项目没有 `openspec/specs/workflow-gates/spec.md` 时按模板创建。命令表只在 `AGENTS.md` 缺少命令表（表头为「名称 / 命令」或英文「Name / Command」）时，按识别到的包管理与测试目录填入，并标注「自动识别，请确认」；判断与文案检查写「可选，未启用」。

#### Scenario: uv 管理的 Python 项目
- **WHEN** 项目有 `pyproject.toml`、`uv.lock` 与 `tests/`，没有 ruff 配置
- **THEN** 新建继承 `.rulemason/lint/ruff-base.toml` 的 ruff 配置，命令表填入 ruff 与 pytest 命令并标注待确认

#### Scenario: 已有 workflow-gates 规格
- **WHEN** 项目已有 `openspec/specs/workflow-gates/spec.md`，但没有 rulemason 的 requirement
- **THEN** init 不修改该文件，在汇报中写明需由 `/rulemason` 合并

#### Scenario: 已有等价的 workflow-gates requirement
- **WHEN** 项目规格里已有以「Apply 后自动精简」开头的 requirement，并引用 `.rulemason/rules/workflow-gates.md`
- **THEN** init 不修改该文件，也不提示合并

#### Scenario: 英文命令表表头
- **WHEN** `AGENTS.md` 已有表头为 `| Name | Command |` 的命令表
- **THEN** init 不再插入自动识别的命令表

#### Scenario: defineConfig 写法的 ESLint 配置
- **WHEN** `web/eslint.config.js` 写 `export default defineConfig([`，没有引入基础规则
- **THEN** init 计划在该文件加入 `import rulemasonBase from "../.rulemason/lint/eslint-base.mjs"` 与数组第一项 `{ rules: rulemasonBase }`，不报「格式无法自动识别」

#### Scenario: tseslint.config 写法的 ESLint 配置
- **WHEN** ESLint 配置写 `export default tseslint.config(`
- **THEN** init 计划把 `{ rules: rulemasonBase }` 作为第一个参数加入，并加上引入

#### Scenario: 引用指向不存在的基础配置
- **WHEN** `apps/admin-web/eslint.config.js` 从 `../../../.rulekit/lint/eslint-base.mjs` 引入，该文件不存在
- **THEN** init 计划把这条路径改为 `../../.rulemason/lint/eslint-base.mjs`，文件里只保留一条基础规则引入

#### Scenario: 唯一的 Python 目录
- **WHEN** 项目的 Python 文件都在 `apps/api/`（有 `pyproject.toml`、没有 ruff 配置），项目根没有 Python 文件
- **THEN** init 新建 `apps/api/ruff.toml`，继承 `../../.rulemason/lint/ruff-base.toml`，项目根不出现 `ruff.toml`

### Requirement: update 刷新副本

`rulemason update` SHALL 用当前安装的版本刷新 rulemason 自己管的文件（`.rulemason/` 副本、skill 副本、已有的标记块与 `.rulemason.yaml`），MUST NOT 提问选工具。缺的配置（ruff / ESLint 继承、基础 rules、workflow-gates 规格、缺的标记块）SHALL 按 `init` 的规则补齐：先列计划，交互确认或带 `--yes` 才写；非交互且没有 `--yes` 时 MUST NOT 修改，只列为「待补齐」。`update` SHALL 删除清单记录过、不再生成且未改的旧副本，改过的只报告；被手改的副本与块 SHALL 列出。`update` MUST NOT 修改标记块以外的命令表、红线或判断层文件。项目没有 `openspec/` 时，`update` 结尾 SHALL 写明方案检查点未启用及补齐方法。

#### Scenario: 升级共享规则
- **WHEN** 用户升级到 rulemason 新版本后在项目运行 `rulemason update`
- **THEN** `.rulemason/rules/` 与 skill 副本变为新版本内容，`.rulemason.yaml` 记录新版本，`AGENTS.md` 标记块以外的内容不变

#### Scenario: 副本被手改
- **WHEN** 有人手改了 `.rulemason/rules/code-style.md` 后运行 update
- **THEN** 该文件恢复为共享版本，汇报列出它被覆盖

#### Scenario: 旧格式项目运行 update
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `rulemason update`
- **THEN** 与没有任何清单的项目相同：报告「先运行 rulemason init」并以非 0 退出，不写任何文件，不提迁移

#### Scenario: 补齐缺的 ruff 继承
- **WHEN** 已接入项目新加了 Python 代码、还没有 ruff 配置，运行 `rulemason update --yes`
- **THEN** 新建继承 `.rulemason/lint/ruff-base.toml` 的 ruff 配置，汇报列出该文件

#### Scenario: 非交互且没有 --yes
- **WHEN** 同样的项目在非交互环境运行 `rulemason update`
- **THEN** 副本照常刷新，ruff 配置不写，汇报列出「待补齐」及运行 `rulemason update --yes`

#### Scenario: 清理旧模板副本
- **WHEN** 从 0.6.x 升级的项目有 `.claude/skills/rulemason/templates/` 下未改动的 3 个模板副本，运行 `rulemason update`
- **THEN** 这 3 个文件与空目录被删除，`.rulemason.yaml` 不再记录它们

#### Scenario: 没有 OpenSpec 的项目运行 update
- **WHEN** 项目没有 `openspec/`，运行 `rulemason update`
- **THEN** 输出最后写明「方案检查点未启用：安装 OpenSpec 并 openspec init 后再运行 rulemason update」，退出码为 0

### Requirement: check 只读检查并以退出码报告

`rulemason check` SHALL 只读，不要求 git，输出识别表、各层状态、巡检结果与下一步。以下任一情况 MUST 以非 0 退出：已选工具入口缺失、生成副本与 `.rulemason.yaml` 记录的校验值不符、标记块与当前模板不一致、项目在 git 仓库里而生成副本被 `.gitignore` 忽略、ruff 或 ESLint 未继承 `.rulemason/lint/` 或引用的基础配置不存在、本机版本应生成的副本与清单记录不一致。只有版本号落后、副本内容相同时 SHALL 报告，MUST NOT 因此非 0 退出。判断层未启用 MUST NOT 被报告为缺，SHALL 显示「可选，未启用」与启用条件；条件已满足而本机没有 key 时 SHALL 提示运行 `rulemason key` 并附申请地址。没有 `openspec/` 的项目 MUST NOT 因缺方案写法规则与检查点规格而非 0 退出，识别表的 openspec 一行 SHALL 写明方案检查点未启用。巡检 MUST NOT 含「旧接入方式」与「旧名残留」两项。

#### Scenario: CI 中运行
- **WHEN** 项目 CI 安装 rulemason 后运行 `rulemason check`，有人手改了 `.rulemason/` 中的副本
- **THEN** 输出被改的文件，退出码非 0

#### Scenario: 一切一致
- **WHEN** 在刚完成 init 的项目运行 `rulemason check`
- **THEN** 各项写「一致」，退出码为 0

#### Scenario: rulekit 仓库自身
- **WHEN** 在 rulemason 仓库根目录运行 `rulemason check`
- **THEN** 按直接引用 `rules/` 的方式检查，不报告「判断引擎副本」或「缺少 `.rulemason/`」

#### Scenario: 副本被 .gitignore 忽略
- **WHEN** 项目的 `.gitignore` 整体忽略 `.claude/`，已选 Claude Code
- **THEN** `rulemason check` 列出被忽略的 skill 副本，退出码非 0

#### Scenario: 尚未迁移的 rulekit 项目
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `rulemason check`
- **THEN** 与没有任何清单的项目相同：第一行提示「接入：运行 rulemason init」，退出码非 0，不提迁移

#### Scenario: 判断层未启用
- **WHEN** 已接入且补完项目信息的项目没有 `openspec/judgments.yaml`，已归档 2 个 change
- **THEN** 判断显示「可选，未启用（需要 git 与至少 3 个已归档 change；还差 1 个）」，不列入缺失，下一步为「日常巡检」，退出码为 0

#### Scenario: 条件满足但没有 key
- **WHEN** 项目已归档 3 个 change、没有 `openspec/judgments.yaml`，本机没有 key
- **THEN** 判断显示「可选，未启用（条件已满足；本机未配置 key：运行 rulemason key，申请地址 https://typesafe.ai/ ）」，退出码不受影响

#### Scenario: 副本内容落后
- **WHEN** 项目记录 0.8.4，本机 0.8.5 改了 `rules/code-style.md`，项目未运行 update
- **THEN** 生成副本一层列出「副本与本机版本应生成的不一致」，退出码非 0

#### Scenario: 启用判断后副本要补文案语气
- **WHEN** 版本未变，项目新增 `openspec/judgments.yaml`，清单里没有 `copy-voice.md` 副本
- **THEN** 生成副本一层列出「副本与本机版本应生成的不一致」，下一步为 `rulemason update`

#### Scenario: 只有版本号落后
- **WHEN** 项目记录 0.8.4，本机 0.8.5 生成的副本与记录的校验值完全相同
- **THEN** 退出码为 0，第一行附一句版本号落后、副本内容相同

#### Scenario: lint 引用的文件不存在
- **WHEN** ESLint 配置引用的 `eslint-base.mjs` 路径不存在
- **THEN** lint 继承一层单独列出「引用的基础配置不存在」及该路径，退出码非 0

### Requirement: check 第一行给结论与下一步

`rulemason check` 输出的第一行 SHALL 是结论与下一步要做的事，下一步 SHALL 按原因给出具体命令或动作，同时有多个原因时按以下顺序取第一个：清单无效 → 先修正清单；尚未接入 → `rulemason init`；生成副本被 `.gitignore` 忽略 → 修改 `.gitignore` 放行 `skills/rulemason/`；副本或标记块与模板不一致、副本与本机应生成的不一致、入口缺失、配置待补齐 → `rulemason update`；接入只剩 update 改不了的 lint 项 → 写明手动修改的文件与要加的内容；项目信息待补 → `/rulemason`。只有版本号落后时第一行 SHALL 附一句，不改变下一步。阶段名 SHALL 使用：接入、补项目信息、日常巡检；判断相关为可选的「整理判断规则」「启用判断」。`next.code` MUST NOT 再出现 `legacy`、`migrate`、`fix_residue`。

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
- **THEN** 第一行写「接入：手动修改 apps/client-web/eslint.config.js」并给出要加的引入与数组项，不写「运行 rulemason update」

#### Scenario: 只有版本号落后
- **WHEN** 项目一切一致，记录 0.8.4，本机 0.8.5 生成的副本内容相同
- **THEN** 第一行写「日常巡检：一切一致」并附「版本号落后（0.8.4 → 0.8.5），副本内容相同」

### Requirement: 按项目语言引用 React 落法

某个 `package.json` 的 `dependencies`、`devDependencies` 或 `peerDependencies` 含 `react` 时，所在目录 SHALL 视为 React 目录。项目有 React 目录时，`init` 与 `update` 写的标记块和工具入口 SHALL 引用 `.rulemason/rules/react.md`，没有时 MUST NOT 引用；已有 OpenCode 配置缺少应引用的落法时，补齐计划 SHALL 追加到其唯一的 instructions 数组末尾，无法安全追加时只提示；识别表的前端目录 SHALL 只列依赖含界面框架（react、vue、svelte、@angular/core、preact、solid-js、next、nuxt）或同目录有 index.html 的目录，并标出 React。`rulemason check` SHALL 在巡检「React 目录缺少 ESLint」中列出本身及上级目录都没有 ESLint 配置的 React 目录，MUST NOT 因此以非 0 退出。

#### Scenario: React 项目
- **WHEN** `web/package.json` 依赖 `react`，运行 `rulemason init --tools claude,opencode --yes`
- **THEN** `AGENTS.md` 的 Code style 块、`CLAUDE.md` 的 rulemason 块与 `opencode.jsonc` 的 instructions 都含 `.rulemason/rules/react.md`

#### Scenario: 已有 OpenCode 配置
- **WHEN** 项目 `.opencode/opencode.jsonc` 的 instructions 没有 `react.md`，升级后运行 `rulemason update --yes`
- **THEN** `react.md` 追加在数组末尾，其余内容不变，check 的工具入口一层齐全

#### Scenario: 没有 React
- **WHEN** 项目只有 Python 与不依赖 react 的 `package.json`
- **THEN** 标记块与入口都不出现 `react.md`

#### Scenario: React 目录没有 ESLint
- **WHEN** 项目乙的 `studio/package.json` 依赖 react，`studio/` 与项目根都没有 ESLint 配置
- **THEN** `rulemason check` 在「React 目录缺少 ESLint」列出 `studio`，退出码不因此改变

#### Scenario: 工作区根与后端的 package.json
- **WHEN** 项目根的 `package.json` 只有工作区与工具依赖，`apps/api/package.json` 也没有界面框架，`apps/web/package.json` 依赖 vue
- **THEN** 识别表前端目录只列 `apps/web`

#### Scenario: 不用框架的网页前端
- **WHEN** `frontend/package.json` 只依赖 vite 与 typescript，`frontend/index.html` 存在
- **THEN** 识别表前端目录列出 `frontend`，不标 React

### Requirement: 子仓库、子项目与第三方目录不属于本项目

列项目文件时，以下子目录 SHALL 视为不属于本项目、整个跳过：含 `.git` 的子目录（另一个 git 仓库，含子模块）、含 `.rulemason.yaml` 的子目录（另一个 rulemason 项目）、名为 `bower_components`、`uni_modules`、`third_party`、`jspm_packages`、`Pods` 的目录，以及含 Composer 的 `autoload.php` 或 Go 的 `modules.txt` 的 `vendor` 目录（第三方代码；没有这些标记的 `vendor` 属于项目自己）。项目在 git 仓库里与不在 git 仓库里时，跳过的结果 MUST 相同。`openspec/changes/` 下的方案草稿与原型 SHALL 静默跳过，不列入「跳过」。被跳过的目录 MUST NOT 参与语言与包管理识别、lint 继承与判断引擎副本的检查，也 MUST NOT 被 `init` 或 `update` 写入。

#### Scenario: 多仓库工作区
- **WHEN** 工作区根目录没有 git、已接入，下面有 3 个独立 git 仓库，各自有 ruff 或 ESLint 配置
- **THEN** check 不要求这 3 个仓库的配置继承基础规则，识别表「跳过」一行列出它们为「另一个仓库」，lint 继承不因它们报缺

#### Scenario: 第三方目录里的 lint 配置
- **WHEN** 项目里有 `static/bower_components/jquery/src/.eslintrc.json`
- **THEN** check 不报它没有引入基础规则，识别表列出 `static/bower_components` 为「第三方目录」，前端目录里也不出现它

#### Scenario: 项目自己的 vendor 目录
- **WHEN** 项目的 `frontend/vendor/` 里只有自己的图片与脚本，没有 `autoload.php` 或 `modules.txt`
- **THEN** 它照常属于本项目，不出现在「跳过」里

#### Scenario: 仓库里的子项目
- **WHEN** 已接入仓库的 `packages/web/` 自己有 `.rulemason.yaml`
- **THEN** 在仓库根运行 check 时不检查 `packages/web/` 下的文件，识别表列出它为「另一个 rulemason 项目」

#### Scenario: 有没有 git 结果一致
- **WHEN** 同一个目录结构（没有被 `.gitignore` 忽略的文件）分别在 git 仓库里与不在 git 仓库里运行 check
- **THEN** 两次的「跳过」一行相同

#### Scenario: 方案里的原型
- **WHEN** `openspec/changes/add-x/prototype/package.json` 依赖 react，没有 ESLint 配置
- **THEN** 前端目录与「React 目录缺少 ESLint」都不出现它，「跳过」一行也不列它
