# 最小有效融合方案（已确认 A+B）

基线：**rulemason 0.8.34** / `71564ca`。OpenSpec：`pm-artifact-guidance-fusion`。

## 用户收益

1. 写 PRD / 用户故事 / 验收 / verification 时有一份**共享、只读**的工程向规矩（可检验标准、非目标、证据边界）。  
2. 对调用方提供的产物记录做**结构提示**，默认不阻断 CI。  
3. 不背全套 PM 助手与 CC-NC 再分发风险。

## 功能前后对比（自写示例，标注）

### 示例 A — 规矩层（必做）

**前：** AI 可写出「提升用户满意度」而无检验方式，且无非目标。  
**后：** 入口要求阅读 `product-artifact-caution`：须写可核对标准与非目标；仍**不会**因文案自动 fail CI。

### 示例 B — 可选结构提示（自写记录，**虚构**，非真实用户数据）

```json
{
  "text": "# 导出 CSV\n\n## 摘要\n让用户导出报表。\n\n## 成功标准\n上线 30 天内导出成功率 ≥ 99%（以服务端日志为准）。\n\n## 非目标\nv1 不做定时调度。\n\n## 验收\nGiven 已登录用户 When 点击导出 Then 收到 CSV 文件。\n"
}
```

- `--preset product-artifact.hint`：若删掉「非目标」小节 → 状态「提示」，**exit 0**。  
- `--preset product-artifact.strict`：同上 → **exit 1**。  
- `--preset hint`：**仍**为 prose-hygiene，不是产物结构。  
- 另有 `must_contain` 失败 → 仍 **exit 1**（提示不吞错）。

**明确：** 结构提示 **≠** 「99% 已达成」或「用户真实需要导出」。

## 输入 / 输出 / 配置

| 项 | 内容 |
|---|---|
| 分发 | `init`/`update` → `.rulemason/rules/product-artifact-caution.md` + 缺失时种子 |
| 执行 | 仅 `rulemason result-check`；`check` 不扫产物 |
| 预设 | `product-artifact.hint`（默认提示）/ `product-artifact.strict`；关闭=不传该预设 |
| 自定义 | 改种子或 `--requirements`；update 不覆盖已有种子 |
| 退出码 | 提示单独不阻断；非法配置 2 |

## 新增 vs 复用

| 能力 | 判定 |
|---|---|
| 产品产物规矩 | **新增**规则文件 + 分发 |
| 节标题存在性 | **复用** `pattern` + severity |
| 结构化 PRD JSON 字段 | **复用** `field`（无本轮 severity） |
| 文风套话 | **复用** `prose_hygiene`（`--preset hint|strict` 不变） |
| 新 check type / 新命令 | **不新增** |

## 误报 / 漏报 / 退出码

- 误报：合法不同标题 → 用户改种子；默认 hint。围栏内假标题为边界。  
- 漏报：有标题但标准不可测 → **预期**；靠规矩与人工。  
- 退出码：不改旧 cjk/field/prose 失败语义。

## 测试 / 打包 / 迁移

- 分发与入口；种子幂等；hint/strict/旧失败/非法；wheel/sdist；干净安装执行。  
- 付费 Jev：**不跑**。  
- 迁移：旧项目无感，直至选用 `product-artifact.*`。
