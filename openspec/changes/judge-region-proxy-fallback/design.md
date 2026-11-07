# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- 建连接：`Judge._jev` 懒建 `TypeSafeClient`，传入 `httpx2.Client(trust_env=False)`，注释写明是有意绕过 shell 代理（`src/rulemason/judge/judge.py:278-293`）。这一行从 0.8.0 起没变过（`git log -S trust_env -- src/rulemason/judge/judge.py` 只有首版提交）。
- 发请求：`Judge.ask` 第 3 步调用 `self._jev().system_one(...)`（`judge.py:315`）；一个 `Judge` 在一次运行里复用同一个连接，`close()` 在 `main` 末尾调用（`judge.py:273-276`、`:644-645`）。
- `trust_env`：httpx2 默认 True；为 True 时经 `urllib.request.getproxies()` 读 `HTTP(S)_PROXY`、`ALL_PROXY`、`NO_PROXY`，macOS 与 Windows 上还读系统代理设置；为 False 时全部忽略（`uv run python -c "import inspect, httpx2._utils as u; print(inspect.getsource(u.get_environment_proxies))"`）。
- 451 的来历：SDK 把非 2xx 响应转成 `TypeSafeAPIError`，带 `status`；451 不在默认重试状态码里（408、429、5xx），会立刻抛出（`.venv/.../typesafe_sdk/_core/retry.py:64`、`_core/errors.py:198-200`）。
- 命令行最外层：`cli()` 只把 `TypeSafeAuthenticationError`（401）、`ConfigError`、`OSError` 转成一句话，451 会带堆栈抛出（`judge.py:652-666`）；issue #24 的报错正是这样。
- 已有测试用 `monkeypatch` 替换 `judge.main` 抛 SDK 异常来测最外层提示（`tests/judge/test_engine.py:395-407`）。

## Goals / Non-Goals

**Goals:**
- 直连可用的人行为与现在一致；直连被按地区拒绝、本机有代理的人不用做任何设置。
- 解决不了时，一句话说清是地区问题、怎么办。

**Non-Goals:**
- 不检测代理能否连通，不在没有代理时猜代理地址。
- 不改 SDK 的重试策略与超时。

## Decisions

1. **「本机设有代理」= `urllib.request.getproxies()` 含 `https` 或 `all`。** 与 httpx 在 `trust_env=True` 时读的是同一份来源，判定「有代理」就等于改走代理后真的会经代理。否决只看 `HTTPS_PROXY` 环境变量：漏掉小写变量、`ALL_PROXY` 与 macOS / Windows 的系统代理。否决发一个探测请求看代理通不通：多一次网络往返，且通不通由重发的那次请求自己说明。
2. **换路放在 `Judge.ask` 里：捕获 status 为 451 的 `TypeSafeAPIError`，若还没走代理且本机有代理，就关掉当前连接、标记改走代理、按 `trust_env=True` 重建连接并重发一次；`_jev` 按这个标记决定 `trust_env`。** 标记存在 `Judge` 实例上，同一次运行后面的请求直接用代理连接，库用法同样生效。否决写一个 httpx 传输层在 HTTP 层重试：要自己处理请求体重放与 SDK 的重试头，复杂得多。否决在 `cli()` 捕获后整次重跑 `main`：已打印的结果会重复一遍，库用法也不生效。
3. **说明行用 `print` 输出到标准输出**，写在发生换路的那条结果之前，与 judge 其他输出同一通道。否决写到标准错误：judge 全部输出都在标准输出，分两处会让顺序错乱。
4. **地区拒绝的一句话提示放在 `cli()` 最外层，与 401 的处理并列：捕获 status 为 451 的 `TypeSafeAPIError`，本机没有代理时提示设置 `HTTPS_PROXY`，有代理（说明经代理也被拒）时提示换一个所在地区可用的代理。** 库用法仍抛原异常，由调用方决定怎么处理。否决在 `ask` 里转成自定义异常：只有命令行需要这句话，多一个异常类型没有别的调用方。
5. **选路结果只存在内存里，每次运行先直连。** 否决写进 `~/.config/rulemason/env`：换了网络后会一直走代理，结果反而错；451 返回很快，每次运行多花的只是第一次请求。
6. **依赖加 `httpx2[socks]`。** 环境里有 `ALL_PROXY=socks5://…`（Clash 等工具常这样导出，常与 `HTTPS_PROXY` 同时设）时，httpx2 按 `trust_env=True` 建连接会为每个代理挂载建传输层，没装 `socksio` 就抛 `ImportError`，命令行会打印堆栈（独立审查发现，`env -i … ALL_PROXY=socks5://127.0.0.1:1` 实测复现；用户确认）。`socksio` 是纯 Python 小包，SOCKS 代理因此也能用。否决只认 http(s) 代理并显式传给连接：只有 SOCKS 代理的人仍用不上，还要放弃 `NO_PROXY` 并改规格措辞。

## Risks / Trade-offs

- [`NO_PROXY` 覆盖了 `api.typesafe.ai`，「改走代理」实际仍直连，再次 451 时提示「换代理」不准] → 少见；提示里的「Typesafe 按地区拒绝」仍然正确，接受。
- [代理本身偶发断连（当初绕开代理的原因）] → 只有直连已被拒绝时才用代理，这时没有更好的路；SDK 对连接错误仍会重试。
- [Typesafe 以后改用别的状态码表示地区拒绝] → 只认 451，其他状态码行为不变；出现新情况时再按实际状态码补。
- [Linux 与 WSL 的桌面系统代理设置读不到] → README 写明设 `HTTPS_PROXY` 环境变量；提示语也指向这个变量。

## Migration Plan

1. 改 `judge.py`，补测试，改 README，跑 ruff 与测试。
2. 发版（版本号按发版时 PyPI 已有版本递增），发布说明写明「被按地区拒绝时自动改用本机代理」；在 issue #24 回复版本号，请报告人升级后实测（他的环境能覆盖「直连 451、代理通」这条路）。
3. 接入项目无需操作。

回滚：`uv tool install rulemason==<上一版>`；本次不改任何文件格式与配置。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/judge/judge.py` | 判断本机有无代理；`Judge` 记录是否改走代理、`_jev` 按它建连接、`ask` 遇 451 换路重发；`cli()` 加 451 的一句话提示 | +30 / −3 |
| `tests/judge/test_engine.py` | 直连成功不用代理、451 有代理换路且只提示一次、451 无代理一句话退出、经代理仍 451 一句话退出 | +80 |
| `README.md` | 「判断」一节补一句 | +2 |
| `pyproject.toml`、`uv.lock` | 新增 `httpx2[socks]` 依赖（审查后加入） | +1、+16 |
