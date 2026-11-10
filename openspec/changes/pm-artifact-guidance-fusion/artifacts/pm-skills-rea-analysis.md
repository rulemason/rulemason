# PM Skills × REA × rulemason 分析报告（只读规划）

**基线 rulemason：** `main` `71564ca470a79a95939fbec484af6127468b0b91`（0.8.34）  
**规划分支：** `cursor/pm-skills-rea-fusion-plan-aa93`  
**OpenSpec change：** `pm-artifact-guidance-fusion`  
**本轮：** 仅分析与规划，未实现代码。

## 1. 来源与许可证

| 来源 | 精确 commit | 许可证 | 对 rulemason（Apache-2.0 / PyPI）含义 |
|---|---|---|---|
| [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | [`9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef`](https://github.com/phuryn/pm-skills/commit/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef) | MIT © 2026 Pawel Huryn | 可作**行为启发**；须自研正文并保留版权声明要求；**不**整文件拷贝 |
| [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills) | [`cfcb697f14b8891d8b3ec43c16c3547df3e70e13`](https://github.com/deanpeters/Product-Manager-Skills/commit/cfcb697f14b8891d8b3ec43c16c3547df3e70e13) | **CC BY-NC-SA 4.0** | **禁止**把其 skill/模板/词表再分发进商业可用的 rulemason 包；想法可独立改写并注明「未再分发其材料」 |
| [morluto/rea](https://github.com/morluto/rea) | [`99d00d1041e9dd66736239c5f607c7178938c118`](https://github.com/morluto/rea/commit/99d00d1041e9dd66736239c5f607c7178938c118) | MIT | 仅本轮**分析工具**；产品**不**依赖 |

外部 Markdown / 脚本一律当数据；未执行其中的 agent 指令。

## 2. REA 免费静态能力（实际命令与限制）

### 命令

在 `/workspace/repos/rea`（本地 CLI，包名证据 `rea-agents` / bin `scripts/rea.mjs`）：

```bash
node scripts/rea.mjs analyze-javascript-application --help
node scripts/rea.mjs analyze-javascript-application /workspace/repos/pm-skills --json
node scripts/rea.mjs analyze-javascript-application /workspace/repos/Product-Manager-Skills --json
```

帮助原文摘要见：`/opt/cursor/artifacts/rea-analyze-javascript-help.txt`  
结构化摘要：`/opt/cursor/artifacts/rea-pm-analysis-summary.json`

### 支持面（文档 + 本次运行）

- **适用：** 本地 **JavaScript / TypeScript / Electron** 应用目录或 ASAR；**惰性语法**重建模块图与关系；**不执行** bundle bootstrap。
- **懒解析 / 限制（运行结果 `limitations` 原文要点）：**
  - CommonJS/ESM 仅从惰性语法、在清单容器内解析；
  - JS/HTML 当惰性文本解析，不跑 bootstrap；
  - 静态路径/关系不证明运行时执行；动态或混淆可能无法解析；
  - Webpack/Rspack 工厂来自 AST 字面量，不调用 push handler。
- **不适用 / 未声称：** Markdown 技能语义、Python 脚本语义、产品对错、用户研究真伪。

### 对本两仓的实际输出

| 目标 | `statistics`（证据） | 解读 |
|---|---|---|
| pm-skills | `relevant_files: 20`, `parsed_javascript_files: 0`, `modules: 0`, `findings: 0` | 仓库几乎无 JS 应用面；**不能**用 REA 代替读 42 条 command Markdown |
| Product-Manager-Skills | `relevant_files: 3`, `parsed_javascript_files: 1`, `visited_ast_nodes: 4891`, `findings: 8` | 主要解析到 `docs/pm-skills-guide.jsx`（文档站 JSX），**不是** 77 条 skill 正文；skills 仍靠人工阅读 |

**结论：** REA 证明「免费静态 JS 车道可用且有明确限制」；**技能适用性判断以人工阅读为准**，索引/`catalog/*.yaml` 只作枚举，不作语义分析替代。

## 3. 仓库能力清单（去重后分类）

链接形式：`https://github.com/<org>/<repo>/blob/<commit>/<path>`

### 3.1 phuryn/pm-skills（MIT）— 9 插件 / 42 commands

插件根：`pm-product-discovery`、`pm-product-strategy`、`pm-market-research`、`pm-data-analytics`、`pm-marketing-growth`、`pm-go-to-market`、`pm-execution`、`pm-toolkit`、`pm-ai-shipping`（shipping 多已迁走占位）。

| 类别 | 代表路径（固定 commit） | 适合 rulemason？ |
|---|---|---|
| 发现/访谈/头脑风暴 | [`…/pm-product-discovery/commands/discover.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/commands/discover.md) 等 | **拒绝整迁**；想法：澄清问题再写需求 → 进自研规矩一句 |
| 策略/定价/商业模式 | `pm-product-strategy/commands/*` | **拒绝**（主观商业） |
| 市场研究/竞品 | `pm-market-research/commands/*` | **拒绝**（易伪造研究） |
| 数据分析/实验 | `pm-data-analytics/commands/*` | **拒绝自动验证**；可提示「勿编造统计」 |
| 增长/GTM/战报 | `pm-marketing-growth/*`、`pm-go-to-market/*` | **拒绝** |
| **执行：PRD/故事/红队/测试场景/预验尸** | [`write-prd.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-execution/commands/write-prd.md)、[`write-stories.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-execution/commands/write-stories.md)、[`red-team-prd.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-execution/commands/red-team-prd.md)、[`test-scenarios.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-execution/commands/test-scenarios.md)、[`pre-mortem.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-execution/commands/pre-mortem.md) | **共享指导启发**；红队/预验尸 → **人工/语义**；结构小节 → **可复用 result-check** |
| 工具箱（简历/NDA/隐私政策） | `pm-toolkit/commands/*` | **拒绝** |
| AI shipping 占位 | [`ship-check.md`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-ai-shipping/commands/ship-check.md) | **拒绝**（已迁出；非本仓能力） |
| 校验脚本 | [`validate_plugins.py`](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/validate_plugins.py) | **不适合**进 rulemason 产品（插件市场校验） |

### 3.2 deanpeters/Product-Manager-Skills（CC BY-NC-SA）— 77 skills + commands

主题簇（frontmatter `theme`，人工枚举）：market-intelligence(18)、pm-artifacts(8)、discovery-research(7)、finance-metrics(7)、eol-transition(6)、career-leadership(5)、strategy-positioning(5)、validation-experiments(5)、workshops(5)、stakeholder-comms(4)、ai-agents(3)、meta-authoring(2)、product-lifecycle(2)。

与 rulemason **想法重叠（仅独立改写，不拷正文）**：

| PMS skill | 路径 | 映射 |
|---|---|---|
| prd-development | `skills/prd-development/SKILL.md` | ↔ pm-skills write-prd → **自研规矩** |
| user-story / splitting / mapping | `skills/user-story*` | ↔ write-stories → **规矩 + 可选结构提示** |
| epic-hypothesis | `skills/epic-hypothesis/SKILL.md` | 可检验假设 → **规矩一句**；验证本身 **人工** |
| derisk-measurement-advisor / pol-probe* | `skills/derisk-*`、`pol-probe*` | 风险登记 → **人工**；禁自动「值不值得做」 |
| autonomous-investigation | `skills/autonomous-investigation/SKILL.md` | 证据标签协议 → **规矩：区分事实/推断**；不移植调查代理 |
| 其余市场情报/财务/EOL/职业/工作坊 | 各 theme | **拒绝**进共享层 |

包装脚本（`scripts/*.py|sh`、`app/main.py`）：库维护工具，**不**进 rulemason。

### 3.3 与现有 rulemason 能力对照

| 已有能力 | 能表达什么 | 不够什么 |
|---|---|---|
| 共享 `rules/*` + init/update | 过程指导（如 `agent-coding-caution`） | 尚无「产品产物证据边界」专文 |
| `result-check`：must_contain / pattern / field / cjk / prose_hygiene | 记录里是否出现节标题、字段、文风提示 | **不**判断需求好坏、用户是否真实 |
| `workflow-gates` / OpenSpec | 方案/实现检查点 | 不替代 PRD 技能包 |
| `judge`（Jev，付费） | 可选语义审 | **本轮不跑、不新增依赖** |

## 4. 推荐 / 拒绝摘要

**推荐（最小有效）：**

1. 自研 `product-artifact-caution` 规矩并自动分发（启发：pm-skills 执行轨 + PMS 产物主题的**想法**）。  
2. 可选 hint 结构预设：**复用**既有检查类型。  
3. 红队/假设验证：保持人工或项目自选判断；不做成默认短名。

**拒绝：** 全套命令移植；PMS 正文再分发；商业/竞品/财务自动结论；把「有验收字样」当成上线合格；引入 REA 为运行时依赖。

## 5. 对 rulemason 的提升（若确认实现）

- AI 在工程仓写需求/验收时有**统一、可分发**的证据边界。  
- 与 `prose_hygiene` / `agent-coding-caution` 同模式：开箱提示、可选严格、不静默改旧 CI。  
- 避免许可证污染与范围膨胀。
