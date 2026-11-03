## 1. Release 说明脚本

- [x] 1.1 新增 `scripts/release_notes.py`：找上一个 `v*` tag、取提交标题、只收 feat / fix / docs 并分组、去掉类型前缀与末尾全角括号、附升级命令与对比链接；验证：`uv run python scripts/release_notes.py v0.8.9` 输出「修复」分组下只有「README 简介跳过语言切换与导航链接行」，末尾有 `v0.8.8...v0.8.9` 链接
- [x] 1.2 新增 `tests/test_release_notes.py`，在临时 git 仓库里造提交与 tag，覆盖规格三个场景（修复加归档、只有 chore / refactor、第一个 tag）以及多分组顺序；验证：`uv run pytest tests/test_release_notes.py` 全部通过
- [x] 1.3 `pyproject.toml`：为脚本加 T201 豁免并注明原因，sdist `only-include` 收录 `scripts`；验证：`uv run ruff check .` 通过，`uv build` 后 sdist 里有 `scripts/release_notes.py`

## 2. PR 检查

- [x] 2.1 新增 `.github/workflows/ci.yml`：`pull_request`（main）与 `push`（main）触发，job 名 `test`，跑 ruff 与 pytest，只读权限、不保留凭据、新提交取消旧运行；验证：YAML 可解析且 job 名为 `test`，推分支开 PR 后 PR 页面出现 `test` 检查并通过

## 3. 发布后自动建 Release

- [x] 3.1 `publish.yml` 新增 `release` job：`needs: publish`，只有它拿 `contents: write`，完整历史 checkout，已有 Release 时跳过，否则用脚本生成说明并 `gh release create --verify-tag --latest`；验证：YAML 可解析、`release` 依赖 `publish`、工作流级权限仍为 `contents: read`；下个版本发布后 Release 自动出现并为 Latest（写进完成汇报的「待发版确认」）

## 4. 验证

- [x] 4.1 按 workflow gates 完成精简、独立审查、ruff、pytest；验证：结果写进 `verification.md`

## Workflow follow-up

- 发版：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README 的 CI 钉版本，推送，按「归档」一节归档，打 tag；确认 PyPI 发布后自动出现 Release。
- 在 `protect-main` 规则集勾选 Require status checks to pass，选 `test`。
