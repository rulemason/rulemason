## Context

动机与试跑结论见 proposal.md「Why」。与做法相关的现状：

- skill 副本由 `src/rulemason/shared.py:46` 的 `SKILL_FILES`（现为 `SKILL.md`、`cleanup.md`）决定，`generated_files` 逐个复制，清单、`check` 比对、`update` 补齐都基于它；打包收整个 `skills/rulemason/` 目录（`pyproject.toml` 的 `force-include`）。0.8.39 加 `cleanup.md` 时已走过同一条路。
- `skills/rulemason/cleanup.md` 现为 38 行。诊断的硬指标一行写「读 ruff 与 ESLint 的『接入前遗留』条目和复杂度」（第 25 行），第 2 步先存证据、第 5 步复核都只说「跑命令表的 ruff 或前端 lint」，没有给出数复杂度的命令。
- 试跑（2026-11-18，只读，记录见下）用的探针草稿在会话草稿目录，环境变量 `PROBE_ROOT`（从哪里解析插件）与 `PROBE_MAX`（阈值）：
  - 一个 pnpm monorepo 项目（Next.js、`typescript-eslint`、ESLint 9.39.5）：项目 lint 检查 142 个文件；阈值 10 时，项目配置与探针都报 8 条、最大 15，逐条（文件、行、复杂度）一致。
  - 一个单页 HTML 项目的前端（`index.html` 内联脚本加 JS，`eslint-plugin-html`，没有 `typescript-eslint`）：阈值 10 时两边都报 10 条、最大 27，逐条一致。
  - 不传文件清单时，探针去解析了 3 个被项目 `globalIgnores` 忽略的 Figma 脚本并报解析错误；改为传项目 lint 的文件清单后消失。
  - 在 `HEAD` 的临时 worktree（无 `node_modules`）里，用主工作区的 ESLint、`PROBE_ROOT` 指向主工作区，112 个文件的结果与主工作区同一批文件一致，耗时不到 1 秒。
- 项目 ESLint 低于 9 时，flat 配置要额外的环境变量才能用 `-c`，试跑没有覆盖（未核实）。
- 本仓库 CI 跑在 `ubuntu-latest`（`.github/workflows/ci.yml:19`），本机有 Node 22。

## Goals / Non-Goals

**Goals:**

- 诊断、改前、改后用同一个探针、同一组参数、同一份文件清单，数字前后可比。
- 探针不依赖项目改配置或装新包，只借用项目已装的 ESLint 与插件。

**Non-Goals:**

- 不提供重复统计、死导出、文案集合比对的附带工具（仍按 `cleanup.md` 写的命令或推荐做法）。
- 探针不做 ruff 那一侧；Python 复杂度照旧用 ruff。

## Decisions

1. **探针是一份 ESLint flat 配置，由项目自己的 ESLint 运行**。否决：rulemason 命令行新增 `probe` 子命令。那要 Python 包去调 Node、处理 monorepo 的工作目录，且只有清理流程一个调用方；做成配置文件，复用项目已装的 ESLint，命令写在 `cleanup.md` 里即可。
2. **插件从 `PROBE_ROOT` 用 `createRequire` 解析，装不到就跳过对应文件类型并在标准错误里写明**。否决：在探针里 `import "typescript-eslint"`。配置文件放在 skill 目录（项目里是 `.claude/skills/rulemason/` 等），普通 `import` 从这里往上找不到项目的依赖，试跑前反馈第 39 条踩过这个坑；用 `createRequire` 还能让 worktree 借用主工作区的依赖。
3. **被测文件取自项目 lint 实际检查过的清单，不在探针里复制项目的忽略规则**。否决：探针里加一份通用忽略列表或读取项目配置的 `ignores`。各项目的忽略规则写法不一，复制会走样；试跑里正是项目忽略的文件导致了解析错误。拿项目 lint 的 JSON 输出取文件清单，范围天然一致。
4. **不做类型检查**。否决：沿用项目带类型信息的解析配置。复杂度只看语法结构，不需要类型；带类型检查会按路径读磁盘上的当前文件，正是「改前代码经 stdin」那次出错的原因，而且要 tsconfig 与依赖齐全，worktree 里跑不起来。
5. **项目 ESLint 低于 9 时不用探针**。否决：在 `cleanup.md` 里写 `ESLINT_USE_FLAT_CONFIG=true` 的兼容用法。没有试跑覆盖，写进去等于未验证的承诺；空出这一列并写明原因，与 jscpd 下载失败时的处理一致。
6. **测试用 Node 加载探针、在临时目录里放假的插件包来验证解析逻辑；没有 Node 时跳过**。否决：在测试里装 ESLint 真跑一遍，那要联网下载，且试跑已经在真实项目上逐条比对过。

## 探针草稿

以下是方案阶段的草稿；实现按审查改过（`PROBE_MAX` 必填、只在包本身没装时算未测、`.cjs` 单列、输出用 `process.stderr.write`、`PROBE_ROOT` 按绝对路径展开），以 `skills/rulemason/complexity-probe.mjs` 为准。

```js
// 复杂度探针：只开 complexity、不做类型检查；插件从 PROBE_ROOT 解析，被测文件可以在别处（如临时 worktree）
import { createRequire } from "node:module";
import path from "node:path";

const root = process.env.PROBE_ROOT;
const max = Number(process.env.PROBE_MAX);   // 必填且为正整数，不给默认值
if (!root) throw new Error("需要设置 PROBE_ROOT：装有项目 ESLint 与插件的目录");
const require = createRequire(path.join(root, "package.json"));

function optional(name) {
  try {
    return require(name);
  } catch (error) {
    // 走到这里说明这个包本身没装：对应的文件类型不测，启动时写明；装了却加载失败的照常报错
    if (error.code === "MODULE_NOT_FOUND" && error.message.includes(`'${name}'`)) return null;
    throw error;
  }
}
// …按是否解析到 typescript-eslint、eslint-plugin-html 拼出 JS / TS / HTML 三个配置块，rules 只有 complexity
```

`cleanup.md` 里的命令形如：`PROBE_ROOT=<lint 目录> PROBE_MAX=15 <lint 目录>/node_modules/.bin/eslint -c <本 skill 目录>/complexity-probe.mjs <清单里的相对路径> --format json`，在被测树里与 `<lint 目录>` 同一层的目录下运行，并核对结果文件数与清单一致、没有解析失败或被忽略的条目。

## Risks / Trade-offs

- [项目用 Vue、Svelte 等单文件组件，探针测不到] → 探针只认 JS、JSX、TS、TSX 与 HTML 内联脚本；`cleanup.md` 写明其他类型空出并写原因。
- [项目 ESLint 的位置因包管理器而异] → 命令统一用装有 ESLint 的那个目录下的 `node_modules/.bin/eslint`（npm、pnpm、Yarn 经典模式都有）；不用 `npx eslint`，它在没装依赖的 worktree 里会下载最新版，版本与项目不一致。Yarn PnP 等没有 `node_modules` 的项目空出这一列并写明原因。
- [探针在标准错误里写明测了哪些类型，被当成调试输出] → 这是命令行的正常输出（九条第 6 条的例外），用于在结果里写明哪些类型没测；用 `process.stderr.write` 而不是 `console`，注释写明原因。
- [skill 目录多一个 `.mjs`，接入项目用 `eslint .` 时会扫到它] → 实测：上面的 pnpm monorepo 项目 lint 脚本就是 `eslint .`，用 `--stdin --stdin-filename` 按 skill 目录的路径检查，初版探针的 `console.error` 被 rulemason 基础规则 `no-console` 报 error，会让项目 lint 变红。探针改用 `process.stderr.write`，同样检查退出码 0；测试断言探针源码不出现 `console.`。对所有文件开类型检查（projectService）的项目可能报这个 `.mjs` 不在 tsconfig 里，风险与已分发的 `.rulemason/lint/eslint-base.mjs` 相同，未单独处理。

## Migration Plan

1. 本仓库合并本 change，发补丁版本。
2. 接入项目升级本机 rulemason 后运行 `rulemason update`，各工具 skill 目录补上 `complexity-probe.mjs`。
3. 按 AGENTS.md「额外步骤」，在一个前端接入项目用开发版只读运行 `rulemason update --dry-run`，并用分发后的探针按 `cleanup.md` 的命令跑一次，结果与项目 lint 比对。

回滚：还原本 change 的提交并发补丁版本；接入项目再运行 `rulemason update`，`plan_stale_copies` 删掉未手改的探针文件。

## 新增与修改的文件

| 文件 | 估计改动行数 |
|---|---|
| `skills/rulemason/complexity-probe.mjs`（新增） | 约 40 行 |
| `skills/rulemason/cleanup.md` | 约 4 行 |
| `src/rulemason/shared.py` | 1 行 |
| `tests/test_templates.py` | 约 40 行 |
