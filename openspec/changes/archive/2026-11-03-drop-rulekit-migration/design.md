# Design

## Context

迁移路径散在六个模块里：`migrate.py` 是迁移计划本身；`shared.py` 的 `OLD_*` 常量与 `read_manifest(product=…)` 读旧清单；`check.py` 有旧接入方式识别（`legacy_issues`）、旧名残留巡检（`residue_*`）、`TO_MIGRATE` 标签和三个下一步代码；`init.py` 在预检里调迁移并把残留写进 notes；`update.py` 与 `remove.py` 各有一处「旧格式先 init」的拦截；`cli.py` 帮助文字提到迁移。skill 第二阶段第 0 步处理残留。测试 380 个，其中 `test_migrate.py` 41 处引用、其余文件约 30 处。

## Goals / Non-Goals

**Goals:**

- 删完后代码、skill、文档、规格里不再出现迁移路径；`check` 的下一步代码表少三项。
- 已迁移项目的行为不变：`check` 对它们的输出只少「旧接入方式」「旧名残留」两行「一致」。

**Non-Goals:**

- 不动 judge 的旧 key 位置兜底；不改规格 id；不改 0.6.x 模板副本清理。

## Decisions

### 1. 一次删干净，不留「已弃用」过渡

直接删除代码、测试与规格，不保留任何「检测到 `.rulekit.yaml` 时提示去装旧版本」的提示。

**否决：** 留一条「发现 `.rulekit.yaml`：请先用 rulemason 0.8.1 迁移」的提示。它要继续认识旧清单名，等于保留一半识别代码；已知没有任何项目处于该状态，提示没有受众。

### 2. 规格：整条删用 REMOVED；涉及迁移的场景改写成「删掉迁移后这种情况怎么办」

三条整条围绕迁移的要求用 REMOVED。另外十条用 MODIFIED：OpenSpec 1.15 的 `validate --strict` 规定 MODIFIED 必须保留现有的每个场景名，同名 REMOVED 加 ADDED 也算冲突，也就是 delta 里不能删场景。于是描述旧格式、旧引用、旧名的六个场景不删，改写成删掉迁移路径之后的实际行为（`.rulekit.yaml` 当作没有清单、`../rulekit/` 引用不再拦截、旧名不再报告）。这正好把 Risks 里「某台机器仍有 `.rulekit.yaml`」的行为写成了规格。场景名是情境标签，保持不变。

**否决：** 用 REMOVED 删整条，再用新名字 ADDED 回来。能绕过校验，但等于给六条要求改名，波及引用这些标题的文档，超出本 change。

**否决：** 把迁移句子当独立要求 REMOVED。它们不是独立要求，对不上主规格的标题。

### 3. `read_manifest` 去掉 `product` 参数

现在 `product` 只为了读 `.rulekit.yaml`；删掉后函数只读 `.rulemason.yaml`，调用处同步。

**否决：** 保留参数以备「以后再改名」。没有调用方的参数，按九条第 9 条不留。

### 4. 下一步代码表删三项，不改其余代码的名字与顺序

`legacy`、`migrate`、`fix_residue` 删除；`fix_manifest`、`init`、`fix_gitignore`、`update`、`fill_project_info`、`none`、`upgrade_*` 不变，skill 表与 `test_templates` 的代码清单同步。

**否决：** 趁机给代码表改名或重排。会波及接入项目里已复制的 skill 副本与依赖 `next.code` 的脚本，超出本 change。

## Risks / Trade-offs

- [某台未知机器仍有 `.rulekit.yaml` 项目] → 0.8.2 会把它当未接入项目，`init` 会在旧副本旁再生成一套；用户可先用 0.8.1 迁移。已知为零，README 不再提。
- [`test_no_old_names_outside_migration_context` 的豁免范围随迁移上下文一起消失] → 改为对 `src/`、`skills/`、`rules/` 断言不含 `rulekit`、`jev-judge`，豁免只剩 judge 的旧 key 路径与规格 id。
- [删 `residue` 后，init-ux-2 的「引用路径存在性检查」失去一处可复用的候选文件列表] → 那条检查按自己的需求重写候选集，不依赖本处。

## Migration Plan

1. 删代码与测试，改 skill 与文档，同步规格；ruff 与 pytest 通过。
2. 在三个接入项目的临时 worktree 里用开发版运行 `check` 与 `update --dry-run`，确认输出只少两行「一致」，退出码不变。
3. 归档，版本 0.8.2，推 tag 发布。

回滚：revert 即可；0.8.1 仍在 PyPI。

## 文件与估计行数

| 文件 | 变化 | 估计行数 |
|---|---|---|
| `src/rulemason/migrate.py` | 删除 | −97 |
| `tests/test_migrate.py` | 删除 | −231 |
| `src/rulemason/check.py` | 删 legacy / residue / TO_MIGRATE / 三个 Next | −60 |
| `src/rulemason/init.py` | 删迁移预检与 notes | −20 |
| `src/rulemason/shared.py` | 删 OLD_* 与 product 参数 | −15 |
| `src/rulemason/update.py`、`remove.py`、`cli.py` | 各删一处 | −8 |
| `skills/rulemason/SKILL.md` | 删第 0 步与三行代码表 | −12 |
| `README.md`、`AGENTS.md` | 删一节、一行 | −23 |
| `tests/test_check.py`、`test_init.py`、`test_remove.py`、`test_shared.py`、`test_templates.py` | 删或改迁移用例 | −60 / +10 |
| `openspec/specs/rulekit-cli/spec.md`、`rules-layer-setup/spec.md` | 归档时合并 | −50 |
