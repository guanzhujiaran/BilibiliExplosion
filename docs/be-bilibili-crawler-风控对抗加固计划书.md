# be-bilibili-crawler：风控对抗加固计划书（TLS/UA、Cookie 持久化、头序基线、行为节流）

> 先有本计划书，再改代码。依据规则「新增或修改功能时先修改计划书」。
> 本文覆盖 2026-11-16 提出的 5 项加固；其中 gaia/WASM 一项经证据核查后**判定当前不可实施**，
> 明确记录在 §3，不假装完成。

## 1. 背景与调研结论

在此前的 Web 接口参数对齐（REA 抓包）之后，继续排查传输层与行为层风险，发现：

1. **TLS 指纹与请求头自相矛盾**：`Utils/代理/SealedRequests.py:309,346,415` 每次请求从 61 个
   impersonate target 里 `random.choice`，实测抽样 12 次有 8 次落在 Firefox / Safari / Edge；
   但请求头 UA 来自 `CONFIG.rand_ua`（桌面 Chrome 系）+ 显式 `sec-ch-ua-platform`。
   即「JA3 说 Firefox，header 说 Chrome」。实测默认头注入（本地回显）确认各 target 的
   默认 UA 互不相同，而我们 `default_headers=False` 把它们全关了，只留下错位。
2. **Cookie 池不跨进程**：`BiliCookie.py:33-38` 是进程内存，重启全丢；每次都用
   全新 buvid3/buvid4/bili_ticket 组合跑业务，容易被关联识别。
3. **头顺序未做基线**：REA 证据 `/tmp/bili_rea_evidence_dynamic.json` 中 17 个 API 的头顺序
   全部是字典序：`:authority, :method, :path, :scheme, accept, accept-encoding, accept-language,
   cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform,
   sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent`。
   当前 `UserAgentParser` 插入序是 UA 打头、`sec-fetch-*` 在 `sec-ch-ua` 之前，与浏览器相反。
   但本地实测 curl_cffi 会**自行重排**传入 header（不保留 dict 插入序），
   所以本项以「代码内组装顺序对齐 + 文档基线 + 单测」为交付，不宣称改变 wire 顺序。
4. **H2 SETTINGS / WINDOW_UPDATE 不可单独控制**：curl_cffi 0.17.0 没有相关 API，
   随 impersonate target 固定注入（`docs/grpc_reverse_evidence/grpc_capture_verification.md:192` 同样结论）。
   本项以「选定正确 target 即继承正确 H2 指纹」为交付，不伪造。
5. **行为层只有失败退避**：`RedisRequestProxy` 有代理 QPS 与退避，但没有业务请求间的
   随机节流；`Utils/通用/SleepTimeGen.py` 已有模拟真人短/中/长等待的工具，尚未接入请求链路。
6. **gaia-bin / WASM**：真机 22 次 gRPC 抓包中 `x-bili-metadata-gaia-bin` 一次都没出现
   （`grpc_capture_verification.md:166`、`grpc_capture_raw_dump.md:13-34`），
   `dfp/dfpP` 标注「未还原/需真机导出」（`grpc_call_reconstruction.md:328`），
   `ExClimbCongLing` 是空函数 + Todo（`BiliApiBase.py:174-188`），全仓无 `.wasm` 文件、无逆向脚本。
   **没有样本、没有算法，无法还原**——按证据边界不实施，详见 §3。

## 2. 本次目标

1. 让 impersonate target 与显式 UA / Client Hints 成对一致，消除最容易被交叉校验的错位。
2. Web Cookie 池挪到 Redis，跨进程/重启复用，沿用设备池的 key + LRU + TTL 范式。
3. 把 Web 头组装顺序改为字典序（对齐 REA 证据），并给 gRPC metadata 头序加回归测试。
4. 在 `request_with_proxy` 入口增加可配置的业务请求随机节流，豁免 cookie/metadata 激活专线。
5. 明确记录 gaia/WASM 的不可行性，并给出回补所需的前置条件。

## 3. gaia / WASM：不可实施说明（交付物为本文档结论，非代码）

经核查，实施 `ExClimbCongLing` WASM 加密还原**缺少两个必要前提**：

- **真机样本**：22 次真机 gRPC 调用中 gaia-bin 出现 0 次，Web 侧激活链路的响应体也未留存；
- **算法/二进制**：仓库内无 `.wasm`、无 WASI 运行时、无 dfp/dfpP 生成算法，逆向文档 §9 明确标「未还原」。

强行写一个「看起来像」的实现只会引入假头，反而增加风险。因此本次**不新增** gaia-bin 相关代码。
回补条件：拿到一台真实 Android 设备的 `ExClimbCongLing` 请求/响应样本 + 对应 JS/WASM 文件，
再做独立逆向计划。届时按本计划书 §2 的配置文件与 §4.5 的测试骨架扩展即可。

（可实施的旁支已确认：`x-bili-aurora-eid` 算法已知——mid 与 `ad1va46a7lza` 循环 XOR 后 base64，
但仅在**登录态**出现，本项目当前是游客态，不需要发。）

## 4. 改动清单（逐文件）

### 4.1 TLS 指纹与 UA 绑定 + 会话复用：`Utils/代理/SealedRequests.py`

> 2026-11-16 追加：会话复用与指纹绑定必须一起做——每请求随机挑 target 会让同一个
> buvid 会话的 JA3 来回漂移，比原状更像机器人。一个会话 = 一个固定指纹 + 一组同源 UA
> + 若干复用连接，才贴近真实浏览器。

- 新增 `WEB_IMPERSONATE_TARGETS`：只保留带明确主版本号的桌面 Chrome target
  （`chrome\d{3}`），从 `SUPPORTED_IMPERSONATE_TARGETS` 过滤得出，
  不硬编码未探测的名字；过滤后为空则回退裸 `chrome`。
- 新增 `chrome_major_of(target)` / `rand_web_ua(target)`：按 target 的主版本号生成同源
  桌面 Chrome UA（Windows / macOS / Linux 三选一），使 `Chrome/152` 与 `chrome152` 成对。
- 新增 `pick_web_fingerprint(headers) -> (target, new_headers)`：在发请求前统一改写 UA，
  保证 TLS 指纹与 HTTP 头同家族同主版本；不改调用方对象本身。
- **按会话固定**：从 `headers` 的 cookie 串中取 `buvid3`（没有则退回按 UA 哈希），
  用稳定哈希 `int(md5(buvid3), 16) % len(WEB_IMPERSONATE_TARGETS)` 选 target。
  同一 buvid 永远命中同一指纹，杜绝会话内 JA3 漂移。
- **Session 池复用**：`MYASYNCHTTPX` 持有 `dict[target, AsyncSession]` LRU 池（带 TTL），
  session 以固定 `impersonate=target` + `http_version=V2_0` 建一次，后续请求复用；
  池化仅限**业务请求**，`local_exit_only=True` 的 cookie/metadata 激活链路继续每次新建短连接
  （它们是一次性握手取 ticket，复用无收益且有跨出口串味风险）。
- 代理仍走 request 级 `proxy` 参数，换出口不换指纹 / UA。
- 保留 `TRUST_ENV=False`；池需要在进程退出时 `aclose()` 全部 session（挂到 FastAPI lifespan shutdown）。

### 4.2 UA 与头序对齐：`Utils/GrpcUtils/UserAgentParser.py`

- `get_headers_dict()` 返回的 dict 按 REA 观测的字典序组装：
  accept / accept-encoding / accept-language / [cookie] / origin / priority / referer /
  sec-ch-ua / sec-ch-ua-mobile / sec-ch-ua-platform / sec-fetch-dest / sec-fetch-mode /
  sec-fetch-site / user-agent（extra_headers 仍最后 update 覆盖）。
  注：curl_cffi 会自行重排，此项的收益主要在「代码可审计 + 测试可锁定」。
- Client Hints 与 UA 一致性校验：`sec-ch-ua` 的版本号从传入 UA 推导（沿用现有 `_client_hints_brands`）。
- 与 4.1 配合：`prepare_request_data` 在 B 站 Web 请求上优先使用 `resolve_ua_for_impersonate`。

### 4.3 Web Cookie 池 Redis 持久化：`Service/GrpcModule/Grpc/Bapi/BiliCookie.py`

- 新增 `CookieRedisStore`（放在同文件或 `Models/AntiRisk/Bili/` 下的新模块），
  照抄 `Utils/GrpcUtils/metadata/device_pool.py` 的范式：
  - key `bili:web_cookie:{uuid}`，Hash 存 `CookieWrapper.model_dump_json()`；
  - zset `bili:web_cookie:lru` 记 `score=last_access_ts`，上限沿用 `pool_size`；
  - TTL 用 `_setex` 按 `expire_ts` 剩余秒数设置，过期 key 自然消失；
  - `note_352` 的 `times_352` / `able` 随 JSON 一起持久化，跨进程继续生效。
- `get_bili_cookie()` 改为优先读 Redis（命中则刷新 LRU score + 反序列化返回），
  未命中再走现有生成链路并回写 Redis；Redis 异常时降级为原内存池，不阻断业务。
- `warmup_bili_cookie_pool()` 写入同一 Redis 池。
- 配置放 `CONFIG.py` 的 `BiliCookieConfig`（L571-592）：`persist_to_redis: bool`、`redis_key_prefix`、
  `redis_pool_size`；env 前缀沿用 `BILI_COOKIE__`。默认**开启**，可用开关回滚。
- 保持 `CookieWrapper` 构造签名 / `note_352` 去重语义 / `able` 判定不变（现有测试依赖）。

### 4.4 业务请求随机节流：`Utils/代理/redisProxyRequest/RedisRequestProxy.py`

- 在 `request_with_proxy()` 的 `resolve_tier` 之后、`_select_proxy` 之前插入：
  ```
  if not request_conf.local_exit_only and throttle_enabled:
      await retry_sleep(random.uniform(min_s, max_s))
  ```
  - 豁免：`local_exit_only=True`（cookie/metadata 激活专线）、`ignore_risk_cooldown=True`
    的显式请求按现语义不受限；由 `RequestConf` 新增 `skip_throttle: bool` 供个别调用点关闭。
  - 位置理由：在重试循环外（不叠加退避）、在选代理前（不占在途/QPS）。
- 配置放 `ProxyHealthConfig` 或新建 `CrawlerThrottleConfig`：
  `business_throttle_enabled`（默认 True）、`business_throttle_min_s` / `max_s`（默认 0.1~0.5s）、
  `skip_proxy_paths`（可选）。挂到 `CONFIG` 字段 / 实例属性。
- 任务级节奏（可选，低风险）：`scheduler_launcher.py:312` 的 `await self.func()` 前
  用 `SleepTimeGenerator.get_wait_time()` 插入任务前置等待，不碰 `save_last_exec_time` 的语义。
  默认关闭，避免拖慢现有日级补跑。

### 4.5 头序与 H2 回归基线：`test/`

- 新增 `test/test_anti_risk_transport_baseline.py`：
  - 断言 `UserAgentParser(...).get_headers_dict()` 的 `list(keys)` 等于 §4.2 的字典序；
  - 断言 gRPC `make_metadata()` 的业务头名序列 == 真机抓包 22/22 的序列
    （从 `grpc_headers.jsonl` 读取，base64 key 解码后比较）；
    若因 region 头插入位置导致不一致，则**同时**调整 `makeMetaData.py:241` 的追加位置使之对齐。
  - 断言 `WEB_IMPERSONATE_TARGETS` 全部是 Chrome 桌面系；
  - 断言节流工具在 `skip_throttle` / `local_exit_only` 下返回 0 等待。
- 明确不测试 H2 SETTINGS（无 API、无证据），在测试 docstring 写明原因。

## 5. 验证方式

1. `uv run python -m pytest test/test_web_bapi_headers.py test/test_anti_risk_transport_baseline.py
   test/test_push_and_cookie_hardening.py test/test_proxy_retry_yield.py -q`
2. 本地回显服务器实测：随机 20 次取 target，断言 UA 版本与 `sec-ch-ua` 版本一致。
3. Redis 持久化：起一个临时 key 写入 → 模拟进程重启（新建实例）→ 读回 `CookieWrapper` 字段一致。
4. 节流：mock `retry_sleep`，确认 `local_exit_only` 与 `skip_throttle` 时不等待。
5. 改的是 crawler 侧采集/链路代码 → 重启 `be-bilibili-crawler`，验证 `/health` 200、
   日志无 ERROR/Traceback、容器内导入新模块。

## 6. 风险与回滚

- TLS target 收窄会降低「指纹多样性」，但换来与 UA 的一致性；若线上 -352 反而升高，
  用配置开关切回全随机（保留 `SUPPORTED_IMPERSONATE_TARGETS` 原变量不动）。
- Cookie Redis 化默认开启；关闭 `BILI_COOKIE__PERSIST_TO_REDIS=false` 即回到原内存池。
  注意 Redis 中的 cookie 与出口 IP 绑定关系：换出口后旧 cookie 可能失效，靠 `note_352` + TTL 自然淘汰。
- 节流默认只加轻微随机（0.1~0.5s）；`local_exit_only` 豁免保证 cookie 激活不被拖慢。
  若影响吞吐，调小或关闭 `BUSINESS_THROTTLE_ENABLED`。
- 头序改动不改 wire 顺序（curl_cffi 自行重排），无线上行为风险；
  gRPC metadata 顺序调整若引起异常，单独回退 `makeMetaData.py` 的 region 插入位置。
- gaia/WASM 本次**无代码改动**，风险为零；后续拿到真机样本再做独立计划。
