## 1. 删代码

- [x] 1.1 删除 `src/rulemason/migrate.py`；`init.py` 去掉迁移预检（`old_manifest`、`migrate.*` 调用、`MigrationError` 分支、残留 notes）。验证：`grep -rn migrate src/` 为空，`uv run rulemason init --plan` 在已接入项目照常输出
- [x] 1.2 `shared.py` 删 `OLD_NAME`、`OLD_MANIFEST`、`OLD_COPY_DIR`，`read_manifest` 去掉 `product` 参数，`SKIP_DIRS` 与 `find_root` 不再认 `.rulekit*`。验证：`grep -rn "OLD_\|rulekit" src/rulemason/shared.py` 为空
- [x] 1.3 `check.py` 删 `legacy_issues`、`residue_*`、`LEGACY_*`、`RESIDUE_*`、`TO_MIGRATE`、`MANAGED_BLOCK`、三个 Next 代码与退出码里的两项。验证：`rulemason check` 在本仓库与一个接入项目的 worktree 里输出不再有「旧接入方式」「旧名残留」两行
- [x] 1.4 `update.py`、`remove.py` 删「旧格式先 init」拦截；`cli.py` init 帮助文字去掉迁移。验证：`rulemason --help`、`rulemason init --help` 不含 rulekit

## 2. 测试、skill 与文档

- [x] 2.1 删除 `tests/test_migrate.py`；`test_check.py`、`test_init.py`、`test_remove.py`、`test_shared.py` 删或改涉及 legacy / 旧清单的用例；`test_templates.py` 的代码清单去掉三项，旧名断言改为对 `src/`、`skills/`、`rules/` 全量检查（豁免 judge 的旧 key 路径）。验证：`uv run pytest` 通过
- [x] 2.2 `skills/rulemason/SKILL.md` 删第二阶段第 0 步与状态表 `legacy`、`migrate`、`fix_residue` 三行，描述去掉迁移。验证：`grep -n "rulekit\|残留" skills/rulemason/SKILL.md` 为空
- [x] 2.3 README 删「从 rulekit 迁移」一节与表里的迁移行；`AGENTS.md` 目录说明去掉迁移逻辑。验证：`grep -n rulekit README.md AGENTS.md` 为空

## 3. 收尾

- [x] 3.1 三个接入项目各开临时 worktree，用开发版运行 `check` 与 `update --dry-run`，对比 0.8.1 的输出只少两行「一致」、退出码相同；主工作区不动。验证：对比结果写进 verification.md
- [x] 3.2 版本改为 0.8.2，过检查点（精简、独立审查、ruff、测试），写 `verification.md`；提交、推送、归档（同步规格），打 tag 发布。验证：`uvx --refresh rulemason@0.8.2 --version`
