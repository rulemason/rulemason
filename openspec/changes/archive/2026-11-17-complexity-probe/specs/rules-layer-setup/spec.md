## ADDED Requirements

### Requirement: 前端复杂度用随 skill 分发的探针统计

存量清理在诊断、改前、改后统计前端函数复杂度时，SHALL 用 skill 目录下的 `complexity-probe.mjs`：以项目自己的 ESLint 运行，阈值与解析插件的来源目录由环境变量给出，只开 `complexity`、不做类型检查。被测文件 SHALL 取自项目 lint 实际检查过的清单；结果的文件数 MUST 与清单一致且没有解析失败或被忽略的条目，否则这次数字不计。在临时 worktree 里取改前数字时，ESLint 与插件 SHALL 借用主工作区，MUST NOT 在 worktree 里装依赖。项目 ESLint 低于 9 时 SHALL 空出这一列并写明原因。

#### Scenario: 全局上限掩盖了超过 15 的函数
- **WHEN** 项目前端的全局复杂度上限是 30，`lint` 不报任何复杂度问题
- **THEN** 诊断用探针以 15 为阈值统计，报出超过 15 的函数个数与最大值，项目的 lint 配置不变

#### Scenario: 项目忽略的文件
- **WHEN** 项目 lint 忽略了一批不是 ES 模块的插件脚本
- **THEN** 探针只测项目 lint 实际检查过的文件，不去解析这些脚本

#### Scenario: worktree 里没有依赖
- **WHEN** 动手之后要在改前提交的临时 worktree 里补取复杂度
- **THEN** 在 worktree 里与主工作区 lint 目录同一层的目录下，用主工作区的 ESLint 运行探针，文件清单用相对路径，`PROBE_ROOT` 指向主工作区，worktree 里不装依赖

#### Scenario: 改前那棵树里没有新建的文件
- **WHEN** 清单里有这次新建的共用模块，要在改前提交的 worktree 里取改前数字
- **THEN** 先去掉清单里在 worktree 中不存在的文件再运行，结果的文件数按去掉后的清单核对

#### Scenario: 项目没装 TypeScript 解析器
- **WHEN** 项目只有 HTML 内联脚本与普通 JS，没有装 `typescript-eslint`
- **THEN** 探针照常统计 JS 与 HTML，输出里写明 TS 文件未测
