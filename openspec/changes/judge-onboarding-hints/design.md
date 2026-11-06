# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- `init.guide_key` 第一行就是「本机有 key 就 return」；条件未满足只打一行，满足且没 key 才问（`src/rulemason/init.py` `guide_key`）。
- `check.judge_label` 有四种结果：已启用（有 `openspec/judgments.yaml`）、缺条件、条件满足没 key、条件满足有 key「要启用时在 AI 工具中运行 /rulemason」（`src/rulemason/check.py:1015`）。这句只在识别表里，不进第一行。
- 归档后的提示写在共享检查点「归档」第 5 步，条件是「已归档 change」正好 3 且「判断」一行含「本机未配置 key」（`rules/workflow-gates.md:92`）；主规格是 `workflow-gates`「归档够 3 个时提示一次配置 key」。
- skill 第 2 节第 4 步要求「判断与文案检查保持『可选，未启用』」，第 3 节巡检要求「用户没有提出要启用就不做第 4 步」（`skills/rulemason/SKILL.md:47`、`:66`）。
- 接入日期 `joined` 与按日期筛归档的 `dated_archives(root, since)` 已在 0.8.20 加入（`src/rulemason/check.py` `dated_archives`，`collect` 里算出 `since`）。
- 那个接入项目：接入时已归档 60 个、本机有 key、接入后没有归档过 change（来自用户的复盘，本机未复现）。

## Goals / Non-Goals

**Goals:**
- 判断条件满足的项目，在接入、补项目信息、接入后第一次归档这三个时点各被告知一次。
- 每次告知都说清判断只审方案与文案，避免误以为能覆盖直接改动。

**Non-Goals:**
- 不在 `check` 第一行或每次运行时提示。
- 不记录「用户拒绝过」。

## Decisions

1. **一次性的触发点用已有的事实算，不新增状态。** 「接入后归档 change 正好 1」与「已归档正好 3」都是从归档目录与 `joined` 算出的，归档动作本身让它们只成立一次。否决在清单里记「已提示过」：要写文件、要随项目提交，且 `check` 是只读的。
2. **`check` 识别表加「接入后归档 change」一行，检查点从 `--json` 的 `facts` 读它。** 和「已归档 change」并列，算法复用 `dated_archives`。否决把数字并进「已归档 change」一行（如「60（接入后 1）」）：检查点要按数字比较，拆成两行更不容易读错。
3. **已有 key 时 `init` 只输出一行说明，不提问。** 启用判断要整理规则、逐条确认，不是在终端答 y 能完成的事；终端里能做的只有告诉人下一步去哪。否决在 `init` 里直接问「要不要现在整理」：`init` 不调 AI，答了也做不了。
4. **skill 在补项目信息的汇报末尾问一次，本次不进入整理。** 保留「每次运行只做一个阶段」的规矩（`rules-layer-setup`「按安装状态而非归档数决定下一步」），只把「下一步可以做什么」说出来。否决补完后直接接着整理：一次运行改动太多，用户也可能这次不想做。
5. **覆盖范围那句话照实说，接入后没起过 change 时直接说「启用后暂时用不上」。** 否决只说「可以启用」：会重演这次以为搭了就有用的误会。

## Risks / Trade-offs

- [「接入后归档正好 1」在接入当天归档的项目上会晚一次触发] → 接入当天的归档按接入前算（0.8.20 的口径），下一次归档就会提示；影响只是晚一次。
- [推算不出接入日期的项目只剩「正好 3 个」一个触发点] → 和现在一样，不比现在差；`rulemason update` 会补上 `joined`。
- [用户不想启用，却在三个时点各被告知一次] → 每处只一句、不提问（skill 那处是问一次），之后不再出现。

## Migration Plan

1. 改 `init.py`、`check.py`、`rules/workflow-gates.md`、`skills/rulemason/SKILL.md`、`README.md`，补测试，跑 ruff 与测试。
2. 在一个已接入、有 key、未启用判断的项目上运行 `rulemason check`，看识别表的「接入后归档 change」；用临时 worktree 验证 `init` 结尾那一行。
3. 发版。接入项目 `rulemason update` 后拿到新检查点与 skill。

回滚：`uv tool install rulemason==<上一版>` 后在接入项目 `rulemason update`；不改任何文件格式。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/init.py` | `guide_key` 已有 key 时输出一行 | +6 / −2 |
| `src/rulemason/check.py` | 识别表「接入后归档 change」 | +3 |
| `rules/workflow-gates.md` | 「归档」第 5 步改写 | +1 / −1 |
| `skills/rulemason/SKILL.md` | 第 2 节末尾问一次；第 3 节巡检那句改措辞 | +3 / −1 |
| `README.md` | 「判断」一节两句 | +2 |
| `tests/test_init.py`、`tests/test_check.py`、`tests/test_templates.py` | 新提示与新事实行 | +40 |
