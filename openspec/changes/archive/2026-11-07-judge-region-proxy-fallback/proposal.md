## Why

[issue #24](https://github.com/rulemason/rulemason/issues/24)：一位在大陆网络、出口走 `HTTPS_PROXY` 的用户，每次 `rulemason judge` 都失败，报 `451 Typesafe is not available in your region`。judge 调 Jev 时写死直连、不读代理（当初是因为直连可用时代理偶发断连），这位用户的网络正相反：直连被按地区拒绝，只有代理能通。没有参数或配置能换路，只能改安装目录里的代码，升级后又被盖回去。

用户配好 key 就应该能用，不应再去弄懂代理开关。

## What Changes

- judge 调用 Jev 时先直连，行为与现在相同；直连收到 451（按地区拒绝），且本机设有代理时，提示一句并经代理重发同一请求；同一次运行后面的请求都走代理。
- 被按地区拒绝而无法经代理解决时（本机没有代理，或经代理仍是 451），以非 0 退出，用一句话说明原因与怎么办，不打印 Python 报错。
- README「判断」一节补一句：被按地区拒绝时自动改用本机代理。
- 不做：环境变量或 `--proxy` 参数让用户手选代理；默认就走代理；把选路结果写进配置文件；超时与连接失败时改走代理；判断或检测代理本身能否连通。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `judge-engine`：新增两条——被按地区拒绝时改用本机代理；无法经代理解决时给一句话提示。

## Impact

- 代码：`src/rulemason/judge/judge.py`（`Judge` 建连接与发请求、命令行最外层的报错）；`tests/judge/test_engine.py`；`README.md`。
- 依赖：新增 `httpx2[socks]`（引入 `socksio`），本机代理是 SOCKS 时也能经代理连接。
- 库用法：项目代码 import `Judge` 调用时同样生效，接口不变。
- 接入项目：无需操作，升级 rulemason 即可。
