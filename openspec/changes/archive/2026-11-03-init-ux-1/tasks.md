## 1. 基础：颜色与按语言生成副本

- [x] 1.1 `shared.py` 新增 `paint(text, code)`（看 `NO_COLOR` 与标准输出是否终端）与颜色常量，`banner.py` 改用它。验证：`test_banner` 全部通过，`NO_COLOR=1` 时输出无转义
- [x] 1.2 `shared.generated_files` 改为按语言选取副本（`code-style`、`workflow-gates`、`README` 固定；python / ruff、react / eslint、copy-voice 按条件），`init` 与 `update` 传入项目信息；README 模板按实际生成的文件写清单。验证：Go 项目 init 后 `.rulemason/` 只有 3 个文件且 `check` 一致；加 `pyproject.toml` 后 `update` 补上 python.md 与 ruff-base

## 2. 工具选择器

- [x] 2.1 新建 `src/rulemason/select.py`：cbreak 读单键，上下 / j k 移动，空格切换，`a` 全选，回车确认，`q` 取消，不支持时抛 `Unsupported`；`finally` 恢复终端。验证：`tests/test_select.py` 用假的按键序列驱动，覆盖移动、切换、全选、空选提示、取消
- [x] 2.2 `init.ask_tools` 改用选择器：首次全不勾并标注「检测到」，重跑预勾清单工具；`Unsupported` 时退回编号输入。验证：`test_init` 选工具一节用假选择器与编号退路各一组

## 3. 计划摘要与收尾

- [x] 3.1 `render_summary` 与 `[y/N/d]` 确认流程；`--plan`、`remove` 保持完整清单。验证：测试覆盖「d 展开后再问」「直接 y」「N 不写」
- [x] 3.2 `report` 改为第一行 + 需要你处理 + 下一步；ESLint note 附可粘贴代码；配色。验证：写入后输出不含「识别表」「各层状态」
- [x] 3.3 `plan_gitignore`：skill 副本被忽略时把放行规则列进「修改」。验证：`.gitignore` 为 `.claude/` 的项目 init 后 `check` 不报副本被忽略

## 4. 无 OpenSpec 分层、预填、key 引导

- [x] 4.1 `ensure_openspec` 返回是否有 openspec；`--yes`、拒绝或无命令时只装读层，workflow-gates 块用「未接 OpenSpec」模板，结尾说明；`update` 在 openspec 出现后补齐并换回正常块。验证：`--yes` 无 openspec 的项目里没有 `openspec/`，AGENTS.md 块写明未启用；补 `openspec/` 后 `update --yes` 写入 config rules 与规格
- [x] 4.2 新建 `AGENTS.md` 时预填简介与红线「暂无」；已有文件不动。验证：有 README、无 README、已有 AGENTS.md 三组用例
- [x] 4.3 `check.judge_label` 条件满足且无 key 时提示 `rulemason key` 与申请地址；`init` 结尾按条件提问或提示，y 调 `key.run()`；`banner.COMMANDS` 加 key 一行；命令表模板「判断层未装」改「可选，未启用」。验证：三种条件各一组用例，非交互与 `--yes` 不提问

## 5. 文档与收尾

- [x] 5.1 `skills/rulemason/SKILL.md` 第二阶段第 1 步改为核对预填简介、第 4 步措辞；README「第一次接入」「升级」按新行为改写（含「update 会删掉用不到的副本」）。验证：`test_templates` 通过，`grep 判断层未装` 只剩规格历史
- [x] 5.2 临时目录手工试：交互 init（空格选工具、`d` 展开）、`--yes` 无 openspec、Go 项目、有 README、`.gitignore` 挡副本；三个接入项目 worktree 跑 `update --dry-run` 与 `check`。验证：结果写进 verification.md
- [x] 5.3 版本 0.8.4（先看 `git tag` 与 PyPI），过检查点（精简、独立审查、ruff、测试），写 `verification.md`；提交、推送、归档、打 tag 发布。验证：`uvx --refresh rulemason@0.8.4 --version`
