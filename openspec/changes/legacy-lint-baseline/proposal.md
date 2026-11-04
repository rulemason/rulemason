## Why

给一个已有大量代码的项目（FastAPI 后端 + 两个前端的 monorepo）接入后，继承基础规则的 ruff 报出 2886 个既有问题。检查点要求「运行 ruff，修掉报出的问题后重跑，直到通过」，于是从此每次改动，哪怕只改一行，按规矩都得先修完这 2886 处：AI 要么一口气大改几千处无关代码，要么无视这条规矩，两种都不对。

`/rulemason` 补项目信息时只把 ruff 报出的问题列进汇报、不修代码，没有给出把既有问题收拢成「基线」的办法。这 2886 处里，约 1100 处是可自动修复的 import 排序与未用导入，874 处是 FastAPI 的 `Depends` / `Query` 写法被 B008 误报，318 处是脚本目录里的 `print`；真正要人看的只剩约 600 处。

另外，补项目信息时 skill 会写一节项目「红线」，命令表下面又写「红线规则：暂无」。后者指的是判断用的规则，但两处用同一个词，读起来像是自相矛盾。

## What Changes

- `/rulemason` 补项目信息时，以及已接入项目在日常巡检时，若命令表里的 ruff 报出既有问题，按规则代码分类统计，并给出建立基线的计划，用户确认后写入：
  - 可安全自动修复的规则（import 排序 `I001`、未用导入 `F401`，排除 `__init__.py`）：列出 `ruff check --fix` 命令与预计修复数量，由用户确认后运行，建议单独提交并先跑测试；
  - 框架在参数默认值里调用函数的写法（依赖里有 `fastapi` 或 `typer`）：在项目 ruff 配置加 `extend-immutable-calls`，列出该框架的函数；
  - 脚本与命令行入口目录里的 `T201`：写进 `per-file-ignores` 并注明原因；
  - 其余既有问题：按文件写进 `per-file-ignores`，原因写「接入前遗留，改到该文件时清掉」。
  完成后命令表的 ruff 通过。
- 检查点改为：运行 ruff 时只修本次改动引入的问题；改动前就存在、项目尚未建立基线的问题不修，汇报中列出数量，并建议运行 `/rulemason` 建立基线。改到某个带「接入前遗留」豁免的文件时，顺手清掉该文件的遗留豁免是可选的，不强制。
- skill 写命令表下方的那一行时，改为「判断用的红线规则：暂无（判断未启用；项目红线见上文「红线」一节）」；启用判断后列出规则 id。
- 不做：用 `# noqa` 逐行豁免（与「豁免写在配置里」冲突）；只对改动文件跑 ruff（会漏掉未改文件里新出现的问题，命令也因项目而异）；不经确认自动修复代码；ESLint 的既有问题基线（另开 change）；把框架函数写进共享基础配置（基础配置保持与框架无关，由项目声明）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rules-layer-setup`：补项目信息与日常巡检阶段新增「既有 lint 问题的基线计划」；命令表下方判断用红线规则那一行的写法。
- `workflow-gates`：apply 后与直接改动后运行 ruff 时，只修本次改动引入的问题，既有问题列出并建议建立基线；命令表下方那一行写作「判断用的红线规则」。

## Impact

- 共享正文：`rules/workflow-gates.md`（ruff 步骤的措辞、「红线规则」的定义）；`skills/rulemason/SKILL.md`（补项目信息与日常巡检的基线步骤）。
- 规格：`openspec/specs/rules-layer-setup/`、`openspec/specs/workflow-gates/` 的增量。
- 代码：只改 init 写 AGENTS.md 用的模板 `src/rulemason/templates/AGENTS.md.tmpl` 中那一行，以及断言它的测试；分类统计与配置写入由 skill 指导 AI 完成，不加命令行功能。
- 接入项目：升级并运行 `rulemason update` 后，检查点副本更新；已接入、有大量既有问题的项目（如上述 monorepo）可再运行一次 `/rulemason` 建立基线。
