## MODIFIED Requirements

### Requirement: 产物写法基础版只住本仓库

本仓库 SHALL 维护一份产物写法基础版，至少包含：
- proposal：写明本次不做什么（Non-goals 小节或以「不做」开头的条目）；控制在 60 行以内，只写为什么和改什么。
- design：Context 里的关键事实注明出处（文件与行，或可复现的命令），没有核实的标「未核实」；每条决策写明被否决的备选与理由；Risks 每行「[风险] → 对策」；Migration Plan 写上线顺序与回滚；列出改动文件与估计行数，apply 后对照，超出一倍说明原因。
- specs：每个 Requirement 至少一个 Scenario，用 WHEN / THEN；用 SHALL / MUST，不用 should / may；每条 Requirement 正文不超过 500 个字符（`openspec validate --strict` 的上限）。
- tasks：每条两小时内可完成，并写明如何验证完成。

#### Scenario: 修改基础版
- **WHEN** 基础版的某条写法需要调整
- **THEN** 只改本仓库那一份，再由巡检报告哪些接入项目与之不一致

#### Scenario: 长度上限
- **WHEN** 新写的 proposal 超过 60 行，或某条 Requirement 正文超过 500 个字符
- **THEN** 按基础版拆短或精简后再交给用户

#### Scenario: design 的事实注明出处
- **WHEN** design 的 Context 写「check 对 ESLint 重复引入不报错」
- **THEN** 这句后面附上出处（如 `src/app/check.py:42` 或复现命令）；只是推断、没有查过的，句末标「未核实」

#### Scenario: 已接入项目升级后补上新条目
- **WHEN** 已接入项目升级 rulemason 后运行 `rulemason update --dry-run`
- **THEN** 补齐计划列出 `openspec/config.yaml`，`rulemason check` 在「产物写法与基础版的差异」报出缺少的 design 新条目；`rulemason update --yes` 后追加在项目 design 列表末尾，项目原有条目逐字不变

### Requirement: 产物写法与判断检查保持一致

基础版中能用正则判死的条目（Risks 行格式、Migration Plan 含回滚、Decisions 每个决策小节写明否决或备选理由）SHALL 由判断层的产物格式 lint 检查；需要理解语义的条目（写明不做什么）SHALL 由判断层基础规则检查，其 `enforces` 指向 `L1/proposal`。「design 关键事实注明出处」一条暂不配 lint 或判断规则，由 apply 后的独立审查检查（审查范围已含 change 产物）。基础版修改某条写法时，MUST 同时检查对应的 lint 或基础规则是否仍然一致。

#### Scenario: 放宽 Risks 写法
- **WHEN** 基础版决定同时接受「- **风险** → 对策」写法
- **THEN** 产物格式 lint 同步接受这种写法，两者在同一次改动中完成

#### Scenario: 决策缺否决理由
- **WHEN** design 的 Decisions 下有一个 `###` 小节，标题以下的正文没有出现「否决」「备选」「未采用」「不采用」或英文 Alternative / Rejected
- **THEN** `lint/design` 报 block，指出该小节标题，这份 design 不再送模型评估

#### Scenario: design 事实没有出处
- **WHEN** 方案刚写完时运行判断，design 的 Context 有一句关键事实没有出处也没标「未核实」
- **THEN** 判断不因此报出；apply 后独立审查把它列为 review
