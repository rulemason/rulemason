# Tasks

## 1. 核心检测库

- [ ] 1.1 新增自研模块 `cjk_typography`：固定预处理（围栏/行内代码、MD 图链**目标**剥离、可见文案保留、裸 URL、行内 HTML）；实现七条短名（含四种一次叹问组合）；默认 units；allowlist；返回短名 + 码点偏移。验证：单测覆盖正/反例、四种组合、组合后再叠、剥离、链接可见文案、默认 units。
- [ ] 1.2 禁止从 Promptfoo / Rea / Cedar / Ruler / pangu / autocorrect 拷代码；无指北长文摘录。验证：源码检索无上述路径或大段指北原文。

## 2. 接入 result-check

- [ ] 2.1 接线 type `cjk_typography`：配置校验；无正文→无法判断；可选 path；省略 units 用默认表。验证：pytest 覆盖 exit 0/1/2、path skip、默认 units。
- [ ] 2.2 失败含短名与位置、不回显全文；旧 requirements 回归。验证：evidence 无整段原文；既有夹具仍 exit 0。
- [ ] 2.3 更新 `result-check --help`。验证：可检索 `cjk_typography` 与 allowlist。

## 3. 共享规则正文与分发

- [ ] 3.1 新增 `rules/cjk-typography.md`（首行注释格式同现有规则；七条自拟短名；写文档/方案/规格时遵守；点名 `cjk_typography` 强制）。验证：人工通读无指北原文大段抄录；短名与实现一致。
- [ ] 3.2 新增 `rules/result-check-contracts.md`（改 schema/prompt 时同 change 更新 requirements 与夹具并跑 result-check；项目约束不进共享文件）。验证：文中无具体项目字段名。
- [ ] 3.3 将两份加入 `COPIED_SHARED` 与必复制逻辑；更新 `code-style.block.md` / Claude / OpenCode 入口引用；`copies-README` 若列文件则同步。验证：临时项目 `init`/`update` 后 `.rulemason/rules/` 含二者；`rulemason check` 为 0；手改副本后 check 非 0；无前端项目也被复制。

## 4. 本仓样例、CI 与发版

- [ ] 4.1 对本仓 `README.md` 与 `rules/**/*.md` 跑首批规则；结果写入 `verification.md`。非平凡违规 ≤20：本 change 内修好；>20：停下只交清单、等用户确认后再修。CI `allowlist` 初始为空，仅样例后按需填并注明理由。验证：verification 含命令、结论表、违规计数；超额时无未授权的文档大改。
- [ ] 4.2 在 pytest（现有 `test` job）内按文件喂 `record.text` 覆盖上述路径（requirements 初始无 allowlist 或空数组）；失败含路径与短名；不改 job 名；不覆盖 `README.en.md` 与 archive。验证：故意弄坏一处本地可红；修回后全绿；CI 工作流仍只依赖 `test`。
- [ ] 4.3 版本 bump **0.8.32**（`__init__.py` + README 中英文 CI 钉）。验证：`--version` 与钉版本均为 0.8.32。
- [ ] 4.4 全量 ruff + pytest + `rulemason check`；完成 `verification.md`。验证：汇报含测试数字；tasks 无提前勾选。
