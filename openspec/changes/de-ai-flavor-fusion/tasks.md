## 0. 确认门（本轮只做到此）

- [ ] 0.1 用户确认双轨方案与五条待决（见 artifacts `02-fusion-recommendation.md`）
- [ ] 0.2 确认前**禁止**改 `prose_hygiene` 实现、测试行为、推送/合并 `bb187b2`

## 1. 文案轨（确认后）

- [ ] 1.1 按决议调整短名集与 `rules/prose-hygiene.md`（含去 AI 味表述边界）
- [ ] 1.2 更新 `prose_hygiene` 实现/测试与 CLI 帮助；保持未声明类型时兼容
- [ ] 1.3 误报集夹具（合法破折号、代码块、disable/allowlist）

## 2. 编码轨（确认后）

- [ ] 2.1 自研 `rules/agent-coding-caution.md`（四原则意译 + 归因 + 非作者判别无关声明）
- [ ] 2.2 按决议接入 `COPIED_SHARED` / 入口模板 / 测试
- [ ] 2.3 与 `workflow-gates` 交叉引用（先确认再实现），不新增 result-check 类型

## 3. 验证（确认并实现后）

- [ ] 3.1 ruff / pytest / openspec strict
- [ ] 3.2 付费 Jev 回归按当时政策；默认可不跑
- [ ] 3.3 本地提交；推送/PR/发版仅在用户另行授权后
