## REMOVED Requirements

### Requirement: init 从 rulekit 格式迁移

**Reason**: rulekit 0.5 只有作者本人用过，所有项目已迁到 rulemason 0.8.x；迁移路径没有受众。
**Migration**: 仍持有 `.rulekit.yaml` 的项目先用 rulemason 0.8.1 运行 `rulemason init` 迁移，再升级。

### Requirement: 迁移前核对旧副本，标记块外只报告

**Reason**: 随迁移路径一起删除。
**Migration**: 同上。

### Requirement: check 报告旧名残留

**Reason**: 旧名只在迁移后出现；迁移路径删除后不再有残留需要巡检。
**Migration**: 无；已迁移项目的残留已在迁移时处理完。

## MODIFIED Requirements

### Requirement: init 预检

`rulemason init [path]` SHALL 按「项目根按最近的 .rulemason.yaml 确定」找项目根；给出 `path` 时以该路径为项目根。不要求 git。没有 git 时 MUST 提示「无法用 diff 查看改动、副本无法通过仓库共享」后继续。没有 `openspec/` 时 MUST 先询问；用户同意后以同一份工具选择运行 `openspec init --tools <所选> --language zh-CN`，用户拒绝或本机没有 `openspec` 命令时 MUST 说明原因并停止，不写任何文件。`init` MUST NOT 识别 rulekit 0.5 的 `.rulekit.yaml`、`.rulekit/` 或 `../rulekit/` 引用：这些文件当作项目自己的内容，不读、不删、不改。

#### Scenario: 空目录新项目
- **WHEN** 在一个既没有 git 也没有 `openspec/` 的目录运行 `rulemason init`，用户同意运行 openspec init
- **THEN** 先提示没有 git，再运行 `openspec init --tools <所选> --language zh-CN`，之后继续完成 rulemason 接入；`openspec/config.yaml` 的 `context` 含 zh-CN 语言声明

#### Scenario: 本机没有 openspec
- **WHEN** 项目没有 `openspec/`，且 `openspec` 命令不存在
- **THEN** 输出 openspec 的安装方法并停止，项目中没有新文件

#### Scenario: 旧接入方式的项目
- **WHEN** 在 `AGENTS.md` 引用 `../rulekit/rules/` 的项目运行 `rulemason init`
- **THEN** 照常接入，不因该引用停止；旧引用留在原处，由用户自行清理

#### Scenario: rulekit 0.5 格式的项目
- **WHEN** 在有 `.rulekit.yaml`、没有 `.rulemason.yaml` 的项目运行 `rulemason init`
- **THEN** 当作尚未接入的项目接入：新生成 `.rulemason/` 与 `.rulemason.yaml`，`.rulekit.yaml` 与 `.rulekit/` 原样保留，计划里不出现它们

### Requirement: update 刷新副本

`rulemason update` SHALL 用当前安装的版本刷新 rulemason 自己管的文件（`.rulemason/` 副本、skill 副本、已有的标记块与 `.rulemason.yaml`），MUST NOT 提问选工具。缺的配置（ruff / ESLint 继承、基础 rules、workflow-gates 规格、缺的标记块）SHALL 按 `init` 的规则补齐：先列计划，交互确认或带 `--yes` 才写；非交互且没有 `--yes` 时 MUST NOT 修改，只列为「待补齐」。`update` SHALL 删除清单记录过、不再生成且未改的旧副本，改过的只报告；被手改的副本与块 SHALL 列出。`update` MUST NOT 修改标记块以外的命令表、红线或判断层文件。

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

### Requirement: check 只读检查并以退出码报告

`rulemason check` SHALL 只读，不要求 git，输出识别表、各层状态、巡检结果与下一步。以下任一情况 MUST 以非 0 退出：已选工具入口缺失、生成副本与 `.rulemason.yaml` 记录的校验值不符、标记块与当前模板不一致、项目在 git 仓库里而生成副本被 `.gitignore` 忽略、ruff 或 ESLint 未继承 `.rulemason/lint/`。`.rulemason.yaml` 记录的版本低于当前安装版本时 SHALL 报告落后，但不单独导致非 0 退出。判断层未启用 MUST NOT 被报告为缺，SHALL 显示「可选，未启用」与启用条件。巡检 MUST NOT 含「旧接入方式」与「旧名残留」两项。

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

### Requirement: 项目根按最近的 .rulemason.yaml 确定

`rulemason init`、`update`、`check` SHALL 从当前目录往上找最近的 `.rulemason.yaml`，以它所在目录为项目根；向上查找 MUST NOT 越过当前目录所在 git 仓库的根目录。找不到时，`init` SHALL 以所在 git 仓库的根为项目根，不在 git 里则以当前目录为项目根；`check` 与 `update` SHALL 报告「先运行 rulemason init」并写明判断出的项目根。`rulemason init <path>` 显式给出路径时 SHALL 以该路径为项目根，不再向上查找。

#### Scenario: 在已接入项目的子目录运行
- **WHEN** 在已接入项目的 `app/` 子目录运行 `rulemason check`
- **THEN** 以项目根目录检查，结果与在项目根运行相同，不提示「先运行 rulemason init」

#### Scenario: 在子目录运行 init
- **WHEN** 在一个尚未接入的 git 仓库的 `web/src/` 目录运行 `rulemason init --tools claude --yes`
- **THEN** 在仓库根目录接入，`web/src/` 下不出现 `.rulemason.yaml` 或 `.rulemason/`

#### Scenario: 工作区里的独立仓库
- **WHEN** 工作区根目录已接入（有 `.rulemason.yaml`），在其中一个独立 git 仓库 `app-a/` 里运行 `rulemason check`
- **THEN** 不向上找到工作区的 `.rulemason.yaml`，报告 `app-a/` 尚未接入，提示「先运行 rulemason init」

#### Scenario: 显式给出路径
- **WHEN** 运行 `rulemason init packages/web --tools claude --yes`
- **THEN** 以 `packages/web/` 为项目根接入，不向上查找

### Requirement: 子仓库、子项目与第三方目录不属于本项目

列项目文件时，以下子目录 SHALL 视为不属于本项目、整个跳过：含 `.git` 的子目录（另一个 git 仓库，含子模块）、含 `.rulemason.yaml` 的子目录（另一个 rulemason 项目）、名为 `bower_components`、`uni_modules`、`third_party`、`jspm_packages`、`Pods` 的目录，以及含 Composer 的 `autoload.php` 或 Go 的 `modules.txt` 的 `vendor` 目录（第三方代码；没有这些标记的 `vendor` 属于项目自己）。项目在 git 仓库里与不在 git 仓库里时，跳过的结果 MUST 相同。被跳过的目录 MUST NOT 参与语言与包管理识别、lint 继承与判断引擎副本的检查，也 MUST NOT 被 `init` 或 `update` 写入。

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

### Requirement: check 第一行给结论与下一步

`rulemason check` 输出的第一行 SHALL 是结论与下一步要做的事，下一步 SHALL 按原因给出具体命令或动作，同时有多个原因时按以下顺序取第一个：清单无效 → 先修正清单；尚未接入 → `rulemason init`；生成副本被 `.gitignore` 忽略 → 修改 `.gitignore` 放行 `skills/rulemason/`；副本或标记块与模板不一致、入口缺失、配置待补齐 → `rulemason update`；项目信息待补 → `/rulemason`；版本落后 → `rulemason update`。阶段名 SHALL 使用：接入、补项目信息、日常巡检；判断相关为可选的「整理判断规则」「启用判断」。`next.code` MUST NOT 再出现 `legacy`、`migrate`、`fix_residue`。

#### Scenario: 刚接入的项目
- **WHEN** 刚运行完 `rulemason init`，项目简介与红线待补
- **THEN** 第一行写「补项目信息：在 AI 工具中运行 /rulemason」

#### Scenario: 副本被忽略
- **WHEN** skill 副本被 `.gitignore` 忽略
- **THEN** 第一行的下一步是修改 `.gitignore` 放行 `skills/rulemason/`，而不是 `rulemason update`

#### Scenario: 一切就绪
- **WHEN** 项目接入完整、项目信息已补、没有任何偏离
- **THEN** 第一行写「日常巡检：一切一致」，退出码为 0

### Requirement: init --plan 只列计划不写入

`rulemason init --plan` SHALL 按 `init` 的同一套规则算出文件计划（含取消工具的删除、补齐配置），打印后以 0 退出；MUST NOT 写入或删除任何文件、MUST NOT 提问、MUST NOT 运行 `openspec init`，在非交互环境也可运行。没带 `--tools` 时 SHALL 用清单记录的工具，没有清单则按项目已有的工具目录推断。项目没有 `openspec/` 时，计划 SHALL 写明「将先运行 openspec init」。预检不通过时 SHALL 照常报告并以对应的非 0 退出码退出。

#### Scenario: AI 会话里先看计划
- **WHEN** 在非交互环境、尚未接入的项目运行 `rulemason init --plan`
- **THEN** 打印将新增的文件清单，退出码为 0，项目中没有任何文件变化

#### Scenario: 迁移计划的 JSON
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `rulemason init --plan --json`
- **THEN** 与尚未接入的项目相同：`writes` 含 `.rulemason.yaml`，`deletes` 为空、不含 `.rulekit.yaml` 或旧副本，项目中没有任何文件变化

#### Scenario: 没有 openspec
- **WHEN** 在没有 `openspec/` 的目录运行 `rulemason init --plan --json`
- **THEN** `openspec_init` 为 true，不运行 openspec，不创建 `openspec/`
