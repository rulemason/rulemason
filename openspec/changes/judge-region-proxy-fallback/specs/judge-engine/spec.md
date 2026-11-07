## ADDED Requirements

### Requirement: 被按地区拒绝时改用本机代理

`rulemason judge` 与库 `Judge` 调用 Jev 时 SHALL 先直连，不读代理设置。直连收到 HTTP 451（Typesafe 按地区拒绝），且本机设有代理（`HTTPS_PROXY`、`ALL_PROXY` 等环境变量，或操作系统提供的代理设置）时，SHALL 输出一行说明直连被按地区拒绝、已改用本机代理，并经代理重发同一请求；同一次运行之后的请求 SHALL 直接经代理，MUST NOT 再次输出这行说明。直连成功时 MUST NOT 使用代理。MUST NOT 把选路结果写进任何文件，用户无需设置任何参数或配置项。

#### Scenario: 直连被按地区拒绝，本机有代理
- **WHEN** 设有 `HTTPS_PROXY`，直连 Jev 返回 451，经代理返回正常结果，运行 `rulemason judge --change x`
- **THEN** 输出一行说明已改用本机代理，判定结果与直连成功时的格式相同，退出码按判定结果决定

#### Scenario: 同一次运行发多个请求
- **WHEN** 设有 `HTTPS_PROXY`，直连返回 451，运行一次需要多个请求的 `rulemason judge --copy`
- **THEN** 只有第一个请求先直连，之后的请求都直接经代理，说明只输出一次

#### Scenario: 直连成功
- **WHEN** 设有 `HTTPS_PROXY`，直连 Jev 返回正常结果
- **THEN** 不经代理，不输出改用代理的说明，输出与现在相同

#### Scenario: 下一次运行重新先直连
- **WHEN** 上一次运行已改用代理，再次运行 `rulemason judge`
- **THEN** 这次仍先直连

### Requirement: 无法经代理解决地区拒绝时给一句话提示

Jev 返回 451 而无法经代理解决时，`rulemason judge` SHALL 以非 0 退出，输出一句以错误标记开头的话，说明 Typesafe 按地区拒绝了当前网络，并按情况给出怎么办：本机没有设代理时，提示设置 `HTTPS_PROXY` 指向能访问 Typesafe 的代理后重试；已经经代理仍被拒绝时，提示换一个所在地区可用的代理。MUST NOT 打印 Python 堆栈。

#### Scenario: 本机没有代理
- **WHEN** 没有设置任何代理，直连 Jev 返回 451，运行 `rulemason judge --change x`
- **THEN** 输出一句说明被按地区拒绝、本机没有设置代理、可设置 `HTTPS_PROXY` 后重试，退出码非 0，没有 Python 堆栈

#### Scenario: 经代理仍被拒绝
- **WHEN** 设有 `HTTPS_PROXY`，直连与经代理都返回 451
- **THEN** 输出改用代理的说明后，再输出一句说明经代理仍被按地区拒绝、请换一个所在地区可用的代理，退出码非 0，没有 Python 堆栈
