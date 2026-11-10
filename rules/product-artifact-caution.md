<!-- 产品产物审慎：写工程交接用的需求/故事/验收/验证说明时阅读。项目经 rulemason 生成的 .rulemason/ 副本引用：不把正文抄进项目指令，不手改副本 -->

写或改**工程交接用的产品产物**（PRD、用户故事、验收标准、verification / 成功标准说明、验证走查记录）时阅读。这是过程指导，**不是**默认判断红线，也**不会**因「像合格需求」自动判业务成功。

## 原则

1. **成功标准可检验**：写清谁在何时用什么证据核对（测试、日志、指标口径）；禁止只写「提升体验/满意度」而无核对方式。
2. **写明非目标**：v1 明确不做的范围，避免范围默默膨胀。
3. **验收可测**：验收条件应能被执行或复核（步骤 → 预期）；缺省时主动补齐或标为待决。
4. **证据边界**：区分已证实事实、推断与假设；**禁止编造**用户引言、调研结论、指标「已达成」或未提供的数据。
5. **验证走查**：先写**可观察期望**（人能看见/核对什么），再请人确认是否符合；逐条记录差距与待决。**禁止**把未执行的核对写成「已测 / 已通过」。
6. **结构提示 ≠ 质量合格**：`result-check` 可选预设只检查约定小节是否出现，**不**证明需求正确、价值成立或功能已验证通过。

## 何时会跑确定性检查

仅当有人调用 `rulemason result-check` 且 requirements（或 `--preset product-artifact.hint|product-artifact.strict` / `verification-walkthrough.hint|verification-walkthrough.strict`）含相应检查项。`init` / `update` **只分发规矩与（缺失时）种子文件**，不扫描仓库正文、不改 `check` 退出码。

**默认 `severity=hint`（结构预设）：** 缺约定小节记「提示」，单独不导致非零。需要门禁时显式选用对应的 `.strict`。非法配置仍为 exit 2；同次其他失败/无法判断仍非零。

**产物结构默认同义标题（标题行）：** 非目标 / 不在范围内 / Out of Scope / Non-goal(s)；成功标准 / 验收 / 验收标准 / Success Criteria / Acceptance。

**走查结构默认同义标题（标题行）：** 验证走查 / 走查记录 / Walkthrough / Verification Walkthrough；可观察期望 / 期望结果 / 期望表现 / Expected / Expected Behavior / Expected Result / Observable Expectation；差距与待决 / 差距 / 不符项 / Gaps / Discrepancies。

结构命中不代表实质合格；代码围栏内的假标题可能误报（本检查不剥围栏）。
