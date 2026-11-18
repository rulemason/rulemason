## Why

存量清理要在诊断、改前、改后三处数前端函数的复杂度。接入项目一般把全局上限设在 30 之类，`lint` 看不到超过 15 的函数，每个模块都得手写只开 `complexity` 的临时 ESLint 配置：从应用目录解析 TypeScript 解析器、避开带类型检查的配置、在临时 worktree 里装依赖。同一个项目 5 个模块各写一遍，还错过两次（改前代码经 stdin 交给带类型检查的配置；参数不同的统计没法比）。0.8.41 的清理流程已经写明「前后用同一条命令、同一组参数、同一个范围」，现在补上这条命令。

在两个接入项目上只读试跑过：同一份文件清单下，探针与项目自己的 lint 逐条一致（TSX 8 条、HTML 内联脚本 10 条）；在不装依赖的临时 worktree 里借用主工作区的 ESLint 与解析器，结果与主工作区一致。

## What Changes

- skill 目录新增 `complexity-probe.mjs`：只开 `complexity`、不做类型检查的 ESLint 配置。阈值与解析插件的来源目录由环境变量给出；从该目录解析 `typescript-eslint` 与 `eslint-plugin-html`，项目没装的文件类型不测并在输出里写明。
- skill 副本从两个文件变成三个，`init` / `update` 一并复制，`check` 照常比对。
- `cleanup.md` 写明用法：用项目自己的 ESLint 运行探针；被测文件取自项目 lint 实际检查过的清单；诊断、改前、改后都用同一条命令与同一组参数；在临时 worktree 里取改前数字时，ESLint 与 `PROBE_ROOT` 都指向主工作区，不在 worktree 里装依赖；项目 ESLint 低于 9 时不用探针，空出这一列并写明原因。
- 不做：前端死代码诊断。knip 试跑结论是不放进 skill：它会执行项目的配置文件，配置加载失败时照样输出并误报，扫描范围与 lint 不一致。
- 不做：探针不支持 Vue、Svelte 等单文件组件，不改项目的 lint 配置，不写进项目依赖。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `rulekit-cli`：skill 副本包含正文与附带文件三个文件。
- `rules-layer-setup`：前端复杂度用随 skill 分发的探针统计。

## Impact

- 新增 `skills/rulemason/complexity-probe.mjs`；改 `src/rulemason/shared.py` 的 skill 文件清单、`skills/rulemason/cleanup.md`、`tests/test_templates.py`，以及相关测试。
- 打包无需改动：整个 `skills/rulemason/` 已收进安装包。
- 接入项目运行 `rulemason update` 后补上探针文件；`check` 在升级前会报副本落后，这是预期行为。
