<!-- 文案卫生：给人读的套话滤镜。项目经 rulemason 生成的 .rulemason/ 副本引用：不把正文抄进项目指令，不手改副本 -->

写给人读的正文（产品文案、说明、方案叙述）时阅读。确定性手段：`rulemason result-check` 的 `prose_hygiene`。

**何时会跑：** 仅当有人调用 `result-check` 且 requirements（或 `--preset`）含 `type: prose_hygiene`。init/update **不会**自动对仓库扫文或改 CI 退出码。`rulemason check` 巡检副本一致性，**不**跑本检查。

**默认 severity=`hint`：** 命中记「提示」，单独不导致非零退出（开箱提示、不阻断 CI）。需要门禁时显式 `severity: strict` 或 `--preset strict`。非法配置仍为 exit 2；同次其他失败/无法判断仍非零——提示不吞错。

**推荐短名（预设默认）：** `chatbot_closer`、`signpost_opener`、`not_just_contrast`。
**高级可选（默认关闭）：** `em_dash`（破折号误报高，**不等于**去 AI 味）。

反例可放行内代码，或 `<!-- rulemason-disable -->` / `<!-- rulemason-disable 短名 -->` 配对 enable。可选 allowlist、path、max_hits。

**不是作者判别**；不自动改字或改事实。种子预设：`.rulemason/result-check/prose-hygiene.hint.json` 与 `.strict.json`（仅首次写入，不覆盖已有）。
