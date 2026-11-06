## MODIFIED Requirements

### Requirement: 归档后提示一次启用判断

归档完成后，`rulemason check --json` 的「判断」一行显示条件已满足且未启用，并且「已归档 change」正好是 3 或「接入后归档 change」正好是 1 时，AI SHALL 在汇报末尾提示一次：本机没有 key 时提示运行 `rulemason key`（申请地址 https://typesafe.ai/ ）；已有 key 时提示在 AI 工具中运行 `/rulemason` 并说明要启用判断。两种提示都 SHALL 附一句：判断审 OpenSpec 方案、界面文案与直接改动的说明。AI MUST NOT 代为配置 key 或启用判断；其余情况 MUST NOT 提示。

#### Scenario: 第 3 个归档且没有 key
- **WHEN** 项目归档第 3 个 change，没有 `openspec/judgments.yaml`，本机未配置 key
- **THEN** 汇报末尾有一句配置 key 的提示与申请地址，附判断覆盖范围

#### Scenario: 接入后第一次归档且已有 key
- **WHEN** 接入时已归档 60 个 change，接入后归档第 1 个，没有 `openspec/judgments.yaml`，本机已有 key
- **THEN** 汇报末尾提示在 AI 工具中运行 `/rulemason` 并说明要启用判断，附判断覆盖范围

#### Scenario: 之后的归档
- **WHEN** 同一项目接入后归档第 2 个 change，仍未启用判断
- **THEN** 汇报不再提示

#### Scenario: 判断已启用
- **WHEN** 项目有 `openspec/judgments.yaml`，接入后归档第 1 个 change
- **THEN** 汇报不提示

## ADDED Requirements

### Requirement: 敏感区域的直接改动先走 OpenSpec

项目指令写有「先走 OpenSpec 的区域」（列出路径或主题）时，不走 OpenSpec 的代码改动落在其中任一区域，AI SHALL 按「改契约」起最小 change（proposal、规格增量或写明不改规格、一两条 tasks），按「方案刚写完时」跑判断后停下等用户确认，即使主规格没写到这次要改的行为。项目没写这一项时 SHALL 跳过这一步。这一步 MUST NOT 依赖判断层。

#### Scenario: 改到迁移目录
- **WHEN** 项目写明「先走 OpenSpec 的区域：数据库迁移（`migrations/`）、部署脚本」，用户让 AI 直接加一个迁移
- **THEN** AI 不直接改，起最小 change，跑判断后说明要做什么，等用户确认

#### Scenario: 没写敏感区域
- **WHEN** 项目指令没有「先走 OpenSpec 的区域」
- **THEN** 判路照旧，不因这一步起 change

### Requirement: 直接改动说明交判断

判断已启用（命令表「判断」一行不是「可选，未启用」）且本次直接改动改了代码逻辑时，AI SHALL 在动手前把判路依据写成直接改动说明：要做什么、改哪些文件、读了哪些主规格与检索命中、判在哪条路及理由，MUST NOT 贴代码；说明存在仓库外的临时文件，运行 `rulemason judge --direct <文件>`。block SHALL 按「冲突」停下问用户；review SHALL 在汇报里列出后继续。只改文档、配置或样式时 SHALL 跳过；判断未启用时 SHALL 跳过并照旧只跑 ruff 与测试。

#### Scenario: 判断给出 review
- **WHEN** 判断已启用，用户让 AI 改一个后端函数，说明交判断后 `direct-route-respects-specs` 给出 review
- **THEN** AI 在汇报里列出这条 review 与原因，然后继续改，改完跑 ruff 与测试

#### Scenario: 红线规则给出 block
- **WHEN** 项目有一条 `target: direct` 的红线规则「这次改动：新增商务咨询表单以外的数据提交入口」，说明里写着要加一个订阅表单，判断给出 block
- **THEN** AI 不改代码，按「冲突」指出碰到的红线，问用户换做法、改规矩还是放弃

#### Scenario: 只改样式
- **WHEN** 判断已启用，这次直接改动只调了按钮间距
- **THEN** 不写说明、不调用判断
