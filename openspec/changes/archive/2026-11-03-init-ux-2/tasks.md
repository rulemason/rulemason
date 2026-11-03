## 1. 扫描与前端目录

- [x] 1.1 `shared.scan` 静默跳过 `openspec/changes/`（遍历与 git 两个分支）；验证：新测试中 `openspec/changes/add-x/prototype/package.json` 依赖 react 时，`list_files` 不含它，识别表「跳过」不列它
- [x] 1.2 `check.package_dirs` 取代 `react_dirs` 的读取逻辑，`frontend_dirs(root, files)` 按 `FRONTEND_DEPS` 识别，更新所有调用处；验证：工作区根与 `apps/api` 只有工具依赖、`apps/web` 依赖 vue 时前端目录只列 `apps/web`，现有 React 测试全过

## 2. lint 引用与自动改写

- [x] 2.1 `check.broken_lint_refs`，check 的 lint 层单独报「引用的基础配置不存在」；验证：ESLint 与 ruff 各一个坏引用的测试，退出码非 0
- [x] 2.2 `check.lint_fix` 收拢逐文件判断：三种 ESLint 锚点、坏路径改正、已有正确引用又有坏引用时给手动提示、ruff 的 select / 其他 extend / 坏 extend；`init.plan_lint` 改用它；验证：`defineConfig([`、`tseslint.config(`（含展开参数）、坏路径改正、两条引用并存四个 init 测试，原有 plan_lint 测试全过
- [x] 2.3 update 补齐计划同样改正坏路径；验证：`update --yes` 后坏引用变为正确路径、check 的 lint 层齐全

## 3. 版本落后与下一步

- [x] 3.1 `check.copies_behind` 进「接入 生成副本」层；源码仓库与记录高于本机时不比较；验证：改动一份共享规则内容后 check 报副本落后且非 0，update 后恢复 0
- [x] 3.2 只差版本号时 `version_findings` 改写、第一行附一句、退出码 0；验证：把清单版本改低但内容不变的测试
- [x] 3.3 `next_stage` 增加 `manual_lint`：接入只剩手动 lint 项时给出文件与要加的内容；验证：只有一份 `.eslintrc.json` 未继承时第一行为「接入：手动修改 …」，`check --json` 的 `next.code` 为 `manual_lint`

## 4. ruff.toml 位置与 update 提示

- [x] 4.1 `ruff_home` 与模板 `$extend`；验证：Python 只在 `apps/api/` 时新建 `apps/api/ruff.toml` 且 `extend = "../../.rulemason/lint/ruff-base.toml"`，`ruff check` 在项目根能读到；根目录有 `.py` 时仍写根目录
- [x] 4.2 没有 `openspec/` 时 update 结尾提示，与识别表共用文字常量；验证：update 输出最后一行测试

## 5. 收尾

- [x] 5.1 README 与 `skills/rulemason/SKILL.md` 中涉及「运行 rulemason update」下一步、前端目录、版本落后的说法与新口径一致；验证：`grep` 不再出现旧说法
- [x] 5.2 按 workflow gates 完成精简、独立审查、ruff、pytest；在项目甲、乙、丙的 worktree 跑 `check` 与 `update --dry-run` 并记录；写 `verification.md`

## Workflow follow-up

- 发版 0.8.5：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README 的 CI 钉版本，推送、归档、打 tag。
- 接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`。
