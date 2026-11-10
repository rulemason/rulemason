# 功能前后对比（自写示例，标明虚构）

基线：0.8.34 / `71564ca`。以下正文均为**自写示例**，非真实用户研究或线上指标。

## 规矩分发

| | 前 | 后 |
|---|---|---|
| 共享规矩 | 无产品产物证据边界专文 | `rules/product-artifact-caution.md` 经 init/update 必复制 |
| 入口 | 无 | AGENTS / CLAUDE / OpenCode 引用并写明阅读场合 |
| init/update | 不扫产物 | **仍不扫**；只分发规矩与缺失种子 |

## 结构检查（可选）

自写记录（虚构）：

```text
# 导出 CSV
## 摘要
让用户导出报表。
## 成功标准
上线 30 天内导出成功率 ≥ 99%（以服务端日志为准）。
## 非目标
v1 不做定时调度。
## 验收
Given 已登录用户 When 点击导出 Then 收到 CSV。
```

| 调用 | 缺「非目标」小节时 |
|---|---|
| `--preset product-artifact.hint` | 项为「提示」，exit **0** |
| `--preset product-artifact.strict` | 项为「失败」，exit **1** |
| `--preset hint` | **仍**跑 prose-hygiene，不是产物结构 |
| 不传预设 / 不用该 requirements | 不检查小节（关闭） |
| 自定义种子后 update | 保留用户改动 |

**结构命中 ≠ 99% 已达成，≠ 真实用户需要导出。**

## severity 增强

| | 前（0.8.34） | 后 |
|---|---|---|
| `must_contain` / `pattern` | 缺失一律失败 | 缺省仍失败；显式 `severity=hint` 可提示 |
| `prose_hygiene` | hint/strict | 不变 |
| `--preset hint\|strict` | prose | **不变**（不偷换） |
