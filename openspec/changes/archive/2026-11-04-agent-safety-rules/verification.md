# Verification：agent-safety-rules

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。

## 写代码前检查点

`rulemason judge --change agent-safety-rules`：pass 3 / review 0 / block 0。

## 1. 自动精简与独立审查

**自动精简**：跳过。本次只改共享正文、skill、产物写法基础版、本仓库 `openspec/config.yaml`、README 与测试，`src/rulemason/` 没有改动，无代码改动，跳过精简。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：block 0，review 15，全部修复：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | review：proposal 说新增内容放进「九条之外」，与 design 决策 1 不符 → 改为「新增一节「外部操作与凭据」」 |
| 正确性 | review：三级只按「删除」分，发布、发送这类收不回的操作没地方放 → 改为读 / 写 / 删除或作废，写包含收不回但不销毁已有东西的操作；「读」会读到密钥与个人数据 → 写明不含；项目想长期放开没有出口 → 补「项目指令另有写明的从项目指令」；候选 1 自相矛盾、触发条件 3 没举例 → 改写并举例；规格里「开发版」发版后失效 → 去掉；第 8 条场景暗示记了日志就行 → 删去；design 两处出处没有行号 → 补上 |
| 安全 | review：proposal 提到真实入侵与外泄 → 改为「整理 AI 协作中的实际事故复盘」；环境文件可能被提交 → 补「确认不会被提交」 |
| 文字质量 | review：第 8 条重复「内部函数」、「写」一条重复说同意 → 精简 |
| 测试 | review：核心行为（不执行、只引用变量名、只检查是否存在）没断言、多项 and 断言看不出哪项失败 → 补断言、改为循环带消息；九条条数已有 `test_rules_wording_key_sections` 断言 |
| 变更卫生 | review：测试空行 → 改正 |

材料缺口经自查：artifact-rules 两条与 rules-layer-setup 一条 MODIFIED 与主规格逐条比对，原有 scenario 全部保留；`openspec validate --strict` 通过。

第二轮：block 0，review 4。按规则修完后只跑 ruff 与测试，不审第三轮：

- README、README.en、proposal 还是旧的「可回滚 / 不可逆」说法 → 改为与正文一致的三级。
- tasks 1.2、4.1 的引文与实际措辞不符 → 改为实际措辞。
- 「强推」放在「不销毁已有东西」里，但它会抹掉别人的提交 → 「写」的例子改为推送 tag，强推覆盖共享分支归入「删除或作废」，规格、design、测试同步。
- 三条常见红线候选互相矛盾（候选 1 允许授权后写库、候选 3 不许），且候选 1、2 带「逐次授权」后并不比通用规则严 → 候选改为「线上数据库只读，迁移与改数据由人执行」「不代为发布到生产，发布由人触发」，与候选 3 一致且都比通用规则严；design 决策 5 同步说明。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：493 passed（改动前 491；新增 2 条，`test_artifact_base_limits` 补 1 条断言）。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案。

## 6. 额外步骤

改了 `rules/` 与 `openspec-base/`：

- 本仓库：同步 `openspec/config.yaml` 前，开发版 `rulemason check` 报「rules.design 缺少或改写了：Context 里的关键事实注明出处…」；同步后为空。
- 任务 3.2 临时项目：用已安装的 0.8.12 接入（旧基础版，design 列表最前有一条项目追加条目），开发版 `check` 报出缺少新条目；`update --dry-run` 的补齐计划列出 `openspec/config.yaml`；`update --yes` 后 diff 只多一行，追加在 design 列表末尾；再 `check` 差异为空。
- 项目甲、乙、丙（开发版 `update --dry-run`）：只刷新 `.rulemason/rules/code-style.md`、rulemason skill 副本与 `.rulemason.yaml`，补齐计划只有 `openspec/config.yaml`；`check` 报出 design 新条目缺失，升级后 `rulemason update --yes` 即可补上。

## 与 design 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `rules/code-style.md` | +14 / −2 | +17 / −2 | 新节含标题 14 行 |
| `skills/rulemason/SKILL.md` | +6 / −1 | +7 / −2 | |
| `openspec-base/artifact-rules.yaml` | +1 | +1 | |
| `openspec/config.yaml` | +1 | +1 | |
| `tests/test_templates.py` | +20 | +32 | 两轮审查补的断言；未超出一倍 |
| `README.md`、`README.en.md` | +2 / −2 | +2 / −2 | |

## 偏差与发现

- **补齐计划不列条目原文**：`rulemason update --dry-run`（文字与 `--json`）只列出要补齐的文件 `openspec/config.yaml`，不列要追加的条目；条目由 `rulemason check` 的「产物写法与基础版的差异」报出。规格 artifact-rules 的场景与 tasks 3.2 原写「补齐计划列出 design 新条目」，按现有行为改写；没有为此改代码（design Goals：不改 `src/`）。
- **三级的界线在审查中改过**：从「可回滚 / 不可逆」改为「会不会销毁已有东西」，发布、发送、推送 tag 归入「写」，强推覆盖共享分支归入「删除或作废」；规格、design、proposal、README 已同步。
- **常见红线候选改得更严**：从「逐次授权」改为「由人执行 / 由人触发」，三条之间不再矛盾。
- **发布说明要写**：新增「外部操作与凭据」一节与第 8 条措辞；`/rulemason` 补红线时按项目实际情况提常见候选；产物写法 design 新增「关键事实注明出处」，升级后 `rulemason check` 会报出缺这一条，运行 `rulemason update --yes` 追加。
