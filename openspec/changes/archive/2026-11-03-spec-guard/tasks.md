## 1. 检查点正文

- [x] 1.1 `rules/workflow-gates.md` 开头改为覆盖每一次改代码，新增「不走 OpenSpec 改代码时」一节（读主规格的方法、四条路、最小 change 形状与停一次、汇报写明依据、改完只跑 ruff 与测试、没有 openspec 的项目）；验证：新测试断言该节含四条路的关键词与「不跑精简与独立审查」
- [x] 1.2 新增「归档」一节（自查、`openspec archive <name> --yes`、`openspec validate --specs --strict`、失败停下、不问是否同步、第 3 个归档时的 key 提示）；验证：新测试断言命令与「正好是 3」的条件都在正文里

## 2. 入口与文档

- [x] 2.1 `workflow-gates.block.md` 与 `workflow-gates-no-openspec.block.md` 写明改代码前读取；验证：更新 `test_update_completes_gates_once_openspec_appears` 的断言，新增无 openspec 入口块含「ruff 与测试」的断言，全量测试通过
- [x] 2.2 本仓库 `AGENTS.md` 的 Workflow gates 一节与 `README.md` 的检查点说明同步新口径；验证：`rulemason check` 在本仓库仍为「日常巡检：一切一致」

## 3. 验证

- [x] 3.1 按 workflow gates 完成精简（只改文档与模板时跳过并写明）、独立审查、ruff、pytest；验证：结果写进 `verification.md`
- [x] 3.2 在项目甲、乙、丙的 worktree 运行本次代码的 `rulemason update` 与 `check`，确认标记块刷新、退出码 0；在一个 worktree 里用 Claude Code 实测一次不走 OpenSpec 的小改动，看是否先读主规格并写明判断依据；验证：结果写进 `verification.md`

## Workflow follow-up

- 发版 0.8.6：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README 的 CI 钉版本，推送、按新「归档」一节归档、打 tag。
- 接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`。
