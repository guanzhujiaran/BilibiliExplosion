# be-bilibili-crawler 云端 LLM 配置持久化计划书

> 目标：把「通过接口 / 管理页保存的云端 LLM 列表」落成本地 JSON 文件，使
> **保存后重启仍然生效**；同时保留「不可恢复错误自动摘除不落盘」的防误删兜底。
>
> 状态：**实施中**（2026-11-08）
> 前序计划书（本文显式修订其冲突条款）：
> - `docs/be-bilibili-crawler-LLM不可用状态机计划书.md`
> - `docs/be-bilibili-crawler-LLM槽位并行计划书.md`（无冲突，仅参考）
>
> 关联代码：
> - `CONFIG.py`：`LLMApiConfig` / `settings.llm_apis`
> - `Service/llm_service/pool.py`：`set_llm_apis()`（人工写操作唯一收敛点）、
>   `remove_llm_by_fingerprint()`（状态机自动摘除路径）、`get_llm_configs()` / `get_llm_stats()`
> - `controller/common/CommonRouter.py`：内部接口 `GET/POST/PUT/PATCH/DELETE /llm/config*`
> - `Utils/推送/push_switch.py`：**可复用的本地 JSON 持久化范式**（RUNTIME_DIR + mkstemp + os.replace）
> - `be-message-service/app/services/admin/crawler_llm.py`：管理端代理（本次不改）

---

## 0. 对前序计划书的冲突修订（必须先读）

前序计划书 `be-bilibili-crawler-LLM不可用状态机计划书.md` 有两处表述与本次需求**直接冲突**，
自本文起作废，改为下面的口径：

| 位置 | 原文（已作废） | 现口径 |
|---|---|---|
| 第 199-200 行「明确不做」 | 「不做已删除指纹的持久化黑名单：配置的唯一事实来源是环境变量 / `POST /llm/config`，服务重启后从配置恢复是预期行为」 | 仍然**不做**「已删除指纹」的持久化黑名单；但**人工显式保存的整份列表**要持久化。配置事实来源变为「**runtime 文件 > `.env`**」，`.env` 降级为初始种子 / 兜底 |
| 第 237 行 风险表「误删配置」 | 「删除只影响运行时内存，不写回环境变量；重启即恢复」 | 不变（这条**仍然成立**，且是刻意保留的安全兜底）：`REMOVED` 自动摘除**不落盘**，重启后该槽位从 `runtime` 文件 / `.env` 原样回来 |

需要分清的三个概念：

| 概念 | 触发者 | 是否落盘 | 重启后 |
|---|---|---|---|
| **人工保存的列表**（本文新增持久化对象） | 运维通过 `PUT /llm/config`（内部接口或管理页）**显式保存整体列表** | ✅ 写 `runtime/llm_apis.json` | 从文件恢复，生效 |
| **自动摘除**（`REMOVED`，状态机判定 401/404/410 等不可恢复错误） | `remove_llm_by_fingerprint()` | ❌ 只改运行时内存 | 恢复到「文件 / `.env` 里仍在的那一条」，由状态机重新判定 |
| `.env` 的 `llm_apis` | 部署配置 | 不写（**永不回写**） | 文件不存在时作为配置来源 |

因此：**持久化的是「人工显式保存的列表」，不是「自动摘除的黑名单」。**
「上游抖动误报 401 → 重启即自愈」的防误删兜底必须保留，不能被持久化削弱。
运维要真正删掉一条坏配置，正确做法是**在列表里删掉它并保存一次**（即人工操作落盘），
而不是指望状态机自动摘除。

---

## 1. 现状

| # | 事实 | 位置 |
|---|---|---|
| 1 | 配置来自根 `.env` 的 `llm_apis` JSON；启动时进 `settings.llm_apis` | `CONFIG.py:130` / `:239` |
| 2 | 所有人工写操作（6 个内部 CRUD + 管理端 `PUT /llm/config`）最终都调 `set_llm_apis()` | `Service/llm_service/pool.py:360` |
| 3 | `set_llm_apis()` 只改内存 + 重建实例池，失败回滚；**不写回 `.env`，重启即丢失** | 同上 |
| 4 | 状态机判 `PERMANENT` 后自动摘除配置，**绕开 `set_llm_apis`**，只改内存 | `pool.py:183` |
| 5 | 内部接口 `GET/POST/PUT/PATCH/DELETE /llm/config*` 无鉴权、网关不转发 | `CommonRouter.py:92-169` |
| 6 | 管理端 `PUT /api/v1/crawler/admin/llm/config` 代理到 crawler 的 `PUT /llm/config`，客户端不缓存 | `be-message-service/.../crawler_llm.py` |
| 7 | 已有本地 JSON 持久化范式（`mkstemp` + `os.replace` + `RUNTIME_DIR` + 读取失败回退） | `Utils/推送/push_switch.py` |
| 8 | `RUNTIME_DIR` 在 dev / prod 均已挂载到宿主机 `docker_vol/fastapi/runtime*`，且 `docker_vol/*` 在 `.gitignore` 内 | compose / `.gitignore` |

痛点：管理页保存一次 → 进程重启（发版 / 容器重启 / OOM）后配置回退到 `.env`，
运维的修正被静默丢弃；为了让修正生效只能去改宿主机 `.env` 再重启（容器改宿主机文件不可靠，也不留审计）。

---

## 2. 介质选型结论

**只用本地 JSON 文件；禁止引入 MySQL / Redis / 任何 DB 表或 alembic 迁移。**

理由：

1. 读写形态是「**整体覆盖式写**（PUT 全量列表）+ **启动时一次性读**」；
2. 没有按条件查询、分页、多字段更新，条目只有个位数；
3. 写频率是「运维偶尔在管理页点一次保存」；
4. 引入 DB 只会额外带来迁移、连接池、密钥入库、双容器 schema 同步等成本，收益为零。

文件用 `mkstemp` + `os.replace` 原子整体覆盖即可（读者永远看到旧的或新的完整文件，
不会读到半截 JSON），并发只有单进程内的 `set_llm_apis`，不需要事务。

---

## 3. 设计

### 3.1 新增模块 `Service/llm_service/config_store.py`

- 文件路径：`RUNTIME_DIR/llm_apis.json`；`RUNTIME_DIR` 为空时回退项目根 `runtime/`（与 `push_switch` 一致）。
- 文件结构（字段与 `LLMApiConfig` 完全一致，便于 `model_validate` 校验）：

```json
{
  "version": 1,
  "updated_at": 1793860644,
  "items": [
    {"base_url": "https://...", "model_name": "...", "token": "...", "requests_per_second": 0.5}
  ]
}
```

- `version`：整数，当前固定 `1`；读到更高版本 / 非法结构一律当「文件不可用」处理（回退 `.env`），
  保证降级部署不会拿新格式乱跑。
- `updated_at`：**秒级 int**（遵守 `unix-timestamp` 规则，不写 ISO 字符串）。
- 原子写：`mkstemp` → 写入 → `os.chmod(0o600)` → `os.replace`；异常时删除临时文件。
  权限 `0600`（文件含明文 token，比 `push_switch` 的 `0644` 更严）。
- 读失败 / JSON 损坏 / 校验不通过：打 `warning`（**不含 token**）并返回「不可用」，
  **绝不因为坏文件导致服务起不来**。
- `token` 严禁出现在日志、接口响应、提交物里：模块内所有日志只打条数 / 路径 / 模型名。

对外函数：

| 函数 | 作用 |
|---|---|
| `config_file_path() -> Path` | 持久化文件绝对路径 |
| `load_persisted() -> LLMApiConfigFile \| None` | 读取并校验；不可用返回 `None`（含 warning） |
| `save_persisted(apis) -> Path` | 原子整体覆盖写，返回文件路径 |
| `delete_persisted() -> bool` | 删除文件（不存在返回 `False`） |
| `apply_to_settings() -> str` | 文件合法时整体覆盖 `settings.llm_apis`，返回 `"file"` / `"env"`（空列表也是合法保存状态：运维显式清空后重启仍为空，不会从 `.env` 复活） |
| `current_source() -> str` | 当前生效来源（`file` / `env`），供日志与回退接口返回 |

`apply_to_settings()` 只**覆盖** `settings.llm_apis`，不重建实例池：
实例池在首次 `get_all_free_llms()` 时按 `_config_key()` 惰性构建，启动阶段无需预热，
也就不会在启动阶段联网 / 打印模型不可用噪音。

### 3.2 启动加载

- `Utils/FastAPI/FastapiLifespan.py`（crawler 角色，含 `SERVICE_ROLE=api` 分支之前）与
  `Utils/FastAPI/QueryFastapiLifespan.py`（query 角色）**都**调用 `apply_to_settings()`；
- 打一行来源日志（可观测「当前生效的是文件还是 `.env`」）：
  `LLM 配置来源: file（13 条）` / `LLM 配置来源: env（13 条）`；
- 文件不存在时**不创建、不改动**，继续用 `.env`（首次保存前系统行为与改造前完全一致）；
- 只有 crawler 容器会**写**（它的 `/llm/*` 是唯一写入口），query 容器只读同一个文件保持一致。

### 3.3 写路径（唯一收敛点）

`set_llm_apis()`：

```
校验 → 记录旧值 → settings.llm_apis = 新列表
     → _build_free_llms() 成功 → _free_llm_cache_key 更新
     → config_store.save_persisted(settings.llm_apis)   # 新增
     → 返回脱敏列表
   任一步异常 → settings.llm_apis / 实例池缓存回滚到旧值 → 重新抛出
```

落盘放在「实例池构建成功之后」：非法配置（缺 `base_url` / `model_name`）在建池前就被拒，
不会污染文件；落盘失败则回滚内存与池缓存，**不出现「内存已改、文件未改」的撕裂状态**。
因为 6 个内部 CRUD 与管理端 `PUT /llm/config` 全部经由它，控制器与 be-message 均无需改动。

### 3.4 自动摘除**不**落盘（刻意设计）

`remove_llm_by_fingerprint()` 保持只改运行时内存（`.env` 与 `llm_apis.json` 都不写）：

- 保留「上游误报 401/404 时重启即恢复」的防误删兜底；
- 状态机的 `REMOVED` 是**运行时观测结论**，不是运维意图，不能写成持久化事实
  （否则一次误报会把好 key 永久钉死，且再也无法从文件恢复）；
- 运维需要真正删除坏配置时：在列表里删掉并保存一次（正好走 3.3 的落盘路径）。

代码注释里必须写明这一点，避免后人「顺手」把删配置也落盘。

### 3.5 回退入口

新增内部接口 `DELETE /llm/config/override`：

1. 删除持久化文件（`delete_persisted()`）；
2. 热切回 `.env` 的当前配置：`settings.llm_apis = env_llm_apis`（启动时从 `.env` 读到的快照）
   → 重建实例池；
3. 返回 `{"source": "env", "configs": [...]}`（`configs` 为脱敏列表）。

- **不改** `GET/PUT /llm/config` 的响应结构（避免联动 be-message 的 schema）；
- 路由常量加到 `ApiRoutes/__init__.py`（`RouterPaths.LLM_CONFIG_OVERRIDE` / `RouterNames.DELETE_LLM_CONFIG_OVERRIDE`）；
- 前端管理页本次不改。

### 3.6 单实例连通性测试（2026-11-08 追加，2026-11-11 修订探测方式）

管理页需要「点一下就知道这条实例现在还能不能用」，而状态列只能反映**最近一次业务调用**的结果，
新建 / 刚改过密钥的实例根本没统计（`state` 缺省），所以必须有一个**主动探测**入口。

新增内部接口 `POST /llm/config/test`（crawler，无鉴权，同其它 `/llm/*`）：

```json
// 请求：index 用于「沿用原密钥」，可空（新增行）
{"index": 7, "base_url": "https://...", "model_name": "...", "token": ""}
```

2026-11-11 修订：**放弃 `httpx` 裸打 `/chat/completions` + `max_tokens=1` 的最小 completion**，
改为**用裸 `langchain_openai.ChatOpenAI` 真发一次提问 `1+1=?`**，拿到模型回复才算通。
原因：最小 completion 只证明「HTTP 层 2xx」，测不到生产真正走的 SDK 链路
（`base_url` 拼接、鉴权头、请求参数、响应解析、SDK 版本兼容）；运维看到「测试成功」
却在业务调用里报错，诊断价值为零。与生产同链路但**用裸类**，二者不冲突。

- `token` 为空或含 `****` 时，按 `index` 从 `settings.llm_apis` 取原密钥（越界 / 无密钥 → `ok=false`，
  `error="未提供密钥"`，**不发请求**）；
- 探测方式：`ChatOpenAI(model=..., base_url=..., api_key=SecretStr(token), timeout=..., max_retries=0)`
  后 `await ainvoke("1+1=?")`；不设 `max_tokens`（各厂商对新版 `max_completion_tokens` 支持不一，
  简单问题本身输出很短）；`max_retries=0` 保证「一次探测 = 一次上游请求」，
  超时沿用 `llm_test_timeout`（默认 45s）；
- **只用裸 `ChatOpenAI`，不碰实例池里的 `TrackedChatOpenAI`**：池实例带限流器与统计埋点，
  借用会污染统计口径，且限流排队会把「测试」拖成几十秒；
- 响应结构**保持不变**：`{ok, base_url, model_name, status_code, latency_ms, error}`
  （成功时 SDK 不回传 HTTP 状态，记 `200`；失败时取 `openai.APIStatusError.status_code`；
  crawler 侧 `status_code` / `latency_ms` 是 int，be-message 代理层转成字符串；
  错误文案先抹掉密钥再截断 200 字符）；
- 模型回复**只写 info 日志（截断 100 字符），不进响应**：避免变更响应 schema 牵动
  be-message 代理层与前端 hey-api SDK 重新生成；
- be-message 代理这条用**独立超时** `crawler_llm_test_timeout`（默认 60s），
  必须大于 crawler 的 `llm_test_timeout`（默认 45s），否则慢模型会被代理层提前掐断；
- **不写任何状态**：探测不参与健康状态机、不改统计、不落盘 —— 它只是一次诊断，
  避免「测一下就影响冷却 / 摘除」；
- 失败归一化：SDK 抛出的 `APIStatusError` / `APITimeoutError` / `APIConnectionError`
  及其它异常统一转成 `ok=false` + 可读文案（超时单独提示「请求超时」），日志不带 token。

前端（be-message 代理 + 管理页）：

- be-message 新增 `POST /api/v1/crawler/admin/llm/config/test`（`AdminUser`），
  代理上述接口并把结果原样转成字符串字段；
- 管理页把表格改成**卡片网格**（一条实例一张卡，字段竖排+状态/统计/测试结果同卡展示），
  每张卡一个「测试」按钮，结果就地显示（成功→耗时；失败→状态码 + 错误摘要）。

### 3.7 观测「当前生效来源」

- 启动日志一行：`LLM 配置来源: file/env（N 条）`；其中 `file`（本地文件覆盖了 `.env`）
  用 **WARNING** 级 —— 默认 `LOG_LEVEL=WARNING` 下也要能在日志里看到这条事实，
  `env` 用 INFO；
- 回退接口返回带 `source` 字段；
- 保存成功日志：`LLM 配置已保存到 <path>: N 条`（**不打 token**）。

---

## 4. 改动清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `Service/llm_service/config_store.py` | **新增**：持久化模型 + 原子读写 + 回退 + 来源 |
| 2 | `Service/llm_service/pool.py` | `set_llm_apis()` 成功后落盘、失败回滚；新增 `restore_llm_apis_from_env()`（回退入口用）；`remove_llm_by_fingerprint()` / `_remove_slot_from_cache()` 注释明确「不落盘」 |
| 3 | `Service/llm_service/__init__.py` | 导出 `config_store` 相关函数与 `restore_llm_apis_from_env` |
| 4 | `Utils/FastAPI/FastapiLifespan.py` | 启动阶段 `apply_to_settings()` + 来源日志 |
| 5 | `Utils/FastAPI/QueryFastapiLifespan.py` | 同上（query 容器只读，不提供写接口） |
| 6 | `controller/common/CommonRouter.py` | 新增 `DELETE /llm/config/override`；`_LLM_CONFIG_DESC` 文案更新为「立即生效且保存到本地文件」 |
| 7 | `ApiRoutes/__init__.py` | 新增路径 / 名称常量 |
| 8 | `CONFIG.py` | `RUNTIME_DIR` 注释补充 `llm_apis.json` |
| 9 | `test/test_llm_config_store.py` | **新增**单测（见第 5 节） |
| 10 | `Service/llm_service/probe.py` | **新增**：单实例连通性探测（`LLMApiTestRequest` / `LLMProbeResult` / `probe_llm_api()` + 密钥回填）。2026-11-11 起探测体改为**裸 `ChatOpenAI.ainvoke("1+1=?")`**（`max_retries=0`，回复只进日志），响应结构不变 |
| 11 | `controller/common/CommonRouter.py` + `ApiRoutes/__init__.py` | 新增 `POST /llm/config/test`（声明在 `/llm/config/{index}` 之前） |
| 12 | `CONFIG.py` | 新增 `llm_test_timeout`（默认 45s） |
| 13 | `test/test_llm_probe.py` | **新增**单测：密钥回填、成功 / SDK 错误状态码 / 超时 / 连接错误 / 未提供密钥 / 不写状态。2026-11-11 起改用假 `ChatOpenAI` 注入（`monkeypatch`），不再 mock `httpx.AsyncClient` |

---

## 5. 验证

### 5.1 单测（`uv run python -m pytest test/test_llm_config_store.py -v`）

1. 写入 → 读回一致（顺序、字段、`requests_per_second`、`updated_at` 为 int）；
2. token 明文只存在文件里：`get_llm_configs()` 返回脱敏，日志不含 token；
3. 文件缺失 → `apply_to_settings()` 返回 `env` 且不改 `settings.llm_apis`；
4. 文件损坏（非 JSON / 字段非法 / `version` 过高）→ 回退 `env` 并有 warning，不抛异常；
5. 原子写：写入后目录里没有残留临时文件；文件权限 `0600`；
6. 落盘失败（`RUNTIME_DIR` 指向不可写路径 / monkeypatch `save_persisted` 抛错）→
   `set_llm_apis()` 回滚 `settings.llm_apis` 与实例池缓存，并抛出异常；
7. 自动摘除后文件不变（`remove_llm_by_fingerprint()` 前后文件内容一致）；
8. `DELETE /llm/config/override` 语义：删除文件后 `apply_to_settings()` 回到 `.env`。

现有 `test/test_llm_health_stats.py` 的统计 / 健康断言不得被破坏（全量跑一遍）。

### 5.2 实跑（重启 `be-bilibili-crawler` 后）

1. `PUT /llm/config` 保存改过的列表 → `GET /llm/config` 顺序与内容一致、token 脱敏；
2. `docker restart be-bilibili-crawler` → `GET /llm/config` 仍是保存后的列表（**核心验收点**）；
3. `GET /llm/stats` 正常返回、`docker logs` 无新异常；
4. `DELETE /llm/config/override` → 回到 `.env` 配置，再重启仍以 `.env` 为准；
5. 若管理端可用：`PUT /api/v1/crawler/admin/llm/config`（token 传脱敏值）保存后重启，配置同样保留。
6. 探测实跑（2026-11-11）：`POST /llm/config/test`（或管理端
   `POST /api/v1/crawler/admin/llm/config/test`）对一条真实实例点「测试」→ `ok=true` +
   `latency_ms`，且 crawler 日志出现 `LLM 探测成功 ... 回答=2`；
   故意传错误密钥 → `ok=false` 且错误文案不含密钥；
   `GET /llm/stats` 前后调用计数不变（证明真实调用没有污染统计）。

---

## 6. 风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| 文件含明文 token | `llm_apis.json` 里是明文密钥 | 权限 `0600`；目录在 `docker_vol/*`（`.gitignore` 忽略）；日志 / 接口一律脱敏、不回显 |
| 坏文件导致启动失败 | 手改文件留下半截 JSON | 读取异常一律 warning + 回退 `.env`，绝不让服务起不来 |
| 双容器配置漂移 | 只有 crawler 会写，query 只读 | 同一挂载文件（生产）/ 同一目录（dev）；query 容器读不到时回退 `.env`，且它不调用 LLM |
| 误以为自动摘除会持久 | 运维看到列表少了条目，重启又回来 | 计划书 3.4 + 代码注释 + 删除日志里写明「重启或重新配置可恢复」；文档要求人工删并保存 |
| 落盘失败掩盖内存已生效 | 内存改成功、文件写失败 | `set_llm_apis()` 统一回滚并抛异常（接口 500），不返回成功 |

---

## 7. 明确不做

- 不改 `.env` 的写法、**不把配置写回 `.env`**（容器改宿主机文件不可靠且无审计）；
- 不引入 MySQL / Redis / 任何数据库表、alembic 迁移或 ORM 模型，不把 token 存进数据库；
- 不做配置多实例同步协议（单写容器 + 共享挂载文件即可）；
- 不改 be-message 管理端页面与前端；探测响应结构保持不变，不新增字段、不触发前端 hey-api SDK 重新生成；
- 不把「自动摘除」做成持久化黑名单，不引入后台定时器；
- 不碰 RPA / 站点专属业务逻辑。
