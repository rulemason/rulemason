# 验证记录：complexity-probe

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前的判断 | `rulemason judge --change complexity-probe`：pass 3 / review 0 / block 0 |
| 1. 自动精简 | 按 `CLAUDE.md` 用 `/simplify`，范围是 `complexity-probe.mjs`、`shared.py` 与测试（`cleanup.md` 是文档，不在范围内）。四个角度各一个子代理，处理见下 |
| 1. 独立审查 | 审查者只读一份材料文件，以「照着 `cleanup.md` 用探针的代理」的身份读。第一轮 block 1 / review 8，修复后第二轮 block 0 / review 6，修完不再审 |
| 2. ruff | `uv run ruff check .`：All checks passed |
| 3. 测试 | `uv run pytest`：770 passed（新增 3 条探针测试；需要 Node 的两条在没有 Node 时跳过）。没有改判断规则文件或 `JEV_MODEL`，不跑判断回归 |
| 4. 前端 lint | 本仓库无前端，跳过 |
| 5. 文案检查 | 本仓库无界面文案，跳过 |
| 6. 额外步骤 | 见下「接入项目验证」 |
| 打包 | `uv build --out-dir <仓库外临时目录>`：wheel 含 `rulemason/_shared/skills/rulemason/complexity-probe.mjs`，与仓库里的文件逐字一致 |
| change 校验 | `openspec validate complexity-probe --strict`：valid。改到的两条 requirement 正文分别为 468 字与 301 字，都在 500 字以内（MODIFIED 的长度 change 校验不查，起草时先量过） |

## 接入项目验证

全程只读，两个项目运行前后 `git status` 都不变。

- **与项目 lint 逐条比对**：用最终版探针，按 `cleanup.md` 的写法（相对路径、只留探针认的类型、去掉不存在的文件），与项目自己的 lint 在阈值 10、同一份文件清单下比对文件、行号、复杂度：
  - pnpm monorepo 项目（Next.js、`typescript-eslint`，ESLint 9.39.5）：清单 142 个、结果 142 个，一致 9 条，两边各自独有 0 条。
  - 单页 HTML 项目（`index.html` 内联脚本加 JS，`eslint-plugin-html`）：清单 3 个、结果 3 个，一致 10 条，0、0。
- **临时 worktree 取改前数字**：在 `HEAD` 的 worktree（没有 `node_modules`）里，ESLint、`PROBE_ROOT`、`-c` 都用主工作区的绝对路径。清单 142 个里有 10 个是工作区新建、worktree 里没有的文件，去掉后传入 132 个、结果 132 个，没有解析失败或被忽略的条目。
- **项目自己的 lint 扫到探针**：pnpm monorepo 项目的 lint 脚本是 `eslint .`。用 `--stdin --stdin-filename` 按 `.claude/skills/rulemason/complexity-probe.mjs` 与 `.agents/skills/rulemason/complexity-probe.mjs` 检查最终版探针，退出码都是 0。另一个项目的 lint 只扫列出的目录，不受影响；其余两个接入项目的 lint 不覆盖 skill 目录，或没有前端。

## 自动精简的取舍

采纳（都不改行为）：

- 去掉探针里的 `ignores` 块：ESLint 默认忽略 `node_modules`，范围只由传进来的文件清单决定（复用、简化、层级三份审查）。
- `PROBE_MAX` 改为必填，不给默认值 15，免得忘了传时悄悄用了不同的阈值（层级审查）。
- 规则只写一处：`complexity` 放在一个不限文件类型的块里；TS 块复用 `jsOptions`；「未测」挪进已有的 `if` 分支；HTML 块拆成多行（简化审查）。
- 测试只断言约定的行为：规则只有 `complexity`、装了才有解析器和插件，不数配置块个数，也不输出没用到的 `files` 字段；环境变量只写一次；改用 `tests/conftest.py` 的 `write` 写假包（简化、层级、复用审查）。

不采纳：

- 直接加载 `@typescript-eslint/parser` 以省一次加载：pnpm 等不提升依赖的布局下常常解析不到，反而会误报「TS 未测」（效率审查本身也建议保留）。
- 三次启动 Node 合成一次：省 0.1–0.2 秒，测试会变脆。

## 独立审查的处理

第一轮：

- **B1**：worktree 里照抄主工作区的绝对路径，数字会变 0，或测到改后的文件。处理：`cleanup.md` 写明换成相对路径、在同一层目录下运行，并核对结果文件数与清单一致、没有解析失败或被忽略的条目，否则不算；规格新增 requirement 同步写明。
- **R1**：规格场景「旧项目升级后补上清理正文」改为「skill 的文件都在」。场景名「skill 副本只有一个文件」OpenSpec 不允许在 MODIFIED 里改名，保留。
- **R2**：计数一致的前提同 B1；另写明项目的 `complexity` 配了 `variant` 时空出这一列。
- **R3**：`PROBE_ROOT` 的含义写准确（见第二轮第 4 条的最终写法）。
- **R4**：`optional()` 只在包本身 `MODULE_NOT_FOUND` 时算未测，其余照常抛出；新增测试。
- **R5**：`PROBE_MAX` 必须为正整数并单独报错；`.cjs` 单列为 CommonJS；测试覆盖空串、非数字、0、负数、小数。
- **R6**：design 里的项目名换成泛称。
- **R7**：测试覆盖见 R4、R5。
- **R8**：审查标为 review，实现者实测后按 block 处理。初版探针的 `console.error` 会被接入项目 `eslint .` 的 `no-console` 报 error，让项目 lint 变红。改用 `process.stderr.write`，并新增测试断言探针源码不出现 `console.`；design 里那条未经验证的风险说法按实测改写。

实现者实走 `cleanup.md` 时另外发现一处：清单里有工作区新建、改前那棵树里没有的文件，ESLint 会整次报错退出。处理：`cleanup.md` 补「去掉在被测的那棵树里不存在的文件」，规格补场景「改前那棵树里没有新建的文件」。

第二轮：

1. 清单只留探针认的扩展名，再去掉报「未测」的类型；去掉的类型与文件在汇报里写明。
2. 只数 `ruleId` 为 `complexity` 的条目。有函数超标时退出码是 1，「找不到规则定义」、未用的 disable 注释这类条目都不算失败；输出用 `-o` 写到仓库外临时文件。核实：在没有 `eslint-disable` 注释的项目上，结果里确实没有这类条目；别的项目常见这类注释，所以照写。
3. `PROBE_ROOT`、`<eslint>`、`-c` 都用主工作区的绝对路径。另外实测相对路径的 `PROBE_ROOT` 会让 `createRequire` 报 `ERR_INVALID_ARG_VALUE`，探针改为先用 `path.resolve` 展开，并补测试。
4. `<lint 目录>` 与 `<eslint>` 分开说：后者是从 `<lint 目录>` 往上最近的 `node_modules/.bin/eslint`。
5. 这次改名或删掉的文件，用 `git diff --name-status <改前提交>` 把旧路径补进改前清单。
6. tasks 1.2 与 design 草稿按实现同步，草稿处注明以实现为准；design 补一句：对所有文件开类型检查的项目可能报这个 `.mjs` 不在 tsconfig 里，风险与已分发的 `eslint-base.mjs` 相同。

## 改既有测试

- `test_skill_is_body_files_and_templates_ship_with_engine`：skill 文件清单从两个改为三个，与规格改动一致，没有放宽。
- `test_skill_legacy_cleanup_section`：原有短语一个没删，只在列表末尾追加探针用法的 5 个短语。

## 估计行数对照

| 文件 | 估计 | 实际 |
|---|---|---|
| `skills/rulemason/complexity-probe.mjs`（新增） | 约 40 | 61 |
| `skills/rulemason/cleanup.md` | 约 4 | 增 10 / 删 3 |
| `src/rulemason/shared.py` | 1 | 1 / 1 |
| `tests/test_templates.py` | 约 40 | 增 68 / 删 2 |

`cleanup.md` 超出估计一倍以上：两轮审查补了取清单、运行、数结果三步的细节（相对路径、扩展名过滤、去掉不存在的文件、结果核对、只数 complexity），并改成分条写，方便代理照着操作。探针与测试在估计的一倍以内。

## 发版说明草稿

- `/rulemason` 的 skill 新增 `complexity-probe.mjs`：只开 `complexity`、不做类型检查的 ESLint 配置，存量清理在诊断、改前、改后数前端函数复杂度时用它。用法写在 `cleanup.md` 的「复杂度探针」一段，由项目自己的 ESLint 运行，不改项目配置、不装新包。
- 接入项目运行 `rulemason update` 补上这个文件。它在 `.claude/skills/`、`.agents/skills/` 下，项目用 `eslint .` 时会被扫到，已确认不会触发 rulemason 基础规则报错。
