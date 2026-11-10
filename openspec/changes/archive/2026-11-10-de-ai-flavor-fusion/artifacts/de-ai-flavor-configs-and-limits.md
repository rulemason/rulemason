# 默认 / 严格 / 关闭配置与限制

## 默认（hint，开箱）

包内与种子：`.rulemason/result-check/prose-hygiene.hint.json`

```json
{
  "schema": 1,
  "checks": [{
    "id": "prose-hygiene",
    "type": "prose_hygiene",
    "rules": ["chatbot_closer", "signpost_opener", "not_just_contrast"],
    "max_hits": 50,
    "severity": "hint"
  }]
}
```

```bash
rulemason result-check --record record.json --preset hint
```

命中 → 状态「提示」，**exit 0**（单独不阻断 CI）。

## 严格（用户选择）

```bash
rulemason result-check --record record.json --preset strict
# 或 requirements 中 "severity": "strict"
```

命中 → **exit 1**。

## 关闭

- 不调用 `result-check`，或 requirements **不含** `prose_hygiene`：无文风检查。
- 种子文件可手改 / 删除；update **不覆盖**已有种子，也不强迫把 prose 加进你的 CI。

## 高级：打开 em_dash

```json
{
  "id": "prose-hygiene",
  "type": "prose_hygiene",
  "rules": ["chatbot_closer", "signpost_opener", "not_just_contrast", "em_dash"],
  "severity": "hint"
}
```

## 放行

- 行内/围栏代码等与 cjk 相同预处理屏蔽
- `<!-- rulemason-disable -->` / `<!-- rulemason-enable -->`（可带短名）
- `allowlist`、`path`、`max_hits`

## 限制（保留原分析事实）

| 项 | 说明 |
|---|---|
| 非作者判别 | 不判断「是否 AI 写的」；只匹配显式短名模式 |
| 非自动改写 | 不 `--fix`、不改事实 |
| anti-slop | 启发来源 miqdadbadjuber/anti-slop MIT `3b75daa`；短名与检测自研，不复制词表/代码 |
| Karpathy skills | multica-ai/andrej-karpathy-skills 声明 MIT `2c60614`；**非**官方；社区仓库无 LICENSE 文件；仅行为启发，不嵌 skill 正文 |
| REA | 付费/代理路径不引入；免费静态启发式仅作背景，本期不依赖 |
| 付费 Jev | 本 change 验证未跑 |
| 误报 | 尤其 `em_dash`；故默认关闭 |
| 退出码 | 0 通过（可含提示）；1 失败/无法判断；2 输入错误。提示不吞掉 1/2 |
