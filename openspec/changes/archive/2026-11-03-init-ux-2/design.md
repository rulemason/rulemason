## Context

见 proposal.md 的 Why。现状要点：

- `init.plan_lint` 只认 `export default [`，其余写法与 `.eslintrc*` 只给「格式无法自动识别」提示；ruff 的 `extend` 指向别处时只报「已继承其他 ruff 配置」。
- `check.eslint_shared_refs` / `ruff_shared_refs` 只判断「有没有指向正确副本的引用」，引用了不存在文件的情况和「没有继承」混在一起。
- `shared.scan` 遍历全部目录，`openspec/changes/` 下的原型也算项目代码。
- `check.frontend_dirs` 把所有含 `package.json` 的目录当前端；它决定识别表的前端目录与是否复制 `copy-voice.md`。
- `check.version_findings` 只比版本号；`next_stage` 对所有接入缺口都给「运行 rulemason update」。
- `shared.generated_files(tools, rules)` 不含版本号，同一版本生成的内容是确定的，可直接与 `.rulemason.yaml` 的 `files` 校验值比较。

## Goals / Non-Goals

**Goals:**
- 每一项「缺」都能落到一个能让 check 前进的动作上：update 能改的给 update，改不了的给具体手动内容。
- init、update、check 对同一份 lint 配置给同一个判断（能改 / 改不了及原因）。

**Non-Goals:**
- 不解析 JS 语法树，不引入 Node 依赖。
- 不改 `.rulemason.yaml` 的字段。

## Decisions

### D1 ESLint 写法：三个固定锚点

认 `export default [`、`export default defineConfig([`、`export default tseslint.config(`，文件里恰好出现一个锚点才改：前两种在 `[` 后插入 `{ rules: rulemasonBase },`，第三种在 `(` 后插入同一项作为第一个参数；引入语句仍放在第一条 `import` 前。
否决：用 Node 解析语法树——要求每个项目装 Node 且调用外部进程，check 也会变慢。否决：认任意 `export default xxx([`——不认识的包装函数可能不接受普通配置对象，改错比不改更糟。

### D2 引用不存在：改路径，不加行

新增 `check.broken_lint_refs(root, file, text, base_name)`：引用原文的文件名是 `eslint-base.mjs` / `ruff-base.toml`，解析后不是正确副本，且目标不存在或在项目外。check 在 lint 层单独报「引用的基础配置不存在：<原文>」。init / update 只把引号里的路径换成 `config_ref` 算出的正确路径，引入的变量名与用法不动（旧配置写的 `...rulekitBase` 照样可用）。同一文件里已有正确引用、又有坏引用时，不自动删行，作为手动项提示「删去引用 <原文> 的那行及其用法」。
否决：删掉旧行再加新行——要同时找到并删掉变量的所有用法，容易把配置改坏。否决：把坏引用继续算「没有继承」——反馈里正是这样导致用户找不到原因。

### D3 lint 能否自动改：一个判定，三处共用

把 `plan_lint` 里逐个文件的判断抽成 `check.lint_fix(root, file, text) -> LintFix(text | None, note | None)`：`text` 是改好的内容，`note` 是改不了时给人的说明（含要粘贴的内容）。`init.plan_lint` 用它写计划与提示；`check.next_stage` 在接入只剩 lint 层、且这些文件都只有 `note` 时，给 `Next("接入", "manual_lint", "手动修改 <第一个文件>：<note>（update 改不了）")`。
否决：check 调用 update 的计划——`update` 导入 `check`，反过来会循环导入，且 check 不该依赖写入路径的代码。否决：按报错文字匹配判断是否手动——文案一改就失效。

### D4 扫描跳过 openspec/changes/

`scan` 遍历时把相对路径 `openspec/changes` 与 `SKIP_DIRS` 同样静默跳过，git 分支同样按前缀过滤；不写进「跳过」一行。归档数仍由 `archived()` 直接读目录，不受影响。
否决：作为「跳过」的一种原因列出——它不是别的项目，列出来只是噪音。否决：只在前端识别处排除——lint、语言识别会继续误报。

### D5 前端目录：依赖含界面框架，或有 index.html

`react_dirs` 的 `package.json` 读取改为通用的 `package_dirs(root, files, deps)`；`FRONTEND_DEPS = (react, vue, svelte, @angular/core, preact, solid-js, next, nuxt)`；`frontend_dirs(root, files)` = `package_dirs(..., FRONTEND_DEPS)` 加上同目录有 `index.html` 的 `package.json` 目录（试跑发现项目乙的前端不用框架，用户确认加这一条），`react_dirs = package_dirs(..., ("react",))`。语言一行的「JS/TS」不变。
否决：只排除项目根——反馈里 `apps/api` 也有 `package.json`。否决：看有没有 `.tsx` / `.vue` 文件——后端也可能有 `.ts`，文件特征比依赖更不稳定。

### D6 版本落后：比内容

新增 `check.copies_behind(root, sel, files) -> list[str]`：项目记录的版本不高于本机时，用 `generated_files(sel.tools, copied_rules(root, files))` 算出期望的校验值，与清单 `files` 中 `.rulemason/` 与 skill 目录下的记录比较；有不同、多出或缺少的路径时返回一条「副本与本机版本应生成的不一致（N 个文件；…）：运行 rulemason update」，放进「接入 生成副本」层，因而非 0 且下一步为 update。记录版本低于本机、但内容相同时，`version_findings` 写「只有版本号落后，副本内容相同」，`next_stage` 在第一行的动作后附这一句（清单没有副本记录时没法比，不附），下一步不变，退出码 0。记录高于本机时照旧「先升级本机」，不算副本落后。源码仓库自身不比较。
否决：包内常量记「最近改 rules/ 或 lint/ 的版本」——发版时要人记得改，忘了就误判；也覆盖不到 skill 与 README 的变化（用户已确认改为比内容）。

### D7 ruff.toml 位置

`ruff_home(files)`：含 `pyproject.toml` 或 `requirements.txt` 的目录恰好一个、不是项目根，且所有 `.py` 文件都在其中时返回该目录，否则返回项目根。新建的 `ruff.toml` 写在那里，`extend` 用 `config_ref` 算相对路径（模板改为 `$extend` 占位）。命令表的 `ruff check .` 不变：ruff 按文件就近找配置。
否决：每个 Python 目录各放一份——多份配置的豁免要分别维护，超出这次范围。

### D8 update 结尾提示

`update.run` 在 `print_notes` 后、没有 `openspec/` 时打印一行「方案检查点未启用：安装 OpenSpec 并 openspec init 后再运行 rulemason update」，文字与识别表的 openspec 一行共用常量。
否决：update 自动代跑 `openspec init`——会替用户装工作流，与 init-ux-1「不代跑」的决定冲突。否决：只在识别表写——update 不输出识别表，用户在 update 后看不到。

## Risks / Trade-offs

- [前端目录口径收紧后，只有工具 `package.json` 的项目不再复制 `copy-voice.md`] → update 按现有规则删除未改动的旧副本，改过的只报告；在 verification 里记录受影响的接入项目。
- [升级后已接入项目首次 check 报「副本落后」并非 0] → 这是想要的行为；第一行就是「运行 rulemason update」，CI 钉版本时记录与本机一致，不受影响。
- [`tseslint.config(` 后紧跟的不是对象而是展开（`...`）] → 插入的是独立的第一个参数，与后续参数无关；用测试覆盖展开写法。
- [标记块模板跨版本变化不算内容落后（`stale_blocks` 在版本不同时不比较，避免把升级差异当手改）] → 只差版本号时的说法限定为「副本内容相同」，update 照常刷新标记块。
- [版本未变、只因项目新增语言或启用判断也会报「副本与本机版本应生成的不一致」并非 0] → 这是想要的：update 会补上新副本；措辞不说「落后」，免得误导。
- [`openspec/changes/` 里放了真的要检查的代码] → 这里按约定只放方案与原型；如有例外，再按项目反馈开 change。

## Migration Plan

1. 实现并通过 ruff 与测试；在项目甲、乙、丙的 worktree 里分别跑 `rulemason check` 与 `rulemason update --dry-run`，记录前后差异。
2. 发版（0.8.5），接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`。
3. 回滚：`uv tool install rulemason==0.8.4` 后 `rulemason update`，副本与清单回到 0.8.4；本次不改清单格式，回滚无需迁移。

## 文件与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/check.py` | `package_dirs`/`frontend_dirs`、`broken_lint_refs`、`lint_fix`、`copies_behind`、`next_stage`、`render` | +110 / −20 |
| `src/rulemason/init.py` | `plan_lint` 改用 `lint_fix`、`ruff_home` | +20 / −25 |
| `src/rulemason/shared.py` | 扫描跳过 `openspec/changes` | +5 |
| `src/rulemason/update.py` | 结尾提示 | +3 |
| `src/rulemason/templates/ruff.toml.tmpl` | `$extend` 占位 | 1 |
| `tests/test_check.py` | 前端目录、坏引用、副本落后、只差版本号、手动项下一步、跳过 changes | +130 |
| `tests/test_init.py` | 两种 ESLint 写法、改路径、ruff.toml 位置 | +80 |
| `tests/test_update.py` | 无 openspec 结尾、坏引用改正 | +30 |
