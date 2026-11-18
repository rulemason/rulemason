## 1. 先写会失败的测试

- [x] 1.1 `tests/test_templates.py`：skill 目录与 `SKILL_FILES` 都是 `SKILL.md`、`cleanup.md`、`complexity-probe.mjs`；`cleanup.md` 含探针用法的关键短语（`complexity-probe.mjs`、`PROBE_ROOT`、「项目 lint 实际检查过的」、「不在 worktree 里装依赖」、「低于 9」）。验证：`uv run pytest tests/test_templates.py` 只有这些断言失败。
- [x] 1.2 `tests/test_templates.py` 新增探针加载测试（没有 Node 时跳过）：`PROBE_ROOT` 指向空临时目录、`PROBE_MAX=12` 时，规则只有 `complexity: ["error", 12]`、不带解析器与插件，标准错误写明 TS 与 HTML 未测；在临时目录放假的 `typescript-eslint` 与 `eslint-plugin-html` 包后，带上解析器与 html 插件，规则仍只有 `complexity`；`PROBE_ROOT` 为空时报错，相对路径可用；`PROBE_MAX` 为空、非数字、0、负数、小数时报错；装了但加载失败的包照常报错，不写成「未测」；探针源码不出现 `console.`（实现中按两轮审查补全）。验证：此时失败（文件还不存在）。

## 2. 探针与分发

- [x] 2.1 新建 `skills/rulemason/complexity-probe.mjs`，按 design 草稿与九条写法（首行用途、中文注释、「走到这里说明」）。验证：1.2 通过。
- [x] 2.2 `src/rulemason/shared.py` 的 `SKILL_FILES` 加入 `complexity-probe.mjs`。验证：1.1 中文件清单断言通过；`uv run pytest tests/test_init.py tests/test_check.py` 通过。
- [x] 2.3 `cleanup.md`：加一段探针用法（命令、文件清单取自项目 lint、worktree 借用主工作区、只认 JS/JSX/TS/TSX/HTML、ESLint 低于 9 空出并写原因），诊断硬指标与第 2、5 步改为引用它。验证：1.1 全部通过，`cleanup.md` 不超过 70 行。

## 3. 检查点与验证

- [x] 3.1 按 `rules/workflow-gates.md`「apply 最后一个任务做完」执行：自动精简、独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果写进 `verification.md`。
- [x] 3.2 额外步骤：在一个前端接入项目用开发版只读运行 `rulemason update --dry-run`；并用本仓库的 `complexity-probe.mjs` 按 `cleanup.md` 的命令跑一次，与项目 lint（同阈值、同文件清单）逐条比对；再用项目自己的 lint 按 skill 目录的路径检查探针文件（`--stdin --stdin-filename`），确认不报错。验证：比对一致、探针不被项目 lint 报错、项目 `git status` 前后不变，记录进 `verification.md`。
- [x] 3.3 构建一次安装包，确认 wheel 里有 `rulemason/_shared/skills/rulemason/complexity-probe.mjs`；`openspec validate complexity-probe --strict` 通过；在 `verification.md` 写发版说明草稿。
