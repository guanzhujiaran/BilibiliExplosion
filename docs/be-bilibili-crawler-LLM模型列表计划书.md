# be-bilibili-crawler 云端 LLM「获取模型列表」计划书

> 目标：管理端「LLM 配置」页不再只能手打模型名，可以从上游 `GET {base_url}/models`
> 拉取可选模型列表并勾选，同时保留手动输入（列表里没出现的模型也能填）。
>
> 状态：**实施中**（2026-11-11）
> 前序计划书（契约沿用，不冲突）：
> - `docs/be-bilibili-crawler-LLM配置持久化计划书.md`
> - `docs/frontend_requirements/be_crawler_llm_config.md`
>
> 关联代码：
> - `CONFIG.py`：`settings.llm_models_timeout`
> - `Service/llm_service/models.py`（新增）：`list_llm_models()` / `resolve_models_config()`
> - `Service/llm_service/probe.py`：抽出 `resolve_api_token()`（探测与模型列表共用密钥回填）
> - `controller/common/CommonRouter.py`：内部接口 `POST /llm/models`
> - `be-message-service/app/api/crawler_llm_admin.py`：管理端代理 `POST /api/v1/crawler/admin/llm/models`

---

## 1. 现状与痛点

| # | 事实 | 位置 |
|---|---|---|
| 1 | 管理页「模型名」是自由输入 `el-input`，无任何候选来源 | `CrawlerLlmConfigAdmin.vue` |
| 2 | 模型名填错只有点「测试」才知道（真实 completion 要等几秒到几十秒） | 同上 |
| 3 | crawler 已有 `base_url + token`，天然具备拉取上游 `/models` 的条件 | `CONFIG.py::LLMApiConfig` |
| 4 | crawler `/llm/*` 无鉴权、网关不转发，必须经 be-message 代理 | `CommonRouter.py` |
| 5 | 密钥读取态是脱敏值，前端拿不到明文 | `pool.py::_mask_token` |

痛点：不同厂商的模型 id 命名差异大（`deepseek-chat` / `qwen-max` / `gpt-4o-mini` …），
手打极易出错，且改 `base_url` 之后原来的模型名往往失效。

---

## 2. 设计结论

### 2.1 新增一个只读诊断接口（不碰状态）

`POST {crawler}/llm/models`：请求体 `{index?, base_url, model_name?, token}`，
用 `httpx` 直连 `GET {base_url}/models`（`Authorization: Bearer {token}`），
返回 `{ok, base_url, status_code, latency_ms, models[], error}`。

- **不走实例池、不走 `ChatOpenAI`**：只取元数据，不产生推理调用、不消耗 token；
- **不写任何状态**：不改统计、不参与健康状态机、不落盘（与「测试」同口径）；
- **`model_name` 不是必填**：「先拉列表再选模型」是主要使用路径，此时模型名还是空的；
- **密钥回填复用 `probe.resolve_api_token()`**：`token` 为空 / 含 `****` 时按 `index`
  从 `settings.llm_apis` 取明文，管理页永远不需要（也拿不到）明文密钥；
- **失败也是 HTTP 200 + `ok=false`**：上游 401 / 超时 / 响应不可解析都归一成一条可读文案，
  避免网关把慢地址掐成 504 让前端拿不到结论。

### 2.2 响应解析兼容三种形状

| 上游 | 形状 |
|---|---|
| OpenAI 兼容（DeepSeek / 通义 / vLLM / one-api …） | `{"data": [{"id": "..."}]}` |
| Ollama | `{"models": [{"name": "..."}]}` |
| 少数自建网关 | `["model-a", {"id": "model-b"}]` |

统一由 pydantic 校验（`_ModelEntry` / `_ModelsEnvelope` / `TypeAdapter`）后
取 `id`（其次 `name`），**去重 + 升序**返回。

### 2.3 超时分两层

| 层 | 配置 | 默认 |
|---|---|---|
| crawler → 上游 | `settings.llm_models_timeout` | 20s |
| be-message → crawler | `settings.crawler_llm_models_timeout` | 30s |

本层必须大于下游，否则前端只会看到「crawler 不可达」，拿不到上游的真实原因。
网关 `ProxyEndPort.js` 已对 `/api/v1/crawler/admin/llm` 整段命名空间放宽到 90s，无需改动。

---

## 3. 接口契约

### 3.1 crawler 内部接口

```
POST /llm/models
{
  "index": 0,                         // 可空；token 为空/脱敏时用它回填原密钥
  "base_url": "https://api.example.com/v1",
  "model_name": "deepseek-chat",      // 可空，仅用于「索引与配置是否匹配」校验
  "token": ""                         // 空串 / 含 **** = 沿用该 index 的原密钥
}
→
{
  "ok": true,
  "base_url": "https://api.example.com/v1",
  "status_code": 200,
  "latency_ms": 812,
  "models": ["deepseek-chat", "deepseek-reasoner"],
  "error": null
}
```

### 3.2 管理端代理接口

```
POST /api/v1/crawler/admin/llm/models      // AdminUser 鉴权
同上请求体；数值一律字符串（status_code / latency_ms）
→ StandardResponse{code, msg, data: CrawlerLlmModelsResp}
```

后端分层：

- `be-message/app/models/schemas/crawler_llm.py`：`CrawlerLlmModelsReq` / `CrawlerLlmModelsResp`
- `be-message/app/services/infrastructure/crawler_llm.py`：`CrawlerLlmClient.list_models()`
- `be-message/app/services/admin/crawler_llm.py`：`CrawlerLlmService.list_models()`
- `be-message/app/api/crawler_llm_admin.py`：路由 + 审计日志

---

## 4. 前端交互（详见 `docs/frontend_requirements/be_crawler_llm_config.md`）

一张卡片仍然对应**一条实例配置**（`base_url + model_name + token + rps`），
避免「一行多模型 → 保存后拆行 → 密钥按 index 回填错位」的隐患。

1. 「模型名」由 `el-input` 改为 `el-select`：
   `filterable` + `allow-create` + `default-first-option` + `clearable`，
   既能从候选里勾选，也能直接输入未列出的模型名（手动输入）；
2. 字段旁新增「获取模型」按钮：用当前卡片的 `base_url + token` 拉列表，
   结果写入该卡片的候选缓存；拉取失败就地显示原因；
3. 地址 / 密钥变更后清空该卡片的候选缓存（避免展示别的厂商的模型）；
4. 未填密钥时按钮禁用并提示（新卡片必须先填密钥）。

---

## 5. 验证方式

1. 静态：`uv run python -c "import main"`（crawler）/ be-message 导入；
2. 单元：`uv run python -m pytest test/test_llm_probe.py -v` 不回归；
3. 联调：`docker compose -f docker-compose.dev.yml restart be-bilibili-crawler`，
   然后 `curl -X POST http://localhost:23333/llm/models -H 'Content-Type: application/json'
   -d '{"index":0,"base_url":"...","model_name":"...","token":""}'`
   观察 `ok / models / error`；
4. 前端：管理页点「获取模型」→ 下拉出现候选 → 勾选 → 保存 → 重新读取后配置正确。

### 5.1 实测记录（2026-11-11）

| 环节 | 结果 |
|---|---|
| crawler `POST /llm/models`（NVIDIA 地址，index=0 回填密钥） | `ok=true`、84 个模型、188ms |
| crawler 错误分支 | 无密钥 → `该实例没有可用密钥（请先填写密钥再获取模型列表）`；index=99 → `索引越界：当前共 11 条配置…` |
| be-message `POST /api/v1/crawler/admin/llm/models`（root 身份） | `code=0`、`ok=true`、84 个模型、123ms |
| `pytest test_llm_config_store.py test_llm_probe.py` | 40 passed（含新增 `test_empty_token_falls_back_to_same_source_key`） |
| 前端 `npm run type-check` / `npx vitest run tests/unit/llmConfigPayload.spec.ts` | 改动文件无类型错误；8 passed |
| 前端实跑（headless chromium + 真实 root 登录态） | 11 张卡片渲染；点「获取模型」→「已获取 84 个模型，可直接勾选」；卡片多选后标题变「… 等 2 个模型」、顶部提示「有未保存的修改」（未点保存，未改动线上配置） |
