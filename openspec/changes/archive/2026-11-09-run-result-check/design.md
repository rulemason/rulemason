# Design

## Context

- See `proposal.md` — Why。本期排除 Skill 检查（覆盖旧需求稿中 RR-05 为本期必须的表述）。
- 现有 CLI 只分发 `init` / `update` / `check` / `remove` / `key` / `judge`（`src/rulemason/cli.py` 约 L13–42）。`check --json` 的 `schema` 当前为 1，字段契约见主规格 `rulekit-cli`「check --json 输出结构化结果」。
- `judge` 输出 pass / review / block，与本检查的通过 / 失败 / 无法判断 / 输入错误正交；本设计不映射二者。
- 首个接入场景取自产品仓快照（`/tmp/yaomancy-product`，提交 `5b9c5e35…`，**未核实**是否与线上一致）：解读结构化约定在 `backend/app/interpretation/prompt.py` 的 `OUTPUT_SCHEMA` / `STEPS_OUTPUT_SCHEMA`；离线 fixture 在 `frontend/e2e/fixtures/interpret.json`；真模型 eval 报告仅当手动跑 `backend/tools/run_quality_eval.py` 并给出路径才落盘，CI **不**跑（`.github/workflows/ci.yml`）。产品路径无编程 Skill 轨迹。
- 本 change 仅规划；下列入口名与退出码为**设计选择**，apply 前仍可在实现任务中微调命名，但不得退回「凡错误也 exit 0」。

## Goals / Non-Goals

**Goals:**

- 纯 Python 确定性核对核心 + 可被 CI 消费的独立入口。
- 状态语义与总体通过条件符合 specs；fixture 仅作离线验收样例。
- 保持 `check` / `update` / `judge` 行为不变。

**Non-Goals:**

- 不实现 Skill / harness / 采集器；不改 Yaomancy；不跑付费 eval；不接产品 HTTP API。
- 不引入 Promptfoo / Rea / Cedar / Ruler 依赖；不做自动脱敏产品。
- 不为「日后 eval 报告」预留解析模块、插件点、配置开关或 CI 步骤；帮助里若出现字段对照，只是给调用方的说明，不是本 change 的实现范围。

## Decisions

1. **独立子命令（推荐名 `rulemason result-check`）**，不复用 `check` / `judge`。  
   - 否决：塞进 `check` — 会污染副本巡检的 `--json` schema 与退出语义。  
   - 否决：复用 `judge` — judge 依赖 Jev/密钥与 pass/review/block，与本地确定性检查正交。

2. **输入为调用方文件（记录 JSON + 要求 JSON，或单文件打包）**，路径由 CLI 参数传入。  
   - 否决：检查器内置去读 Cursor/Claude 会话目录 — 超出「记录由调用方提供」，且各工具格式不一。  
   - 否决：本期自动打产品 `/interpret` — 用户明确排除自动接 API。

3. **退出码（设计选择，非已实现事实）**：`0` 仅总体通过；`1` 存在必需失败或无法判断；`2` 输入错误（空要求集、非法模式、损坏 JSON、点名已排除的 Skill 项等）；其它未捕获异常保持非 0。  
   - 否决：一律 `0` 只靠 JSON 字段区分 — CI 默认不读 stdout 会漏拦。  
   - 否决：与 `check` 共用同一套 `next.code` — 语义不同，避免脚本误解析。

4. **机器可读结果**：独立 JSON（自有 `schema` 版本，从 1 起），含逐项状态、汇总、来源/范围/限度；**不**写入或扩展 `check --json` schema 1。  
   - 否决：复用 check 的 `layers`/`findings` 形状 — 字段语义不匹配。

5. **Skill 要求的处置**：若要求文件仍含 Skill 出现类条目 → 记「输入错误」，该项不得为「通过」，总体不得宣称通过。  
   - 否决：静默当「不适用且总体仍可通过」而不提示 — 易把排除项偷成绿灯。  
   - 否决：做成可插拔的 Skill 检查开关「默认关闭」— 等于为本期排除的能力预留配置，属投机扩展。

6. **首个验收夹具**：仓库内用合成的解读结构化样例（可对照 Yaomancy fixture 字段形状，但**不**把产品仓文件拷进本包运行时；测试夹具自维护）。实现与测试只认「已是检查输入形状」的调用方记录；若帮助提及 eval 报告，仅说明调用方如何自行映射字段后再交进来，本期不写报告解析器、不接 CI。  
   - 否决：测试里联网打 DashScope — 违反零额外 API 与本期范围。  
   - 否决：先做通用「多来源适配层」再接 fixture — 超出本期，属投机扩展。

7. **默认人读报告**：只给状态、标识、短摘录/路径；完整原文需显式标志才输出。  
   - 否决：默认全文回显 — 易把密钥或用户问句打进 CI 日志；也不承诺自动脱敏。

## Risks / Trade-offs

- [调用方交来伪造记录] → 对策：限度写明「可核对≠防伪」；不宣称真实性验证。
- [fixture 被误当成线上证据] → 对策：验收与文档强制写来源类型；汇总限度区分 fixture / 报告 / 未覆盖在线。
- [用户仍提交 Skill 项期望绿灯] → 对策：规格与实现将其视为输入错误或明确不适用且不得通过；帮助文案写明本期排除。
- [子命令命名日后微调] → 对策：tasks 先定公共库 API，CLI 名在实现首任务锁定并写进帮助；归档前与 specs「独立入口」一致即可。
- [与产品既有护栏重复] → 对策：本检查不替换产品 `score_fidelity` 等；只做调用方显式要求的通用确定性核对。

## Migration Plan

1. 仅在本仓库实现库 + CLI + 测试并发版（apply 阶段）；不改接入项目。
2. 文档示例：如何用解读 JSON fixture 调用新入口；标明非真实会话。
3. 接入项目若要用：自行在脚本中调用；本期不改其 workflow。
4. 回滚：去掉新子命令与库模块即可；`check`/`update`/`judge` 无耦合，卸载无迁移脚本。

## 文件与估计行数（apply 时对照）

| 文件 | 动作 | 估计行数 |
|---|---|---|
| `src/rulemason/result_check.py`（或包目录） | 新增 | 250–400 |
| `src/rulemason/cli.py` | 修改 | +30–50 |
| `tests/test_result_check.py` | 新增 | 200–300 |
| 包内帮助/README 片段 | 修改 | +40–80 |
| OpenSpec 主规格归档时同步 | 归档阶段 | 规格正文迁入 `openspec/specs/run-result-check/` |

超出一倍须在完成汇报说明。
