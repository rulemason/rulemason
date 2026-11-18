## 1. 先写会失败的测试

- [x] 1.1 `tests/test_templates.py`：skill 目录断言改为 `["SKILL.md", "cleanup.md"]`；`test_skill_legacy_cleanup_section` 的切片来源改为 `cleanup.md`（短语一个不少）；新增断言：`SKILL.md` 第 7 节点名 `cleanup.md` 且不再含「**先存证据**」等清理步骤，`cleanup.md` 含 `refactor(cleanup-step):` 与「只有最后一次」。验证：`uv run pytest tests/test_templates.py` 只有这些断言失败。
- [x] 1.2 `tests/test_check.py` 加一条（用现成的 `inited` 夹具）：只记录了 `SKILL.md` 的旧清单，`check` 在「接入 生成副本」报出副本与本机版本应生成的不一致，`update` 后补齐且清单记录二者。验证：此时失败。

## 2. 搬家与分发

- [x] 2.1 新建 `skills/rulemason/cleanup.md`：第 7 节正文逐字搬入，开头加一句说明文中「第 1 节」「第 8 节」指同目录 `SKILL.md` 的章节（原计划逐处改写，其中两处被测试按原文断言，改为加一句说明）。验证：`diff` 搬入前后的正文，只有完成标记两处不同。
- [x] 2.2 `cleanup.md` 的完成标记一段补上阶段提交的写法，收尾要求提交处写明完整提交说明。验证：1.1 的相关断言通过。
- [x] 2.3 `SKILL.md` 第 7 节换成入口一段（读本 skill 目录下的 `cleanup.md`，没读到就停下说明）。验证：`SKILL.md` 第 1 节第 35 行未动；1.1 全部通过。
- [x] 2.4 `src/rulemason/shared.py` 的 `SKILL_FILES` 加入 `cleanup.md`，注释同步。验证：1.2 通过；`uv run pytest tests/test_init.py tests/test_check.py` 通过。
- [x] 2.5 测量 `cleanup.md` 行数，与 70 行上限对照。验证：不超过；超过时只把上限改为实测值并在测试旁注明原因，汇报写明。

## 3. 检查点与验证

- [x] 3.1 按 `rules/workflow-gates.md`「apply 最后一个任务做完」执行：自动精简、独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果写进 `verification.md`。
- [x] 3.2 额外步骤：在一个接入项目用开发版只读运行 `rulemason update --dry-run` 与 `rulemason check`。验证：只多出 `cleanup.md` 与 `SKILL.md` 的变化，项目 `git status` 前后不变；记录进 `verification.md`。
- [x] 3.3 构建一次安装包，确认 wheel 里有 `rulemason/_shared/skills/rulemason/cleanup.md`。验证：`uv build` 后用 `unzip -l` 列出。
- [x] 3.4 `openspec validate skill-cleanup-file --strict` 通过，并在 `verification.md` 写发版说明草稿（接入项目运行 `rulemason update` 补上 `cleanup.md`；分阶段清理的提交写法）。
