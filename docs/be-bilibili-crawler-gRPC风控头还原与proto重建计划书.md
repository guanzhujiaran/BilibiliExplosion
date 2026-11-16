# be-bilibili-crawler：gRPC 风控头还原（真机 evidence）与 proto 重建计划书

> 先有本计划书，再改代码。依据规则「新增或修改功能时先修改计划书」。
> 本次同时视为修复 `-352` 风控问题（bug 修复）。

## 1. 背景与证据

`BiliReverseEnginnering/` 里已完成 APK 9.19.0（`iBiliPlayer-bili.apk`）逆向与真机抓包：

- 静态还原：`docs/grpc_call_reconstruction.md` —— B 站 gRPC 走 `libignet.so`（gRPC C-core 1.66.2 + BoringSSL），Moss 拦截器链产出请求头。
- 真机抓包：`docs/grpc_capture_verification.md`、`work/capture/grpc_headers.jsonl` —— FIRERPA + mitmproxy 抓到 **22 次真实 gRPC 调用**，20 个 HTTP/2 头逐项记录；`work/capture/real_headers_sample.json` 是完整头样本。
- 复刻验证：`bili_grpc/` 客户端按 evidence 构造 12 个业务头，与真机 **12/12 完全一致**；`View` / `PlayViewUnite` 均 `bili-status-code=0`，裸头对照组 `PlayViewUnite` 返回 `-400`。

## 2. 现状（生产链路）

| 位置 | 作用 |
| --- | --- |
| `Utils/GrpcUtils/metadata/makeMetaData.py::make_metadata` | 统一 gRPC metadata 生成器 |
| `Utils/GrpcUtils/metadata/device_env.py` | 设备身份 / 三套 UA / locale / network / region |
| `Service/GrpcModule/Grpc/grpc_api.py` | `BiliGrpc` 主客户端、`grpc.aio.secure_channel` |
| `Service/GrpcModule/Grpc/GrpcProto/` | 138 个 `.proto` + 生成出的 `*_pb2.py` |
| `Service/GrpcModule/Grpc/GrpcProto/a.bash` | `python -m grpc_tools.protoc` 重建脚本 |
| `test/grpc_capture/` | 静态抓包解析测试与 `_proto_index.py` |

项目已实现大多数头（`x-bili-network-bin`、`x-bili-restriction-bin`、`ticket`、`region`、`locale timezone`、`fawkes session_id` 等），
但真机 evidence 暴露出以下**不一致**：

| # | 项 | 现状 | 真机实测 |
| --- | --- | --- | --- |
| 1 | `user-agent` | `device.ua`（`grpc-c++/1.66.2 Dalvik/... ignet_http/5.66.4 (bilibili-android-client/... grpc-c/43.0.0) ct/1`） | `grpc-c++/1.66.2 ` + **`device.ua_http`**（`Dalvik/... 9.19.0 os/android model/... channel/oppo ... network/2`） |
| 2 | `x-bili-trace-id` | **不发**（注释「抓包未发送」） | 22/22 都发，格式 `<32hex>:<后16hex>:0:0` |
| 3 | `grpc-timeout` | `8S` | `7990m` |
| 4 | `grpc-encoding` / 实际压缩 | metadata 写 `gzip`，但 channel `compression=NoCompression`（声明与实体不一致） | 请求体确实 gzip，`grpc-encoding: gzip` |
| 5 | 默认 `version_name` / `build` | `9.13.0` / `9130500` | APK `9.19.0` / `9190400` |
| 6 | `x-bili-network-bin` 的 `success_rate` | 随机 `0.95~0.99` | `NetQuality(success_rate=-1.0)`（未采样） |

## 3. 本次目标

1. 把 evidence 落到项目正式目录，并变成可执行回归测试。
2. 按 evidence 修正生产 gRPC metadata / channel（目标：减少 `-352`）。
3. 重新构建 proto stub（`a.bash`）与 `_proto_index.py`，保证测试包可用。
4. 验证：新 metadata 与真机头一一对应；公开接口直连返回 `bili-status-code=0`。

## 4. 改动清单（逐文件）

### 4.1 新增：evidence 目录（无业务代码风险）

- `be-bilibili-crawler/docs/grpc_reverse_evidence/README.md` —— 索引与证据说明
- `.../docs/grpc_reverse_evidence/*.md` —— 三份还原/抓包文档（从 `BiliReverseEnginnering/docs/` 复制）
- `.../docs/grpc_reverse_evidence/capture/` —— `grpc_headers.jsonl`、`real_headers_sample.json`
- `.../docs/grpc_reverse_evidence/tools/` —— 抓包/分析/身份导出脚本
- `test/grpc_capture/test_firerpa_headers.py` —— **新增回归测试**：用项目自己的 `bilibili.metadata.*_pb2` 解析真机 `-bin` 头，断言字段与项目 `make_metadata` 生成的头一致（头名集合、UA 形态、trace-id 正则、fawkes appkey/env、locale timezone、restriction 16、moss-engine-type）
- `test/grpc_capture/captures/FirerpaGuest/` —— 真机样本（头 JSON，供 `test_metadata_headers.py` 风格的校验复用）

### 4.2 修改：`Utils/GrpcUtils/metadata/makeMetaData.py`

- `user-agent` 改为 `f"grpc-c++/1.66.2 {device.ua_http}"`（真机形态）；`device.ua` 保留给其他场景，不删。
- 新增 `("x-bili-trace-id", device.gen_trace_id())`，使用 `device_env.gen_trace_id()`。
- `grpc-timeout` 改为 `7990m`。
- `x-bili-network-bin` 用 `success_rate=-1.0`（设备未采样），与真机一致。
- `version_name` / `build` 默认改为 `9.19.0` / `9190400`。
- 注释同步：删掉「抓包未发送 x-bili-trace-id」的错误结论。

### 4.3 修改：`Utils/GrpcUtils/metadata/device_env.py`

- 默认 `version_name` / `build` 对齐 `9.19.0` / `9190400`（`DeviceEnv` 与 `new_device_env` 两处）。
- 新增 `DeviceEnv.gen_trace_id()` 便捷方法（内部复用模块级 `gen_trace_id`，便于 `make_metadata` 调用）。
- `gen_ua()` 保持不动（三套 UA 各有用途），只在 `make_metadata` 里选对那套。

### 4.4 修改：`Service/GrpcModule/Grpc/grpc_api.py`

- `grpc.aio.secure_channel` 的 `compression` 由 `NoCompression` 改为 `Gzip`，
  使 metadata 中的 `grpc-encoding: gzip` 与实际请求体一致。
- 若实测出现 metadata 冲突，则回退为：从 `make_metadata` 移除手写 `grpc-encoding`，由库生成。
- 不改动代理 / 换设备 / 极验等既有风控逻辑。

### 4.5 重建：`Service/GrpcModule/Grpc/GrpcProto/`

- 执行 `bash Service/GrpcModule/Grpc/GrpcProto/a.bash`（先确认目录内没有手写 `.py`）。
- 重新生成 `test/grpc_capture/_proto_index.py`（按该目录 README 的脚本）。
- 不修改任何 `.proto` 定义本身（evidence 证明现有 proto 字段号正确）。

## 5. 验证方式

1. `uv run pytest test/grpc_capture -q`（含新增 `test_firerpa_headers.py`）。
2. 最小直连脚本：`make_metadata(access_key="")` → 打印头名集合，与真机 20 头比对（允许 gRPC 库自动头）。
3. `uv run python tools/grpc_probe.py`（如环境允许）或 `bili_grpc` 的 `check_player_unite.py` 复跑，确认 `bili-status-code=0`。
4. `git diff --stat` 检查 proto 重建产物只包含生成文件。

## 6. 风险与回滚

- `a.bash` 会 `find -name "*.py" -delete` 再生成；先确认无非生成 py，且重建后用 `git status` 核对。
- UA / trace-id / compression 变更会影响线上请求形态；改动集中在 `make_metadata` 一处，回滚只需还原该文件。
- 真机 JWT（`ticket` / `recent-region`）含设备凭据，只作为 evidence 样本留在项目内，不入代码默认值。
- 若 Gzip 导致既有调用异常，立即回退 4.4，保留 4.2 的头修正。

## 7. 追加变更：region 头恒带 + 忽略逆向工作区

用户确认后追加：

- `Utils/GrpcUtils/metadata/region_fallback.json`（新增）：只保存
  `x-bili-metadata-ip-region=CN`；**不再放跨设备共享的 recent JWT**。
- `device_env.py`：`DeviceEnv.ip_region` 默认 `CN`；`region_headers()` 回带本设备
  实际持有的 region（recent 只取 `self.recent_region`，过期失效）。
- `makeMetaData.py`：设备没有有效 recent 时按设备调 `fetch_region()` 领取，
  结果写在 `DeviceEnv` 上并随设备池持久化；领不到就记 warning 且本次不带该头。
  `BILI_RECENT_REGION` 仅作为单设备调试覆盖。
- `.gitignore`：追加 `BiliReverseEnginnering/`（原文件只有拼写不同的
  `BiliReverseEngineering/`，导致 APK/反编译产物显示为未跟踪）。
- 回归测试改为 `test_region_is_per_device`，断言代码里没有跨设备 JWT 兜底。

技术说明：`x-bili-ticket` 与 `recent-region` 都是**调用 B 站接口、由服务端签发**的
按设备凭证：`ticket` 走 `GetTicket` 接口（响应体），`recent-region` 走 `tab/v2`
接口（响应头）。客户端只负责按设备触发请求并回带，不本地签发。
（`gen_x_bili_ticket` 的 HMAC 只是 `GetTicket` 请求里的校验参数，不是最终 ticket。）
因此「按设备分开设置」的正确形态就是**按设备领取 + 随设备持久化 + 过期刷新**，
设备池（Redis）已提供持久化基础。

验证：两台设备的 JWT 独立（payload 的 `buvid` 各自不同）、`to_dict/from_dict` 持久化保持、
新设备首启只带 ip-region；已领取 region 的设备头集合 **20/20 与真机一致**；
`git check-ignore -v` 确认 `BiliReverseEnginnering/` 已被忽略。

## 8. 统一 ticket / region 的生命周期（追加）

按用户要求，两个凭证不再各搞一套：

- `makeMetaData.py` 新增 `ensure_credentials(device, device_info, md, proxy)`：
  ticket 缺失/过期 → 调 `GetTicket`；`GetTicket` 响应头已 `learn_region()`，
  因此**一次请求同时刷新两个凭证**；只有它没下发 region 时才回退 `tab/v2`。
- `DeviceEnv` 新增 `ticket` 字段与 `ticket_valid()`，与 `recent_region_valid()`
  共用 `is_expired(JWT exp)` 规则；两者都随设备池 `to_dict/from_dict` 持久化。
- `make_metadata` 里统一回带缓存凭证；缓存命中时不再重复请求 `GetTicket`
  （第二返回值仍兼容 `GetTicketResponse(ticket=...)`）。
- 回归测试新增 `test_ticket_and_region_share_one_lifecycle`。

验证：同一设备连续两次 `make_metadata` 只触发 1 次 `GetTicket`，两台设备各 1 次且
ticket 独立；`MetaDataBasicInfo.ticket` 与 header 一致；持久化后 ticket 仍属于原设备；
`uv run pytest test/grpc_capture -q` → **30 passed, 25 skipped**。

## 9. gRPC 工具链升级 + pb2 重编译（追加）

用户指出此前只重编译 pb2、没有升级工具链。本次同步升级：

- `pyproject.toml`：`grpcio 1.84.0 → 1.85.1`、`grpcio-tools 1.84.0 → 1.85.1`、
  `protobuf 7.36.1 → 7.36.2`（PyPI 当前最新；grpcio/grpcio-tools 必须同版本）。
- `requirements.txt`：旧声明（1.75.1 / 6.32.1）同步到同一组版本，消除两份声明漂移。
- `uv lock` 刷新锁文件后，用 `GrpcProto/a.bash` 按新 protoc 重新生成全部 pb2，
  再刷新 `test/grpc_capture/_proto_index.py`。
- 验证：生成文件的 `ValidateProtobufRuntimeVersion` 要求 7.35.1，runtime 7.36.2 满足；
  `uv run python -c "import grpc"` → 1.85.1；`uv run pytest test/grpc_capture -q`
  → **30 passed, 25 skipped**；真机头 + Gzip 直连 `View` 成功返回 **69 033 bytes**。
