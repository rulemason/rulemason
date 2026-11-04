# shared-code-style Specification

## Purpose
规定代码写法规矩（九条与 Python 落法）和 ruff / ESLint 基础规则在本仓库只有一份，以及接入项目如何引用它们、在哪里补充项目自己的部分，使规矩改一处、所有项目同时生效。

## Requirements

### Requirement: 九条与 Python 落法只住本仓库

不分语言的九条写法原则、Python 落法与 React 落法 SHALL 各在本仓库有且只有一份可编辑正文。接入项目只持有由 `rulemason init` / `rulemason update` 生成的只读副本（`.rulemason/rules/`），MUST NOT 手改或另写一份；项目要调整某条措辞时 SHALL 改本仓库的正文并发布，各项目运行 `rulemason update` 后生效。共享落法 MUST NOT 写具体项目的样板路径、目录、框架或国际化方案，这些由项目在引入处写明。

#### Scenario: 查找写法规矩
- **WHEN** 开发者或 AI 想知道某个接入项目的代码该怎么写
- **THEN** 读到的是项目 `.rulemason/rules/` 中由本仓库生成的副本，项目里没有其他版本的正文

#### Scenario: 修改一条规矩
- **WHEN** 某条规矩的措辞需要调整
- **THEN** 只改本仓库的正文并发布新版本；各项目运行 `rulemason update` 后读到新措辞，项目自己不编辑正文

#### Scenario: 副本被手改
- **WHEN** 有人在项目里直接修改 `.rulemason/rules/code-style.md`
- **THEN** `rulemason check` 报告该副本与记录不符并以非 0 退出

#### Scenario: React 落法不含项目专属内容
- **WHEN** 查看 `rules/react.md`
- **THEN** 其中没有 Next.js、next-intl、某个项目的文件路径或目录名

### Requirement: 项目在 Code style 标题下引用共享规矩

接入项目的通用指令 SHALL 保留 `## Code style` 标题，并在 rulemason 标记块内引用 `.rulemason/rules/` 下的九条与对应语言落法副本。项目 SHALL 在标记块外保留自己的样板路径、语言落法位置与豁免说明。选了 Claude Code 时，`CLAUDE.md` SHALL 导入通用指令与适用的共享正文副本，使会话开始即加载；OpenCode SHALL 通过 `instructions` 加载相同副本；Cursor 与 Codex SHALL 通过 `AGENTS.md` 读取。

#### Scenario: 引入后 AI 读到完整规矩
- **WHEN** Claude Code、OpenCode、Cursor 或 Codex 在已接入项目中开始会话
- **THEN** 所选工具从项目内的通用指令或其原生入口读到 rulemason 的九条原则、语言落法与项目样板路径

#### Scenario: 判断规则仍能找到上层规矩
- **WHEN** 项目判断规则写 `enforces: L0/Code style`
- **THEN** 通用指令中存在 `## Code style`，判断层不报「enforces 指向不存在的上层规则」

#### Scenario: 本仓库与项目不在同一父目录
- **WHEN** 项目被单独 clone 到任意位置，附近没有 rulemason 仓库
- **THEN** 所选工具照常读到九条副本，不需要读取项目外文件

### Requirement: 前端落法在出现第二个同类项目前留在项目

某种前端形态的落法（如 React、单文件原生 JS）在只有一个项目使用时 SHALL 留在该项目的语言目录 `CLAUDE.md`，不进本仓库；同一形态出现第二个接入项目时，SHALL 先把落法收进本仓库再接入第二个项目，不复制。

#### Scenario: 当前状态
- **WHEN** 查看本仓库的语言落法
- **THEN** 有 Python 落法与 React 落法；项目乙 `frontend/CLAUDE.md` 的单文件原生 JS 落法仍留原处

#### Scenario: 第二个 React 项目接入
- **WHEN** 项目乙 `studio/` 作为第二个 React 项目接入
- **THEN** 本仓库先发布 React 落法；迁移时项目甲先升级并把 `web/CLAUDE.md` 精简为只留项目专属内容，项目乙再升级引用，过程中两个项目都不另写一份 React 落法

### Requirement: ruff 基础规则由项目继承

本仓库 SHALL 提供一份 ruff 基础配置：选用规则 ERA001（注释掉的代码）、T201（print）、BLE001（过宽 except）、E722（裸 except）、C901（圈复杂度）、F（pyflakes）、E701 与 E702（一行写多条语句）、RUF021（`a and b or c` 不加括号）、B（bugbear）、I（import 排序），并单独开启预览规则 PLW1514（读写文本不写 encoding），复杂度上限 10。接入项目的 ruff 配置 SHALL 继承它在项目内的副本 `.rulemason/lint/ruff-base.toml`，只写豁免路径与框架声明；每条豁免 MUST 写明原因，MUST NOT 在代码中逐行加 noqa。共享配置 MUST NOT 写任何项目的框架或领域名。

#### Scenario: 项目继承基础规则
- **WHEN** 在已接入项目运行 ruff
- **THEN** 生效的选用规则与复杂度上限来自 `.rulemason/lint/ruff-base.toml`，项目配置里只出现豁免与框架声明

#### Scenario: 基础规则调整
- **WHEN** 本仓库的基础配置新增一条选用规则并发布
- **THEN** 项目运行 `rulemason update` 后，下次运行 ruff 即按新规则检查，项目自己的 ruff 配置不需要改

#### Scenario: 继承前后结果一致
- **WHEN** 项目从自带规则改为继承基础配置
- **THEN** 迁移前后 ruff 对同一份代码的报告完全相同

#### Scenario: 框架惯用写法的误报由项目声明
- **WHEN** 某项目的框架约定在参数默认值里调用函数（如 FastAPI 的 `Depends()`）而触发 B008
- **THEN** 该项目在自己的 ruff 配置里用 `extend-immutable-calls` 声明这些调用，共享配置不关闭 B008

#### Scenario: 只开一条预览规则
- **WHEN** 项目继承基础配置运行 ruff
- **THEN** 未写 encoding 的 `open()` 与 `read_text()` 被报出，其他预览规则不因此生效

### Requirement: ESLint 基础规则由项目继承

本仓库 SHALL 提供一份 ESLint 基础规则：`no-console`、`no-nested-ternary` 与 `no-empty`（空 `catch` 同样报出）为报错级别，函数复杂度目标上限 15；MUST NOT 收入 ESLint 已弃用的格式类规则。接入项目的 ESLint 配置 SHALL 引入这份基础规则，再加本项目的框架规则与豁免。项目当前代码超出复杂度目标时，SHALL 把上限设为当前最复杂函数的值并写明原因与递减计划，上限只降不升。

#### Scenario: 项目甲引入基础规则
- **WHEN** 在项目甲 `web/` 运行 lint
- **THEN** `no-console`、`no-nested-ternary`、`no-empty`、复杂度 15 来自本仓库，中文字面量等 React 专属规则仍在项目配置

#### Scenario: 项目乙使用复杂度棘轮
- **WHEN** 项目乙前端当前最复杂函数为 35
- **THEN** 项目配置把复杂度上限设为 35 并写明「目标 15，只降不升」，其余基础规则照常生效

#### Scenario: 项目放宽空 catch
- **WHEN** 项目乙前端在基础规则之后写 `"no-empty": ["error", { allowEmptyCatch: true }]` 并注明原因
- **THEN** 空 `catch` 不报，其他空块仍报

#### Scenario: 继承前后结果一致
- **WHEN** 两个项目从自带规则改为引入基础规则
- **THEN** 迁移前后 lint 的报告完全相同

### Requirement: 九条之外的通用约定

共享规矩 SHALL 写明以下不分语言的约定：注释与 docstring 用中文，标识符用英文，界面文字与数据值可以是中文；一行只做一件事；MUST NOT 提交密钥、凭证与本机绝对路径。Python 落法 SHALL 写明：服务端与长期运行的程序用 logging 输出，`print` 只用于命令行与脚本，这些目录在 ruff 配置里豁免 T201 并注明原因。

#### Scenario: 项目里写了本机路径
- **WHEN** 新代码里出现 `/Users/<某人>/...` 这样的绝对路径
- **THEN** 独立审查按「九条之外」的约定报 block，改为相对路径或配置项

#### Scenario: 服务端用 print
- **WHEN** 后端服务的请求处理代码里用 `print` 输出日志
- **THEN** ruff 报 T201，按 Python 落法改用 logging

### Requirement: 对外部平台与环境的操作分三级

共享规矩 SHALL 写明：AI 对外部平台与环境（云平台、DNS、数据库、部署与发布、第三方账号）的操作分三级，项目指令另有写明的从项目。读（不含密钥值与个人数据）：直接做，汇报写明读了什么。写（能改回去的改动，以及发布、发送消息、推送 tag 这类收不回但不销毁已有东西的操作）：先说清改什么、改成什么、能否及怎么改回去，等用户就这一次授权，做完汇报。删除或作废（含强推覆盖共享分支，说不清会不会销毁的也算）：AI MUST NOT 执行，只给出操作入口与核对点。有写权限 MUST NOT 被当成可以写。

#### Scenario: 只读查询
- **WHEN** 用户让 AI 查一个域名当前的 DNS 记录
- **THEN** AI 直接查询，汇报写明查了哪个域名的哪些记录，不改任何记录

#### Scenario: 能改回去的写
- **WHEN** 排查中发现需要把某条 DNS 记录改指向新地址
- **THEN** AI 先写明记录名、旧值、新值与改回旧值的方法，等用户回复同意这一次再改；改完在汇报写明

#### Scenario: 授权不延续
- **WHEN** 用户刚同意改一条 DNS 记录，AI 随后发现还要改另一条
- **THEN** AI 对第二条重新说明并等授权，不沿用上一次的同意

#### Scenario: 收不回的发布
- **WHEN** 用户让 AI 把一个新版本发布到公开的包仓库
- **THEN** AI 先说明要发布的版本、发布后不能撤回同一版本号，等用户同意这一次再发布

#### Scenario: 不可逆的删除
- **WHEN** 清理时需要删除一个数据库或作废一把 API key
- **THEN** AI 不执行，给出平台上的操作入口与删除前要核对的项（名称、所属环境、是否仍被引用），由人操作

#### Scenario: 凭据权限大于任务
- **WHEN** AI 手里的凭据对生产数据库有写权限，用户只让它看一下数据
- **THEN** AI 只执行读操作；要写时按「写」先说明并等授权

### Requirement: 密钥不经过会话

共享规矩 SHALL 写明密钥的会话纪律：MUST NOT 让用户把密钥值贴进对话，改为让用户自己写进本机的环境文件（确认不会被提交）或密钥管理工具，AI 只引用变量名；MUST NOT 把密钥值打印到命令输出，需要确认时只检查是否存在；密钥值在对话或日志里出现过，SHALL 按泄露处理，提醒用户作废并重新签发。新建密钥时 SHALL 建议一个用途一把、只给需要的权限、预发与生产分开。

#### Scenario: 用户要贴 token
- **WHEN** 用户说「我把 token 发给你，你帮我配上」
- **THEN** AI 请用户把 token 写进本机的环境文件（或项目约定的密钥位置），自己只在配置里引用变量名，不接收值

#### Scenario: 确认密钥已配置
- **WHEN** AI 需要确认 `DATABASE_URL` 已经设置
- **THEN** AI 只检查变量是否存在、是否为空，不用 `echo`、`cat` 或 `printenv` 打印它的值

#### Scenario: 值已经出现在对话里
- **WHEN** 用户已经把一个 API key 贴进了对话
- **THEN** AI 不使用它，提醒用户这把 key 已按泄露处理、要作废并重新签发，再按上面的方式配置新 key

#### Scenario: 新建密钥
- **WHEN** 项目要接一个新的第三方服务
- **THEN** AI 建议为这一个用途单独建一把 key，只勾需要的权限，预发与生产各用一把

### Requirement: 内部函数不静默改走另一条路径

九条第 8 条 SHALL 写明：内部函数除了不吞异常，也 MUST NOT 在失败时静默改走另一条路径（换一个接口、退回缓存或旧数据）来掩盖失败；需要降级时，由面向用户或命令行的最外层决定，并让调用方或用户知道走了降级。

#### Scenario: 静默切到备用接口
- **WHEN** 新代码在内部函数里捕获主接口的错误，改调备用接口并照常返回
- **THEN** 独立审查按九条第 8 条报出，改为让错误往上抛，或在最外层显式降级并告知

#### Scenario: 最外层显式降级
- **WHEN** 命令行入口在主数据源失败时改用本地缓存，并在输出里写明「使用缓存数据」
- **THEN** 不违反第 8 条
