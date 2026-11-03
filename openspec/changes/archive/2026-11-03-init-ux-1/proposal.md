# Proposal

## Why

公司项目第一次接入 0.8.0 的反馈集中在 `init` 的体验：工具选择靠输编号；文件计划把十几个路径全部打出来；写完又把整份 check 报告倒在屏幕上；`--yes` 会静默代跑 `openspec init` 写入 24 个文件；Go 项目也被塞进 Python、React、文案语气的规则副本；AGENTS.md 接入后是五处「待 /rulemason 补充」；`.gitignore` 挡住 skill 副本时只提示不动手；判断功能和 `rulemason key` 没有任何引导，用户不知道有这回事。这些都在 `init` 一条命令的路径上，一起改。

## What Changes

- 工具选择改为上下键移动、空格勾选、回车确认、`a` 全选；第一次全不勾，检测到工具目录只标注「检测到」；重跑预勾清单记录的工具。非终端或 Windows 退回现在的编号输入。不加依赖，用标准库读单键。
- 交互确认时只显示文件计划摘要（按规则副本 / skill / 配置 / 入口计数，修改的文件逐个列出，需要处理的事项逐条列出），提示 `[y/N/d]`，`d` 展开完整清单后再问一次；`--plan` 与 `--json` 保持完整输出。
- 写入后只给 check 第一行、「需要你处理」清单（ESLint 等附可粘贴的代码）与下一步，不再打印整份报告；标题、路径、待办用启动画面的配色，`NO_COLOR` 全关。
- 没有 `openspec/` 时：交互仍问要不要代跑 `openspec init`；`--yes`、用户拒绝或本机没有 `openspec` 命令时只装「读」层（规则副本、入口块、lint 继承），结尾写明检查点与方案写法需要 OpenSpec、装好后 `rulemason update` 补齐。
- 按识别到的语言复制副本：`code-style`、`workflow-gates` 必复制；`python.md` + `ruff-base` 只在有 Python 时；`react.md` + `eslint-base` 只在有 React 目录时；`copy-voice` 只在有前端目录或判断已启用时。清单记实际集合，`update` 在语言出现后补齐。
- AGENTS.md 预填：简介取 README 第一段正文截两句，没有 README 保留占位；红线写「暂无」；「样板与豁免」与命令表的「自动识别，请确认」保留，`check` 的下一步仍指向 `/rulemason`。
- `.gitignore` 挡住 skill 副本时，放行规则作为「修改」进计划，和其他改动一起确认后写入。
- key 引导：交互且无 `--yes`、本机无 key、判断条件已满足时，结尾问一句是否现在配置，选是直接进入不回显输入；不满足时只提示一行；`check` 的「判断」一行在条件满足而无 key 时提示 `rulemason key`；提示都附申请地址 https://typesafe.ai/ ；不带参数运行的常用命令表加 `rulemason key`。
- 命令表模板「判断层未装」改为「可选，未启用」。
- 不做：改 `update`、`check` 的计划与报告格式（它们面向日常与 AI，保持完整）；改启动画面的图标与字标；ESLint `defineConfig` 写法、引用路径存在性检查、跳过 `openspec/changes/`、前端目录识别、版本落后口径（归 init-ux-2）。
- 不做：Windows 下的方向键选择（退回编号输入即可）；AI 代配 key。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：init 的工具选择、计划摘要与收尾、无 OpenSpec 时的分层接入、按语言复制副本、预填项目信息、`.gitignore` 放行进计划、key 引导；check 的判断一行；不带参数的常用命令表。
- `rules-layer-setup`：skill 第二阶段核对 init 预填的简介、命令表措辞改为「可选，未启用」。

## Impact

- 代码：`init.py`（选择器、摘要、收尾、分层、预填、gitignore、key 引导）、`shared.py`（按语言生成副本、颜色函数）、`check.py`（判断一行、副本集合按清单）、`update.py`（按语言刷新副本）、`banner.py`（颜色函数迁出、常用命令加一行）、`templates/AGENTS.md.tmpl`、`templates/workflow-gates.block.md`。
- 测试：`test_init.py`、`test_update.py`、`test_check.py`、`test_banner.py`、`test_templates.py`、`test_shared.py`。
- 文档：README「第一次接入」；`skills/rulemason/SKILL.md` 第二阶段第 1、4 步。
- 接入项目：下次 `update` 会删掉本项目语言用不到的副本（`update` 现有的「不再生成且未改的旧副本」逻辑），AGENTS.md 入口块里的落法引用随之变化；`check` 输出的「判断」一行措辞变化，CI 只看退出码不受影响。
