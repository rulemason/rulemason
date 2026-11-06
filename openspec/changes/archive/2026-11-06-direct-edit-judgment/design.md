# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- 检查点「不走 OpenSpec 改代码时」四步：读主规格与检索、判路（改契约、冲突、未覆盖、不改行为）、汇报写明依据、只跑 ruff 与测试（`rules/workflow-gates.md`「不走 OpenSpec 改代码时」）。第 4 步写明「不跑自动精简与独立审查」。模板 `workflow-gates-no-openspec.block.md`、skill 第 7 节都按编号引用第 4 步。
- 判断引擎的产物类型是 `Literal["proposal", "design", "tasks", "specs", "copy", "chat"]`（`src/rulemason/judge/judge.py:47`）；`run_change` 对 design 先跑 `lint_design`，再按 `r.target == target` 选规则问裁判（`judge.py:489-514`）；`main` 有 `--change`、`--copy`、`--lint-only`、`--dry-run`、`--template`（`judge.py:576-600`）。
- 通用规则在 `src/rulemason/judge/base/judgments.yaml`，目前两条：`proposal-states-non-goals`（block 0.3）、`design-no-speculative-extension`（block 0.3）。
- 项目红线规则的写法：`target: design`、`enforces: L0/红线（不可违反）`、问题以「该设计最终采纳的方案是：」开头、阈值按回归结果校准（一个接入项目的 `openspec/judgments.yaml`：三条红线规则的 block 由 0 收紧到 0.2，注明了 2026-10-29 的回归数据）。模板注明「红线规则 block 起始 0.0（只 review 不拦），连续三个 change 零误拦后再收紧」（`rulemason judge --template judgments`）。
- skill 第 2 节第 2 步按项目里存在的东西提常见红线候选（数据库、部署、生产配置）（`skills/rulemason/SKILL.md` 第 2 节）。
- Jev 对代码 diff 的判断准确率：未核实，本 change 不依赖它。

## Goals / Non-Goals

**Goals:**
- 碰到敏感区域的直接改动回到 OpenSpec，享受现有的方案判断。
- 其余改了代码逻辑的直接改动，用一段文字说明接受 Jev 的红线与判路检查，不外发源码。
- 先以 review 为主跑一段时间，有数据后再收紧。

**Non-Goals:**
- 不判代码 diff，不拦截命令。
- 不改 apply 那条路，不改 `init` 模板。

## Decisions

1. **判的是直接改动说明，不是 diff。** 说明是 AI 判路时本来就要写进汇报的依据，固定成四段后交 Jev；Jev 擅长判文字，且不外发源码。否决送 diff：准确率没验证，公司项目未必允许源码外发。代价是判得准不准取决于说明是否如实，见 Risks。
2. **说明格式用 lint 卡住，缺段直接 block、不送模型。** 和 `lint/design` 同样做法：格式问题能用规则判死就不花模型调用。四段的标题固定，lint 只认这四个标题。否决让模型判断说明是否完整：贵且不稳定。
3. **说明存在仓库外的临时文件，用 `--direct <文件>` 传入。** 不进仓库、不留噪音；`--dry-run` 也能直接打印要发的内容。否决写进 `openspec/changes/` 下：直接改动不是 change，放进去会被 `check` 当成 change 统计。否决从标准输入读：AI 要先展示说明再判断，文件更好核对。
4. **直接改动的红线规则另写一条 `target: direct`，不让一条规则同时作用于两种产物。** 现有红线规则的问题是「该设计最终采纳的方案是：…」，阈值按 design 的回归数据校准过；直接改动换了措辞与语料，应有自己的阈值，从 0 起步。否决让 `target` 取列表：会改动已校准规则的适用对象，阈值也无从分开调。
5. **通用规则 `direct-route-respects-specs` 的 block 阈值先取 0。** 沿用红线规则「先只 review、零误拦后收紧」的惯例；先看它在真实直接改动上的分数分布。否决直接取 0.3：没有任何样本支撑。
6. **只在判断已启用且改了代码逻辑时跑，判定标准与 `/simplify` 相同。** 控制成本：只改文档、配置、样式的不调用。否决每次直接改动都跑：样式和文案调整多，调用会成倍增加。否决只在敏感区域跑：敏感区域已经走 OpenSpec 了。
7. **敏感区域写在 AGENTS.md「红线」一节下一行，由检查点读，不依赖判断层。** 它是项目专属内容，放在项目指令里；没启用判断的项目也能用。否决放进 `openspec/judge.yaml`：那份只有启用判断才有。否决改 `init` 模板加这一行：已接入项目拿不到，统一由 skill 补。
9. **把前一个 change 写进各处的覆盖范围说法一并改掉，不留到下一版。** 因为两个 change 合在同一个版本发出，留着旧说法会让同一版里的提示自相矛盾。改成「判断审 OpenSpec 方案、界面文案与直接改动的说明」，并区分「接入后没起过 change」时哪些判断用不上。否决只改文档不改规格：这几句被三条主规格（`rulekit-cli`、`workflow-gates`、`rules-layer-setup`）逐字锁定，不改规格，检查点和代码会与规格不符。
8. **不改第 4 步的编号，判断说明并进第 3 步。** 模板与 skill 第 7 节按编号引用第 4 步；在第 3 步「写明依据」之后接一句「判断已启用时把依据写成说明交判断」，编号不动。

## Risks / Trade-offs

- [AI 写的说明不如实或漏写改动范围，Jev 判不出问题] → 说明必须列出改哪些文件与检索命中；汇报里附说明原文，用户能一眼核对；跑一段时间后看是否需要独立审查核对说明。
- [review 太多成为噪音] → 阈值只影响 block；review 只在汇报里列一行，观察后按数据调整措辞或阈值。
- [敏感区域写得太宽，几乎所有改动都要起 change] → 候选只按真实存在的目录提出，逐条由用户确认；写得太宽时用户随时可删。
- [启用判断的项目每次改代码多一次 Jev 调用] → 只在改了代码逻辑时跑；成本记进 verification，跑一段时间后评估。
- [共享正文改动影响所有接入项目] → 没写敏感区、没启用判断的项目行为完全不变。

## Migration Plan

1. 改 `judge.py`、`base/judgments.yaml`、`rules/workflow-gates.md`、`skills/rulemason/SKILL.md`、`README.md`，补测试，跑 ruff 与测试。
2. 用 `rulemason judge --direct <样例说明> --dry-run` 在一个已启用判断的项目里检查请求体（不发送）；在本仓库对缺段说明跑 `--lint-only`。
3. 发版，发布说明写明：敏感区域要经 `/rulemason` 补写才生效；直接改动判断先只 review。

回滚：`uv tool install rulemason==<上一版>` 后在接入项目 `rulemason update`；项目里新增的 `target: direct` 规则在旧版引擎上不被选中（旧版只认原有产物类型），需要时由人删掉。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/judge/judge.py` | `direct` 产物类型、`--direct`、`lint_direct`、`run_direct` | +45 / −3 |
| `src/rulemason/judge/base/judgments.yaml` | 第三条通用规则 | +10 |
| `rules/workflow-gates.md` | 第 2 步敏感区域一条；第 3 步交判断一句 | +3 / −1 |
| `skills/rulemason/SKILL.md` | 第 2 节敏感区域候选；第 3 节巡检一句；第 4.2 节直接改动规则 | +12 / −1 |
| `README.md` | 判断一节写直接改动说明 | +4 |
| `tests/judge/test_engine.py`、`tests/test_templates.py` | 说明 lint、`--direct`、通用规则、正文措辞 | +70 |
