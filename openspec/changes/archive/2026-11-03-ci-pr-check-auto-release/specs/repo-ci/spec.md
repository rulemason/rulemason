# Spec Delta

## Purpose

rulemason 仓库自身的持续集成与发版：PR 合入前自动跑检查，推 `v*` tag 发布 PyPI 成功后自动创建 GitHub Release，并约定 Release 说明的生成规则。

## ADDED Requirements

### Requirement: PR 与 main 推送自动检查

对 `main` 发起或更新的 PR，以及推送到 `main` 的提交，SHALL 自动运行 ruff 与测试。检查在 GitHub 上的名称 MUST 固定为 `test`，供分支保护规则引用；ruff 或任一测试失败时，该检查 SHALL 显示为失败。

#### Scenario: PR 含 ruff 问题
- **WHEN** 协作者提交一个含 ruff 报错的 PR 到 `main`
- **THEN** PR 页面上名为 `test` 的检查显示失败，并能看到 ruff 的报错输出

#### Scenario: PR 全部通过
- **WHEN** PR 的 ruff 与测试都通过
- **THEN** 名为 `test` 的检查显示通过

#### Scenario: 直接推送 main
- **WHEN** 管理员绕过规则集直接推送提交到 `main`
- **THEN** 同样运行 `test` 检查，结果显示在该提交上

### Requirement: PyPI 发布成功后自动创建 Release

推送 `v*` tag 且该版本发布到 PyPI 成功后，SHALL 为该 tag 创建已发布（非草稿）的 GitHub Release，标题为 tag 名，并设为 Latest。PyPI 发布失败、被取消或尚未获批准时 MUST NOT 创建 Release。该 tag 已有 Release 时 SHALL 跳过创建并视为成功，MUST NOT 修改已有 Release。

#### Scenario: 发布成功
- **WHEN** 推送 tag `v0.9.0`，检查通过、`pypi` 环境获批、上传 PyPI 成功
- **THEN** 仓库出现标题为 `v0.9.0` 的 Release，并标记为 Latest

#### Scenario: PyPI 发布失败
- **WHEN** 推送 tag 后测试失败，或 tag 与包版本不一致，或 PyPI 上传失败
- **THEN** 不创建该 tag 的 Release

#### Scenario: 已手动建过 Release
- **WHEN** 推送 tag 前或发布过程中，该 tag 已有手动创建的 Release
- **THEN** 创建步骤跳过且不报错，已有 Release 的标题与说明保持不变

### Requirement: Release 说明由提交标题生成

Release 说明 SHALL 取上一个 `v*` tag 到本 tag 之间的提交标题，只收 `feat`、`fix`、`docs` 三类，按「新功能」「修复」「文档」分组列出，MUST NOT 收其他类型（如 `chore`、`refactor`、`test`）。每条 SHALL 去掉类型与范围前缀、末尾全角括号里的 change 名与版本号，以及 squash 合入时追加的 `(#PR 号)`。说明末尾 SHALL 附升级命令与上一个 tag 到本 tag 的对比链接。

#### Scenario: 一版里有修复与归档提交
- **WHEN** 上一个 tag 到本 tag 之间有 `fix(init): README 简介跳过语言切换与导航链接行（readme-intro-lang-line，v0.8.9）` 与一条 `chore: 归档 …` 提交
- **THEN** 说明的「修复」分组下有一条「README 简介跳过语言切换与导航链接行」，没有「新功能」「文档」分组，不出现归档提交，末尾有升级命令与 `v0.8.8...v0.8.9` 对比链接

#### Scenario: 没有面向用户的提交
- **WHEN** 两个 tag 之间只有 `chore` 或 `refactor` 提交
- **THEN** 说明写明「本版本没有面向用户的改动」，仍附升级命令与对比链接

#### Scenario: 第一个 tag
- **WHEN** 本 tag 之前没有任何 `v*` tag
- **THEN** 从仓库第一个提交开始取提交标题，末尾不附对比链接
