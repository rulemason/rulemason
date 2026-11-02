# judge-engine Specification

## Purpose
规定 Jev 判断引擎（命令 `rulemason judge`，库 `rulemason.judge`）只在本仓库一份：项目在自己根目录用同一个命令审方案与文案，需要时从代码里 import 同一个库；项目差异写在项目配置里，通用判断规则与通用短标签词表随引擎提供。

## Requirements

### Requirement: 引擎只住本仓库

判断引擎 SHALL 在本仓库只有一份代码，作为 `rulemason` 包的子包 `rulemason.judge` 提供命令行与库两种用法，随 `rulemason` 包发布。接入项目 MUST NOT 保留引擎副本；项目代码需要 import 引擎库时，SHALL 以发布版本依赖 `rulemason` 包，MUST NOT 依赖同级目录的 rulemason 源码路径。项目修引擎问题时 SHALL 改本仓库并发布新版本，各接入项目升级依赖版本后生效。

#### Scenario: 修一个引擎问题
- **WHEN** 引擎的某个判定逻辑需要修改
- **THEN** 只改本仓库并发布新版本；接入项目把依赖的 `rulemason` 版本升上去后用上新逻辑，项目内不出现引擎代码改动

#### Scenario: 项目里不再有副本
- **WHEN** 在接入项目里查找 `judge.py`
- **THEN** 只剩与判断层无关的文件（如项目乙的 `app/eval/judge.py`），没有判断引擎副本

#### Scenario: 附近没有 rulekit 仓库
- **WHEN** 接入项目被单独克隆到一台没有 rulemason 仓库的机器（或 CI），按项目说明安装开发依赖
- **THEN** 依赖安装成功，项目中 import 引擎库的测试可以运行，不需要建立任何指向项目外的路径或链接

### Requirement: 命令在项目根目录运行

命令 `rulemason judge` SHALL 在任一接入项目内运行，按与 `rulemason init`、`update`、`check` 相同的规则确定项目根：从当前目录往上找最近的 `.rulemason.yaml`，不越过所在 git 仓库的根目录；找不到时以 git 仓库根为项目根。引擎读取该项目根下的 `openspec/`。参数与原 `jev-judge` 一致：`--change <name>` 依次在 `openspec/changes/<name>`、`openspec/changes/archive/<name>`、`openspec/changes/archive/` 下唯一名为 `YYYY-MM-DD-<name>` 的目录中查找产物（只认日期前缀加完整名称；匹配到多个时列出并以非 0 退出），`--copy` 审相对主分支新增或修改的界面文案，`--lint-only` 只跑正则检查不联网，`--dry-run` 打印将要发送的请求而不发送。参数 SHALL 只在引擎里定义一处，`rulemason` 命令原样转交。

#### Scenario: 在子目录运行
- **WHEN** 在项目甲的 `api/` 目录下运行 `rulemason judge --change adopt-shared-rules`
- **THEN** 引擎以项目甲仓库根为项目根，审 `openspec/changes/adopt-shared-rules` 下的产物

#### Scenario: 仓库里的子项目
- **WHEN** 一个仓库的 `packages/web/` 自己有 `.rulemason.yaml` 与 `openspec/`，在 `packages/web/src/` 下运行 `rulemason judge --change x --lint-only`
- **THEN** 引擎以 `packages/web/` 为项目根，审它自己的 `openspec/changes/x`

#### Scenario: 不在 git 仓库里
- **WHEN** 在一个不属于任何 git 仓库的目录运行
- **THEN** 以非 0 退出码报错，说明需在接入项目内运行 `rulemason judge`

#### Scenario: 审已归档的 change
- **WHEN** 在项目内运行 `rulemason judge --change adopt-rulekit-cli --lint-only`，该 change 已归档为 `archive/2026-11-01-adopt-rulekit-cli`
- **THEN** 引擎审查该归档目录下的产物，不报 change 不存在

#### Scenario: 帮助里的命令名
- **WHEN** 运行 `rulemason judge --help`
- **THEN** 用法行写 `rulemason judge`，列出 `--change`、`--copy`、`--lint-only`、`--dry-run`

### Requirement: 库接口名称保持不变

引擎 SHALL 以库 `rulemason.judge` 提供 `load_rules`、`Rule`、`Judge`、`verdict_or_pending`、`lint_design`、`lint_copy`、`label_len`、`enforces_exists`、`change_files`、`lexicon`、`pick_provider`，模块 `rulemason.judge.judge` 保留原 `jev_judge.judge` 的全部公开名称。名称与含义不变，项目代码只需把 import 中的 `jev_judge` 换成 `rulemason.judge`。

#### Scenario: 项目甲对话评估集
- **WHEN** `tests/eval/test_chat_eval.py` 把 `from jev_judge import judge` 改为 `from rulemason.judge import judge`
- **THEN** 不改其他代码即可运行，结果与改名前一致

### Requirement: 项目差异写在项目配置

文案文件的位置、格式（嵌套 JSON，或 HTML 内的 JS 对象）、取哪种语言，以及项目自己的文案禁词，SHALL 写在项目的 `openspec/judge.yaml`，引擎不写死任何项目的路径或词语。项目没有配置文案时，`--copy` MUST 以非 0 退出码报错并说明缺少哪项配置。

#### Scenario: 项目甲审文案
- **WHEN** 项目甲配置文案为 `web/messages/zh.json`、格式为嵌套 JSON
- **THEN** `rulemason judge --copy` 审该文件相对主分支新增或修改的条目

#### Scenario: 项目乙审文案
- **WHEN** 项目乙配置文案为 `frontend/index.html`、格式为 HTML 内 JS 对象、语言 `zh-Hans`，禁词含「保证有效」等
- **THEN** `rulemason judge --copy` 只审简体那一套，含禁词的条目在 lint 阶段 block

### Requirement: 通用判断规则随引擎提供

「写明不做什么」「不做过度设计」两条通用判断规则 SHALL 随引擎提供，所有接入项目自动启用；「决策附备选」由产物格式 lint 检查，MUST NOT 再作为判断规则送模型。`design-no-speculative-extension` 的 block 阈值 SHALL 为 0.3。项目 `openspec/judgments.yaml` 只写本项目的规则；与通用规则同 id 时 SHALL 以项目规则为准。通用规则的 `enforces` MUST 按项目的 `AGENTS.md` 与 `openspec/config.yaml` 检查；没有 `AGENTS.md` 的旧项目 SHALL 回退到 `CLAUDE.md`。

#### Scenario: 迁移后项目规则文件变短
- **WHEN** 项目甲与项目乙的 `judgments.yaml` 不写任何通用规则
- **THEN** 运行判断时「写明不做什么」「不做过度设计」两条照常出现，「决策附备选」由 `lint/design` 检查

#### Scenario: 运行判断时的通用规则
- **WHEN** 在没有自己判断规则的项目运行 `rulemason judge --change x`
- **THEN** 只有 `proposal-states-non-goals` 与 `design-no-speculative-extension` 两条通用规则参与评估

#### Scenario: 项目收紧一条通用规则
- **WHEN** 项目在自己的 `judgments.yaml` 写了同 id 的 `proposal-states-non-goals` 并调高 block 阈值
- **THEN** 该项目使用自己的版本，其他项目仍用通用版本

#### Scenario: 过度设计被拦下
- **WHEN** design 为本次不使用的需求构建插件机制，`design-no-speculative-extension` 得分低于 0.3
- **THEN** 判断结果为 block

### Requirement: L0 enforces 使用工具中立的项目指令

引擎 SHALL 先在项目权威 `AGENTS.md` 中查找 `L0/<标题>`；仅当 `AGENTS.md` 不存在时，迁移期 MUST 回退检查 `CLAUDE.md`。判断结果 MUST NOT 因已选 agent 工具不同而改变。

#### Scenario: 已选工具共用 L0 上层规则
- **WHEN** OpenCode、Claude Code、Cursor 或 Codex 项目的判断规则写 `enforces: L0/Code style`
- **THEN** 引擎在项目 `AGENTS.md` 找到 `## Code style`，不因工具入口不同而误报缺少上层规则

### Requirement: 通用短标签词表随引擎提供

引擎 SHALL 带一份通用短标签词表，只收不属于任何领域的控件与状态标签（如「重试」「收起」「关闭」「加载中…」）。审短标签时通用词表与项目词表任一包含即 pass。领域词 MUST NOT 进通用词表。

#### Scenario: 通用标签不必进项目词表
- **WHEN** 新项目界面新增「重试」，项目词表为空
- **THEN** 查通用词表命中，pass

### Requirement: key 只放一处

Jev 的 key SHALL 从环境变量 `TYPESAFE_API_KEY` 读取；未设置时读 `~/.config/rulemason/env`；该文件不存在时读旧位置 `~/.config/jev-judge/env`。引擎 MUST NOT 读取项目目录里的 `.env`，MUST NOT 创建、复制或搬运 key 文件（配置 key 由 `rulemason key` 在用户输入后写入）。报错与提示中 SHALL 只写新位置。裁判选择规则不变：未指定时有 key 用 Jev、无 key 用人工模式；指定 Jev 却没有 key 时以非 0 退出码报错，不悄悄退化；key 被 Jev 拒绝（已作废或填错）时 SHALL 以非 0 退出并用一句话指出检查 key 的位置，MUST NOT 打印堆栈。人工模式 MUST NOT 显示模型版本，SHALL 提示可以运行 `rulemason key` 配置 key 以自动判断。

#### Scenario: 新项目接入不用再放 key
- **WHEN** 一个新项目接入，项目里没有任何 key
- **THEN** 引擎读到 `~/.config/rulemason/env` 中的 key，使用 Jev

#### Scenario: 只有旧位置的 key
- **WHEN** 机器上只有 `~/.config/jev-judge/env`，没有新位置的文件
- **THEN** 引擎读到旧位置的 key，使用 Jev；不创建新位置的文件

#### Scenario: 没有 key 时预览请求
- **WHEN** 没有 key，运行 `rulemason judge --change x --dry-run`
- **THEN** 打印将要发给 Jev 的请求内容，不报错、不发送

#### Scenario: key 已作废
- **WHEN** key 已被作废，运行 `rulemason judge --change x`
- **THEN** 输出一行说明 key 被拒绝，提示检查 `~/.config/rulemason/env` 或环境变量 `TYPESAFE_API_KEY`，退出码非 0，没有 Python 堆栈

#### Scenario: 没有 key 时走人工模式
- **WHEN** 没有 key，运行 `rulemason judge --change x`
- **THEN** 第一行写「裁判：人工（没有 key；运行 rulemason key 配置后自动用 Jev 判断）」，不出现模型版本

### Requirement: 判定口径与迁移前一致

引擎合并与改名 SHALL 不改变判定口径：pass / review / block 的阈值算法、置信度规则、`JEV_MODEL` 固定版本、有 block 时退出码非 0，均与改名前一致。同一批回归用例在改名前后的结果 MUST 相同。

#### Scenario: 迁移前后回归对比
- **WHEN** 接入项目从 `jev-judge` 改用 `rulemason judge` 后重跑 Jev 回归
- **THEN** 通过与失败的用例集合与改名前完全相同

### Requirement: 判断层模板随引擎提供

判断层的三份模板（项目判断规则 `judgments`、项目判断配置 `judge`、回归用例骨架 `judge_cases`）SHALL 随安装包提供，MUST NOT 复制进项目。`rulemason judge --template <judgments|judge|judge_cases>` SHALL 把对应模板原样打印到标准输出并以 0 退出；名称不认识时 SHALL 列出可选名称并以非 0 退出。该参数不要求在 git 仓库或接入项目里运行。

#### Scenario: 启用判断时取模板
- **WHEN** 在任意目录运行 `rulemason judge --template judgments`
- **THEN** 输出判断规则模板全文，退出码为 0

#### Scenario: 名称写错
- **WHEN** 运行 `rulemason judge --template rules`
- **THEN** 列出 `judgments`、`judge`、`judge_cases`，退出码非 0

### Requirement: 判断引擎读配置出错时给可读提示

`rulemason judge` 读取 `openspec/config.yaml`、`openspec/judge.yaml`、`openspec/judgments.yaml` 或 `openspec/copy-lexicon.yaml` 时，文件不是合法 YAML、顶层类型不对，或判断规则有一条不是带 `id` 的映射，SHALL 输出以「✗」开头、含文件路径与原因（解析失败时含行号，条目问题含第几条）的一行提示，以非 0 退出，MUST NOT 打印 Python traceback。

#### Scenario: judgments.yaml 语法错误
- **WHEN** 项目 `openspec/judgments.yaml` 第 3 行缩进错误，运行 `rulemason judge --change x`
- **THEN** 输出「✗ openspec/judgments.yaml 不是合法的 YAML（第 3 行：…）」，退出码非 0，没有 traceback

#### Scenario: 判断规则缺 id
- **WHEN** `openspec/judgments.yaml` 第 2 条没有 `id`
- **THEN** 输出「✗ openspec/judgments.yaml 第 2 条不是带 id 的映射」，退出码非 0
