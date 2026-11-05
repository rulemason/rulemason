# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- ESLint 基础规则的注释写着「项目当前代码超出时，在自己的配置里用当前最复杂函数的值覆盖，写明递减计划，只降不升」（`lint/eslint-base.mjs:7-8`）；主规格 `shared-code-style`「ESLint 基础规则由项目继承」同样写「SHALL 把上限设为当前最复杂函数的值」，场景「项目乙使用复杂度棘轮」把上限设为 35。React 落法末段引用这句说明（`rules/react.md:27`）。
- ruff 基线流程在 `skills/rulemason/SKILL.md` 第 5 节（87–112 行）：统计 → 分四类写计划 → 列给用户确认 → 确认后照做；遗留豁免写进 `[lint.per-file-ignores]`，注释「接入前遗留，改到该文件时清掉」。第 2 节第 6 步与第 3 节巡检都指向它（`SKILL.md:47`、`:60`）。ESLint 没有对应的节。
- `check` 认 ESLint 继承只看 `import … from "…eslint-base.mjs"` 这一行（`src/rulemason/check.py:577` `eslint_refs`），`ESLINT_ANCHORS`（`check.py:56`）只用于自动插入；项目在配置数组里追加按文件的条目不影响识别。
- 没有测试钉着 `eslint-base.mjs` 的注释原文或 `react.md` 的末段（`grep -rn "最复杂函数" src tests` 无结果）；`tests/test_templates.py` 只校验 skill 目录里只有 `SKILL.md`、入口模板引用的副本路径。
- 检查点「不走 OpenSpec 改代码时」第 1 步只写按能力名筛选（`rules/workflow-gates.md:67`）；「提交信息」一节三行（`:86-88`）；「外部操作与凭据」在 `rules/code-style.md`，讲的是平台操作分级，不涉及 git。
- 本机那个存量改造项目的检出分支工作区里没有 `.rulemason.yaml`，两份 `eslint.config.js` 也没有引入 `eslint-base.mjs`（`grep -rn eslint-base apps/*/eslint.config.js` 无结果），接入所在的提交在远端分支上；手写过渡豁免的具体形态未核实。
- 建议页记录的数字：接入时前端两个包分别报 151 与 408 个 error；上限从 205 降到 30 后超过 15 的函数从 173 变 188，拆出的 55 个函数里 8 个停在 30（来自建议页，未在本机复现）。

## Goals / Non-Goals

**Goals:**
- 前端接入有和 ruff 对称的基线流程，口径不再误导。
- 四段检查点措辞（检索主规格、改既有测试、提交与推送）让 AI 一条命令就能执行。

**Non-Goals:**
- 不让 `check` 读 ESLint 基线条目，不做标记块。
- 不改 `init`、`update`、`check` 的任何代码。

## Decisions

1. **ESLint 基线按文件写 flat config 条目，只用注释标记，不做命令也不做标记块识别。** 否决 `rulemason baseline --eslint` 命令：Python 包要调 node、处理多包工作目录，目前只有一个调用方。否决用 `// rulemason:legacy` 标记块让 `check` 报条目数：ruff 侧也只是注释标记，两边保持对称，等第二个项目再出现需求时一起做。
2. **改主规格「ESLint 基础规则由项目继承」这一条，而不是另加一条。** 旧条文本身是误导的源头，留着会和新条矛盾。场景「项目乙使用复杂度棘轮」改写成按文件条目，新增「拆分不卡线」。否决只改注释不改规格：主规格是 `/rulemason` 判路时读的东西，注释改了规格没改，AI 仍会按规格指导用户。
3. **B1 用检索口径，写在第 1 步里，不新增命令。** AI 一条 grep 就能做；`specs-for --diff` 要按语言解析 diff，rulemason 没有 JS 解析器。否决把检索写成单独一步：它是「找相关主规格」的一部分，拆开会让人以为可以只做其一。
4. **C4 新开「改既有测试时」小节，两条路各引用一句。** 否决写两遍：同一段逻辑两处。否决只写在不走 OpenSpec 一路：apply 阶段的存量清理同样会碰到。小节放在「不走 OpenSpec 改代码时」之前、「自动精简与代码审查」之后。
5. **E1 进「提交信息」扩成的「提交与推送」，只写原则不写命令。** 否决放进 `code-style.md`「外部操作与凭据」：那一节是平台操作分级，塞进 git 细节会变长且跑题。否决写 `git commit --only -- <路径>`：共享正文不写具体子命令选项，项目可以自己选 `--only` 或 `--pathspec-from-file`。`git worktree` 是建议不是命令选项，可以写。
6. **skill 新节的统计用命令表前端 lint 的命令加 `--format json`，按文件 × 规则汇总，复杂度取该文件报出的最大值。** 否决让 AI 读 ESLint 的默认输出：按文件汇总要自己数；JSON 输出有 `filePath`、`ruleId` 与消息里的复杂度数值。否决一步到位算「下一档」：第一次建基线只记当前值，递减在之后每次改到文件时做。

## Risks / Trade-offs

- [按文件条目多，ESLint 配置变长] → 一文件一行按路径排序，条目多时汇报只列前 20 行与总数，同 ruff。
- [已按旧口径设了全局上限的项目不会被 `check` 报出] → skill 新节写明迁移做法，下次 `/rulemason` 巡检前端 lint 报问题时带出；不加检查项。
- [检索口径依赖 AI 执行，没有机械保证] → 场景写清命中后的动作；CLI 粗提取版等口径跑顺后再评估。
- [共享正文变长] → 新小节各控制在 6 行以内，「提交与推送」不超过 8 行。
- [改 `rules/` 与 `skills/` 影响所有接入项目] → 额外步骤：在一个有前端的接入项目 `update` 并按新节建一次 ESLint 基线，结果写进 verification.md，不提交。

## Migration Plan

1. 改 `lint/eslint-base.mjs`、`rules/react.md`、`rules/workflow-gates.md`、`skills/rulemason/SKILL.md`、`README.md`，跑 ruff 与测试。
2. 在一个有前端的接入项目运行 `rulemason update`，用新节对一个前端目录做一次 ESLint 基线（只在本机，不提交），前端 lint 通过。
3. 发版，发布说明写明 ESLint 基线与四段检查点措辞；接入项目 `rulemason update`。

回滚：`uv tool install rulemason==<上一版>` 后在接入项目 `rulemason update`，副本回到旧文字；本次不改任何文件格式与清单结构。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `lint/eslint-base.mjs` | 注释改口径 | +3 / −2 |
| `rules/react.md` | 末段一句改；新小节「重构等价性」 | +9 / −1 |
| `rules/workflow-gates.md` | 第 1 步加检索句；新小节「改既有测试时」；两路各引用一句；「提交与推送」 | +14 / −3 |
| `skills/rulemason/SKILL.md` | 新第 6 节「建立 ESLint 基线」，原第 6 节顺延为第 7；第 2 节第 6 步与第 3 节巡检各加半句 | +22 / −3 |
| `README.md` | 「日常」一句补 ESLint | +1 / −1 |
