## Context

`.github/workflows/publish.yml` 只在推 `v*` tag 时运行：`build` job 跑 ruff、pytest、核对 tag 与包版本、`uv build`；`publish` job 在 `pypi` 环境（需 jincheng-xie 批准，管理员可绕过）里经 Trusted Publishing 上传。工作流级权限是 `contents: read`。

仓库已开启 immutable releases：Release 发布后 tag 与附件不能改，标题与说明仍可编辑。`main` 由规则集 `protect-main` 保护，管理员可绕过。

提交信息按 `rules/workflow-gates.md`「提交信息」一节写成「类型(范围): 中文说明（change 名，vX）」，归档提交是 `chore`。

## Goals / Non-Goals

**Goals:**
- PR 上能看到 ruff 与测试的结果，审核者不用自己拉代码跑。
- 推 tag 后不再手动建 Release。

**Non-Goals:**
- 不在 PR 检查里跑多个 Python 版本或多个系统；和发版检查保持一致，只跑一次。

## Decisions

### D1 PR 检查单独放 `ci.yml`，job 名 `test`

触发：`pull_request`（目标 `main`）与 `push`（`main`）；步骤同 `build` 的前两步（`uv run ruff check .`、`uv run pytest`）；`permissions: contents: read`，checkout 不保留凭据；同一分支新提交到来时取消旧的运行。
否决：并进 `publish.yml` 用条件区分触发。两种触发的权限与环境不同，混在一个文件里，一个条件写错就可能让 PR 跑到发布步骤。

### D2 `release` job 放在 `publish` 之后

`needs: publish`，只有这个 job 声明 `contents: write`；checkout 取完整历史（`fetch-depth: 0`）才能找到上一个 tag。先用 `gh release view <tag>` 判断是否已存在，存在就打印一行说明并成功退出；不存在则 `gh release create <tag> --verify-tag --title <tag> --notes-file <文件> --latest`。
否决：在 `build` 之后与 `publish` 并行建 Release。PyPI 上传失败或审批被拒时会留下一个对不上 PyPI 的 Release，而 immutable releases 下 tag 不能再挪。否决：用第三方建 Release 的 action。`gh` 已预装在 runner 上，少一个外部依赖。

### D3 说明由 `scripts/release_notes.py` 生成

输入 tag 名，输出 Markdown 到标准输出：
1. 用 `git tag --list 'v*' --sort=-v:refname` 找到本 tag 之前的上一个 tag；没有时从第一个提交开始。
2. `git log --format=%s <上一个>..<本 tag>` 取标题，按正则 `^(feat|fix|docs)(?:\([^)]*\))?: (.+)$` 归类（类型列表取自分组表，不另写一份），其余丢弃。
3. 去掉说明末尾的全角括号段（`（…）`），保留中间的破折号说明。
4. 按「新功能」「修复」「文档」顺序输出有内容的分组；都没有时写「本版本没有面向用户的改动」；末尾附 `uv tool upgrade rulemason` 与对比链接（第一个 tag 不附）。
否决：GitHub 的 `--generate-notes`。它按合并的 PR 生成，本仓库发版多数直接推 `main`，生成结果几乎只有一行链接。否决：只建草稿等人工补写。和现在的手动流程差别不大，仍会忘。否决：在 workflow 里用 shell 加 `sed` 拼说明。分组与去括号的规则不好测试，出错要到发版时才发现。

### D4 脚本可测试且随 sdist 发布

测试放 `tests/test_release_notes.py`，在临时目录里建一个 git 仓库、造提交与 tag 来调用脚本。sdist 的 `only-include` 收录 `tests`，所以同时补上 `scripts`，否则从 sdist 跑测试会找不到脚本。脚本把结果打印到标准输出，在 ruff 豁免里为它加 T201 并注明原因。
否决：把脚本放进 `src/rulemason/`。它是本仓库的发版工具，不是给接入项目用的功能，不该随 wheel 装到用户机器上。

## Risks / Trade-offs

- [提交标题偏长、偏开发者视角] → 说明可在发布后手动编辑；immutable releases 不锁标题与说明。
- [提交信息没按「类型: 说明」格式写] → 该提交不会出现在说明里；格式由 workflow-gates「提交信息」约定，pre-commit 不拦，审核 PR 时留意。
- [`pypi` 环境审批前，Release 不会出现] → 符合预期：Release 只代表已发布到 PyPI 的版本。
- [以后给旧版本线补发补丁（如 v0.9.0 之后发 v0.8.10）时，`--latest` 会把 Latest 挪到旧版本] → 目前单线发版不会发生；真要维护多条版本线时，改为只在本 tag 是最高版本时加 `--latest`，并同步改规格。
- [短时间连推 `main` 时旧检查被取消] → 只对 PR 取消旧运行，`main` 上每个提交都保留检查结果。
- [管理员绕过规则集直推 `main` 时 `test` 失败] → 检查结果仍显示在提交上，发版时 `build` 会再跑一遍，失败就不发布。

## Migration Plan

1. 在分支上实现，提 PR：PR 本身就会触发新的 `test` 检查，用来验证 `ci.yml`。
2. 本地用 `uv run python scripts/release_notes.py v0.8.9` 核对输出与手写的 v0.8.9 说明一致。
3. 合入后发下一个版本，确认 PyPI 发布成功后自动出现 Release 并为 Latest。
4. 在 `protect-main` 规则集勾选 Require status checks to pass，选 `test`（网页操作，记入完成汇报）。
5. 回滚：删除 `ci.yml`，去掉 `publish.yml` 的 `release` job；已建的 Release 不受影响。

## 文件与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `.github/workflows/ci.yml` | 新增：PR 与 main 推送检查 | +25 |
| `.github/workflows/publish.yml` | 新增 `release` job | +25 |
| `scripts/release_notes.py` | 新增：生成 Release 说明 | +70 |
| `tests/test_release_notes.py` | 新增：分组、去括号、无用户改动、第一个 tag、对比链接 | +80 |
| `pyproject.toml` | ruff T201 豁免、sdist 收录 `scripts` | +2 |
