<!-- result-check 契约：改被检查覆盖的结构化输出时同步要求文件。项目经 rulemason 生成的 .rulemason/ 副本引用：不把正文抄进项目指令，不手改副本 -->

当修改**已被**某份 `result-check` requirements 覆盖的结构化输出 schema、生成该输出的 prompt、或被检查覆盖的文案字段（含可选 `prose_hygiene`），或改工程交接用产品产物且项目选用了结构预设时：

1. 在**同一次** change / PR 内更新对应的 requirements JSON 与相关夹具；
2. 本地运行 `rulemason result-check --record … --requirements …`（或 `--preset hint|strict` / `product-artifact.hint|product-artifact.strict` / `verification-walkthrough.hint|verification-walkthrough.strict`）确认通过、提示或按预期失败并已处理。

项目专属的字段名、频率、白名单、小节标题与路径只写在各项目的 requirements / 夹具里，不写进本共享文件。产品产物字段与夹具须与 `product-artifact-caution` 的证据边界一致：结构命中 ≠ 业务验证通过。未使用 result-check 的项目可忽略本条。`.rulemason/result-check/prose-hygiene.*.json`、`product-artifact.*.json` 与 `verification-walkthrough.*.json` 种子仅首次写入，手改后 update 不覆盖。
