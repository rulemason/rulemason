## Why

`/rulemason` skill 的「存量清理」一节约 7600 字节，占 `SKILL.md` 的三分之一，可日常的补项目信息、巡检都用不到它，每次调用 skill 却都要一起读进来；后续要把清理经验写进去，这一节还会变长。另外，接入项目做多阶段清理时，第一个阶段提交就用了 `refactor(cleanup): <模块>`，诊断随即把整个模块当成已完成、从队列里划掉，而模块里还有十几个超标函数没清。

## What Changes

- 存量清理的正文从 `SKILL.md` 移到同目录的 `cleanup.md`。`SKILL.md` 第 7 节只留入口：用户要做存量清理时读 `cleanup.md` 并照做。
- skill 副本从一个文件变成两个：`init` / `update` 把 `SKILL.md` 与 `cleanup.md` 都复制到各工具的 skill 发现路径，清单记录校验值，`check` 照常比对。已接入项目运行 `rulemason update` 后补上 `cleanup.md`。
- 修完成标记：一个模块分几次提交时，只有最后一次用 `refactor(cleanup): <模块>`；之前的阶段提交写成 `refactor(cleanup-step): <模块> 第 N 步`，诊断不把它算完成；收尾时计划里还有步骤没做完，就不把模块当成已完成，最后一行是继续这个模块的命令；全部做完才请用户按 `refactor(cleanup):` 提交。
- 不做：不改清理流程本身的步骤和措辞，只搬家（完成标记与收尾两处除外）；清理流程的重写放到后面的 change。
- 不做：不改写作类规则的加载方式、不改归档第 5 步、不调字数上限，这些留给「写作类规则按需加载」那个 change。
- 不做：诊断不新增「进行中」状态，有阶段提交、没有最终提交的模块照旧按未完成排队。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `rulekit-cli`：skill 副本包含 `SKILL.md` 与 `cleanup.md` 两个文件。
- `rules-layer-setup`：存量清理正文单独成文件；模块完成只认最后一次清理提交，阶段提交另用前缀。

## Impact

- 改：`skills/rulemason/SKILL.md`，新增 `skills/rulemason/cleanup.md`；`src/rulemason/shared.py` 的 skill 文件清单；`tests/test_templates.py` 中切片读取第 7 节的断言改为读 `cleanup.md`；`tests/test_check.py` 新增旧项目升级补齐 `cleanup.md` 的测试。
- 打包无需改动：`pyproject.toml` 已把整个 `skills/rulemason/` 收进安装包。
- 接入项目升级后，`check` 会先在「生成副本」报副本与本机版本应生成的不一致，提示运行 `rulemason update`，这是预期行为。
