## MODIFIED Requirements

### Requirement: 模块完成只认清理提交

一个模块 SHALL 只在 git 历史里存在提交说明以 `refactor(cleanup): <该模块>` 开头的提交时算完成。清理改动还在工作区时 MUST 仍算未完成。一个模块分几次提交时，只有最后一次 SHALL 用这个开头；之前的阶段提交 SHALL 写成 `refactor(cleanup-step): <该模块> 第 N 步`，诊断 MUST NOT 把阶段提交算作完成；收尾时计划里还有步骤没做完，MUST NOT 把该模块视为已完成，最后一行 SHALL 是继续该模块的清理命令；步骤全部做完时才 SHALL 请用户提交 `refactor(cleanup): <该模块>`。skill MUST NOT 自己提交。

#### Scenario: 改完但还没提交
- **WHEN** 某模块的清理改动还在工作区，历史里没有指向它的 `refactor(cleanup):` 提交
- **THEN** 下次不带模块名的诊断仍把它排进队列，不把它算完成

#### Scenario: 提交之后跳过
- **WHEN** 用户提交了 `refactor(cleanup): api/app/ai`
- **THEN** 之后的队列跳过 `api/app/ai`

#### Scenario: 分阶段提交
- **WHEN** 一个模块的清理分三步做，前两步各自提交为 `refactor(cleanup-step): web/features/generate 第 1 步`、`第 2 步`，第三步还没做
- **THEN** 不带模块名的诊断仍把 `web/features/generate` 排进队列；第三步做完、用户提交 `refactor(cleanup): web/features/generate` 之后才跳过它

#### Scenario: 计划还有步骤没做完
- **WHEN** 一个模块的计划分三步，这一轮做完了第 1 步
- **THEN** 收尾请用户提交 `refactor(cleanup-step): <该模块> 第 1 步`，不把该模块视为已完成，最后一行是 `/rulemason cleanup <该模块>`，不给出下一个模块

#### Scenario: 最后一步做完
- **WHEN** 同一个模块已有第 1、2 步的阶段提交，这一轮做完了第 3 步，计划的步骤全部完成
- **THEN** 收尾请用户提交 `refactor(cleanup): <该模块>`，把该模块视为已完成，最后一行给出下一个模块

## ADDED Requirements

### Requirement: 存量清理正文单独成文件

存量清理的做法（入口闸门之后的诊断、修一个模块的各步、完成标记与收尾）SHALL 写在 skill 目录下的 `cleanup.md`，`SKILL.md` 只保留入口：用户要做存量清理时读 `cleanup.md` 并照做。补项目信息、日常巡检、启用判断等其他用途 MUST NOT 要求读 `cleanup.md`。

#### Scenario: 日常巡检
- **WHEN** 用户在已接入项目运行 `/rulemason` 做日常巡检
- **THEN** 按 `SKILL.md` 做完巡检，不读 `cleanup.md`

#### Scenario: 要做存量清理
- **WHEN** 用户输入 `/rulemason cleanup`
- **THEN** 按 `SKILL.md` 第 1 节过完入口闸门后，读同目录的 `cleanup.md` 并按它诊断
