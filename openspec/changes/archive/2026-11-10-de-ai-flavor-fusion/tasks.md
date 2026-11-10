## 1. 规格与规则

- [x] 1.1 按确认决策更新本 change 的 proposal/design/specs
- [x] 1.2 新增 `rules/prose-hygiene.md`、`rules/agent-coding-caution.md`；更新契约一句
- [x] 1.3 分发：COPIED_SHARED、入口模板、AGENTS/CLAUDE

## 2. 检查与入口

- [x] 2.1 `prose_hygiene.py` + result-check 接线：`severity`、状态「提示」、em_dash 可选
- [x] 2.2 包内 hint/strict 预设；init/update 幂等种子；CLI `--preset`
- [x] 2.3 测试：hint exit0、strict 非零、旧失败/非法仍非零、幂等、正反例、回归

## 3. 验证

- [x] 3.1 ruff / pytest / openspec strict
- [x] 3.2 付费 Jev：不跑并注明
- [x] 3.3 verification + artifacts；本地提交；不推送
