## Why

rulemason 已有长期协作者，`main` 也开了「合入必须走 PR 并经 1 人批准」的保护，但 PR 上不跑任何检查：ruff 与测试只在推 `v*` tag 发版时运行，审核者得自己拉代码验证，问题要到发版时才暴露。

另外，推 tag 只会发布到 PyPI，GitHub Release 每次都要手动补写（v0.8.9 已发 PyPI，仓库首页的 Latest 仍停在 v0.8.8），容易漏，且与 PyPI 版本脱节。

## What Changes

- 新增 PR 检查：对 `main` 的 PR 与推送到 `main` 时运行 ruff 与测试，检查名固定为 `test`，供分支保护日后设为必须通过。
- 发版流程在 PyPI 发布成功后，自动为该 tag 创建 GitHub Release 并设为 Latest；PyPI 发布失败或未获批准时不创建；该 tag 已有 Release 时跳过。
- Release 说明由上一个 tag 到本 tag 之间的提交标题生成：只取 `feat` / `fix` / `docs`，按类型分组，去掉类型前缀与末尾括号里的 change 名和版本，末尾附升级命令与对比链接。
- 不做：在 `protect-main` 规则集里把 `test` 设为必须通过（合入后在网页上勾选，不属于仓库文件）。
- 不做：修改 PyPI 发布本身（检查、版本核对、构建、Trusted Publishing、`pypi` 环境审批保持原样）。
- 不做：维护 CHANGELOG 文件，也不回补 v0.8.9 及更早版本的 Release。

## Capabilities

### New Capabilities

- `repo-ci`：rulemason 仓库自身的持续集成与发版——PR 检查、发布后自动建 Release、Release 说明的生成规则。

### Modified Capabilities

（无）

## Impact

- 新增 `.github/workflows/ci.yml`；修改 `.github/workflows/publish.yml`（新增 `release` job，只有它拿 `contents: write`）。
- 新增生成 Release 说明的脚本与对应测试；`pyproject.toml` 补 ruff 豁免与 sdist 收录。
- 只影响本仓库的 GitHub 设置与发版体验；不改变发布到 PyPI 的包内容，接入项目不受影响。
