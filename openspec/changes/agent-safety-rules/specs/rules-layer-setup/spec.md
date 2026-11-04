## ADDED Requirements

### Requirement: 按项目实际情况提出常见红线候选

补项目信息问红线时，skill SHALL 在 README 与 `context` 的候选之外，按项目里实际存在的东西提出常见红线候选：有数据库访问（ORM、迁移目录、数据库连接配置）时提「线上数据库只读，迁移与改数据由人执行」；有部署脚本或 CI 发布流程时提「不代为发布到生产，发布由人触发」；有区分生产环境的配置（如 `.env.production`、`config/production.*`）时提「生产凭据只给人用，AI 会话不使用生产写权限」。出处写「rulemason 常见红线」并附触发它的文件；项目没有对应的东西时 MUST NOT 提出该条。

#### Scenario: 有数据库与部署的后端
- **WHEN** 项目有 `alembic/` 迁移目录和 `.github/workflows/deploy.yml`，README 与 `context` 都没写红线
- **THEN** skill 提出「线上数据库只读」「不代为发布到生产」两条候选，出处分别写「rulemason 常见红线（alembic/）」与「rulemason 常见红线（.github/workflows/deploy.yml）」，逐条请用户确认、改写或删除

#### Scenario: 纯工具库
- **WHEN** 项目是一个没有数据库访问、没有部署流程的命令行工具库
- **THEN** skill 不提出任何常见红线候选，仍按原来的方式问用户一句有没有红线

#### Scenario: 用户删掉候选
- **WHEN** 用户说这个项目没有线上数据库，不需要第一条
- **THEN** 该条不写入，红线一节只写用户确认的条目

## MODIFIED Requirements

### Requirement: 红线由人确认，skill 不代写

skill 提出的红线与判断规则候选 SHALL 注明出处（项目 README、`openspec/config.yaml` 的 `context`、某个已归档方案，或「rulemason 常见红线」及触发它的文件），写入项目通用指令入口或 `judgments.yaml` 前 MUST 逐条请用户确认或改写；用户没有确认的候选 MUST NOT 写入。

#### Scenario: 从 context 提候选
- **WHEN** 项目丙的 `config.yaml` context 写着「无注册/登录/UGC」
- **THEN** skill 把它列为红线候选，等用户确认后才写进项目指令

#### Scenario: 常见红线也要确认
- **WHEN** skill 按项目里的迁移目录提出「线上数据库只读」，用户没有回复
- **THEN** 这一条不写入，红线一节保持原样
