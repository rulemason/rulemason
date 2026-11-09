<!-- result-check 契约：改被检查覆盖的结构化输出时同步要求文件。项目经 rulemason 生成的 .rulemason/ 副本引用：不把正文抄进项目指令，不手改副本 -->

当修改**已被**某份 `result-check` requirements 覆盖的结构化输出 schema，或生成该输出的 prompt 时：

1. 在**同一次** change / PR 内更新对应的 requirements JSON 与相关夹具；
2. 本地运行 `rulemason result-check --record … --requirements …`（或等价库调用）确认通过或按预期失败并已处理。

项目专属的字段名、阈值、白名单与路径只写在各项目的 requirements / 夹具里，不写进本共享文件。未使用 result-check 的项目可忽略本条。
