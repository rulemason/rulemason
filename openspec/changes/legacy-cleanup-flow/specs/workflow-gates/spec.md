## MODIFIED Requirements

### Requirement: Apply 后行为保持的自动精简

实现者 SHALL 在独立只读审查前，对本次 diff 中的代码执行自动精简，重点消除重复、死代码、冗余抽象和过复杂逻辑；本次新增的函数 SHALL 先按名字在仓库里检索，已有同名或同用途的实现时改为复用。精简 MUST 保持需求、外部行为和 API 不变，MUST NOT 为减少行数而重写无关代码。已选工具 MAY 通过自己的入口（如 Claude Code 的 `CLAUDE.md` 标记块）把这一步映射到该工具的精简命令；映射只决定由谁执行，范围与约束仍以共享正文为准，共享正文 MUST NOT 写入某一工具的专属命令。

#### Scenario: 本次改动中有可安全消除的重复
- **WHEN** diff 中有重复逻辑，且合并不会改变需求、外部行为或 API
- **THEN** AI 自动精简该逻辑，再交独立只读审查并运行测试

#### Scenario: 精简可能改变行为或范围
- **WHEN** 某项精简会改变外部行为、API、规格或超出本次 diff
- **THEN** AI 不自动实施该精简，并在审查结果中说明原因

#### Scenario: Claude Code 用 /simplify 执行精简
- **WHEN** 选了 Claude Code 的项目在 apply 结束前，diff 改了代码逻辑
- **THEN** 用 `/simplify` 执行精简，只采纳行为保持的修改，之后照常做独立只读审查与测试

#### Scenario: 只改了文档或配置
- **WHEN** 本次 diff 只涉及文档、配置或生成副本
- **THEN** 不调用 `/simplify`，汇报中写明无代码改动、跳过精简

#### Scenario: 新函数在别处已有
- **WHEN** 本次 diff 新增了 `formatExpiresAt`，仓库另一个文件里已有同名、同用途的函数
- **THEN** 精简时改为调用已有的那个，删掉新加的这份
