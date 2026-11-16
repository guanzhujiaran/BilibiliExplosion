# be-bilibili-crawler：B 站 Web 接口风控头与参数对齐计划书

> 先有本计划书，再改代码。依据规则「新增或修改功能时先修改计划书」。
> 本次为功能补齐（对齐浏览器真实请求形态），不是单纯 bug 修复。

## 1. 背景与证据

用 REA 的 `capture_browser_scenario` 启动 Chromium 153（locale=`zh-CN`），
对 B 站真实页面做受控回放抓包，保留完整请求头与 query：

| 页面 | REA Evidence ID | 关键接口 |
| --- | --- | --- |
| `https://www.bilibili.com/` | `ev_0da0872b51857bbaaf107c99d1e25d559ba1c9d154f360173e08477f7a0d5840` | `x/web-interface/nav`、`x/web-interface/wbi/search/default`、`x/web-show/wbi/res/locs`、`GenWebTicket`、gaia 网关 |
| `https://space.bilibili.com/1/dynamic` | `ev_8c5157ae67c7c027999f4abaddcd184809b510975d202eb36651843577e32c73` | `x/polymer/web-dynamic/v1/feed/space`、`x/space/wbi/acc/info`、`x/space/reservation`、`x/frontend/finger/spi`、`GenWebTicket` |
| `https://t.bilibili.com/463864834570585963` | `ev_ad019dbd7f5f39e78083741fb49bce52160ae9a3755e87ae83b9f5627bc48673` | `x/polymer/web-dynamic/v1/detail`、gaia 网关 |

证据包已导出到 `/tmp/bili_rea_evidence_{homepage,dynamic,detail}.json`，
解析后的 API 清单在 `/tmp/bili_api_{homepage,dynamic}.json`。
以上均为**受控回放观测**，不是页面自发行为；响应体未作为本次改动依据。

另外用本地回显服务器实测（curl_cffi + `default_headers=False`）：
当前 `my_async_httpx.request` **只发送代码显式给出的 header**，
`impersonate` 不会自动补 `sec-ch-*` / `sec-fetch-*` / `priority`。

## 2. 现状差距（观测 vs 生产代码）

| # | 项 | 浏览器真实请求 | 生产代码现状 | 结论 |
| --- | --- | --- | --- | --- |
| 1 | `x-bili-locale-json`（query） | `www`/`space` 域名的 Web API 几乎全带：`{"c_locale":{"language":"zh","script":"Hans"},"always_translate":false}` | 完全没有 | **新增** |
| 2 | `x-bili-device-req-json`（query） | feed/space：`{"platform":"web","device":"pc","spmid":"333.1387","mobi_app":"web_cn"}`；detail：`{"platform":"web","device":"pc","spmid":"333.1368"}` | 只有 `{"platform":"web","device":"pc"}`，缺 `spmid` / `mobi_app` | **补齐**，`spmid` 必须等于当次 `web_location` |
| 3 | `features`（feed/space） | 17 个 flag（见下） | 只有前 10 个 | **更新** |
| 4 | `sec-ch-ua` / `sec-ch-ua-mobile` / `sec-ch-ua-platform` / `sec-fetch-dest` / `sec-fetch-mode` / `sec-fetch-site` / `priority` | 17/17 个 API 请求都带；`accept-language: zh-CN` | `UserAgentParser` 只发 4 个基础头（UA/accept/accept-language/accept-encoding） | **新增**，按 UA 推导，保持与 UA 平台一致 |
| 5 | `x-bili-web-req-json`（query） | 浏览器**没有**发 | feed/space 与 detail 都额外发了 | 暂不删除（未知参数通常被忽略，删除收益未验证），在风险项记录 |
| 6 | `csrf=""`（GenWebTicket） | 浏览器没有发 | `gen_web_ticket` 额外发了 | 暂不改动，未观测到失败 |
| 7 | `features`（detail） | 18 个 flag | 完全一致 | 不改 |
| 8 | `timezone_offset` | 抓包环境为 UTC → `0`；生产用 `-480`（北京时间） | `-480` | 不改，长期配置正确 |
| 9 | `x-bili-locale-json` 在 detail | 未出现 | 未发 | 不改 |
| 10 | `x-bili-trace-id` / `x-bili-metadata-ip-region` | 出现在**响应**头 | 由 gRPC 侧处理 | 不改，本次只处理请求侧 |

## 3. 本次目标

1. 把观测到的 Web API 请求形态固化成常量 / 工具函数，避免各接口各写一份。
2. feed/space、detail 两个抽奖主链路接口的 query 对齐浏览器。
3. 所有经 `prepare_request_data` / `_gen_headers_base` 发出的请求补上浏览器 Fetch Metadata 与 Client Hints。
4. 增加回归测试，防止后续改动又把 `spmid` / `locale` / `features` 改回去。
5. 不触碰 gRPC metadata（已有独立计划书）、不触碰代理与 cookie 池逻辑。

## 4. 改动清单（逐文件）

### 4.1 新增常量：`Service/GrpcModule/Grpc/Bapi/Constants.py`

- `BILI_WEB_LOCALE_JSON`：`{"c_locale":{"language":"zh","script":"Hans"},"always_translate":false}`
- `FEATURES_SPACE_DYNAMIC`：feed/space 的 17 个 flag（顺序照抄抓包）
- `FEATURES_DYNAMIC_DETAIL`：detail 的 18 个 flag（值照抄现有内联字符串，仅抽成常量）

### 4.2 新增工具函数：`Utils/加密/wbi加密.py`

- `gen_bili_device_req_json(spm_id: str, *, include_mobi_app: bool = False) -> str`：
  生成 `{"platform":"web","device":"pc","spmid":"<spm_id>"}`，
  `include_mobi_app=True` 时追加 `"mobi_app":"web_cn"`；用 `separators=(",", ":")` 与浏览器一致。
- 不改动 `encWbi` / `get_wbi_params` / `gen_dm_args` 的签名和行为。

### 4.3 修改：`Service/GrpcModule/Grpc/Bapi/BiliApi.py`

- `get_space_dynamic_req_with_proxy`：
  - `features` 换成 `FEATURES_SPACE_DYNAMIC`；
  - 在 `gen_dm_args` 之后、wbi 签名之前加入 `x-bili-locale-json: BILI_WEB_LOCALE_JSON`；
  - `x-bili-device-req-json` 换成 `gen_bili_device_req_json(spm_id, include_mobi_app=True)`。
- `get_polymer_web_dynamic_detail`（两个分支都要）：
  - `features` 换成 `FEATURES_DYNAMIC_DETAIL`（值不变）；
  - wbi 签名前加入 `x-bili-locale-json`？——**不加**：detail 来自 `t.bilibili.com`，
    抓包未带该参数；只把 `x-bili-device-req-json` 换成
    `gen_bili_device_req_json("333.1368")`（与当次 `web_location` 对齐）。
- `get_lot_notice`：接口在 `api.vc.bilibili.com`，本次抓包未覆盖，**不改**。

### 4.4 修改：`Utils/GrpcUtils/UserAgentParser.py`

- `get_headers_dict` 在基础 4 个头之外补充：
  - `sec-fetch-dest: empty`、`sec-fetch-mode: cors`、`sec-fetch-site: same-site`、`priority: u=1, i`；
  - `sec-ch-ua-mobile: ?0`；
  - `sec-ch-ua-platform`：从 UA 推导（`Windows NT`→`Windows`，`Macintosh`→`macOS`，
    `Android`→`Android`，`iPhone|iPad`→`iOS`，`CrOS`→`Chrome OS`，`Linux`→`Linux`）；
  - `sec-ch-ua`：仅 Chromium 系（Chrome / Edge / Opera）推导品牌与版本，
    Firefox / Safari 不发（与真实浏览器一致）。
- 所有新增头都允许 `extra_headers_dict` 覆盖，保持向后兼容。
- 不引入动态 import，类型标注用具体 `dict[str, str]` / `str`。

### 4.5 新增测试：`test/test_web_bapi_headers.py`

- UA→platform 映射（Windows/macOS/Linux/Android/iOS）断言；
- Chromium UA 产生 `sec-ch-ua`，Firefox UA 不产生；
- `extra_headers_dict` 能覆盖默认 `sec-fetch-site`；
- `gen_bili_device_req_json` 的 `spmid` / `mobi_app` 输出与抓包一致；
- feed/space 的 `features` 常量与抓包 17 个 flag 完全一致。

## 5. 验证方式

1. `uv run pytest test/test_web_bapi_headers.py -q`（用 `/home/minato/.local/bin/uv`，当前环境未加入 PATH）。
2. 本地构造 `get_space_dynamic_req_with_proxy` 的 params（不真发请求），打印完整 URL，
   逐项与 Evidence 中 feed/space 的 query key 集合比对。
3. 改动涉及只读查询路由之外的爬虫代码，**不重启容器**即可做静态验证；
   若需实跑，重启 `be-bilibili-crawler`（写库/采集侧）并观察 bapi 日志中的 `-352` / `-412`。
4. `git diff --stat` 确认只改了上述文件。

## 6. 风险与回滚

- `sec-ch-ua` 由 UA 推导，若 `fake_useragent` 返回少见的 Chromium 变体，
  品牌可能与真实浏览器略有差异；选择「宁可不发也不发错」策略（非 Chromium 不发）。
- 新增头会改变请求指纹，理论上可能触发风控；改动集中在 `UserAgentParser` 一处，
  回滚只需还原该文件。
- `x-bili-web-req-json` / `csrf=""` 暂不删除：浏览器不发不代表服务端拒绝，
  删除收益未验证，留待后续 A/B 观察。
- 本计划不改 wbi 签名算法；所有新增 query 必须在 `get_wbi_params` **之前**写入，
  否则 `w_rid` 与服务端口径不一致。
