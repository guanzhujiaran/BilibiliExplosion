# 管理端「RPC 调试」页

> 后端已就绪：`be-message-service` `/api/v1/message/admin/rpc-debug/*`（仅 root，见
> `docs/be-message-统一计划书.md` §5.22）。
>
> ⚠️ **接前必做**：`npx @hey-api/openapi-ts` 重新生成 SDK（后端新增了 2 个接口），生成后再开发本页。

## 背景

RPC 走 RabbitMQ，此前没有可视化调用入口：

- FastStream `/asyncapi` 文档页的「Try it out」对本服务**必然 404**
  （`{"details": "xxx destination not found."}`）：它默认走内存 TestRabbitBroker 且只按
  默认 exchange 匹配订阅者，而我们的队列全部绑定在自定义 `message_exchange` 上；
  勾选 `sendToRealBroker` 也只是单向 `publish`（不等待回包），测不出 RPC 返回值。
- RabbitMQ 管理台虽可测通（自建回包队列 + 手填 `reply_to`），但每次要手填路由键与属性，太繁琐。

## 页面形态（管理端 → 新增「RPC 调试」菜单项）

```
┌────────────────────────────────────────────────────────────┐
│ 方法 [ resolve_ip_region                ▼ ]  服务 be-message │
│ 路由键 message.geoip.rpc.resolve_ip_region（只读展示）        │
│ ┌─ 参数表单（由 paramsSchema 渲染）────────────────────┐    │
│ │ ip        [ 114.114.114.114            ]            │    │
│ └──────────────────────────────────────────────────────┘    │
│ 超时 [ 5 ] 秒                          [ 发起调用 ]          │
│ ── 结果 ──────────────────────────────────────────────      │
│ 耗时 7ms                                                    │
│ reply: { "code": 0, "msg": "success",                       │
│          "data": { "region": "中国", "isp": "Zenlayer Inc"}} │
└────────────────────────────────────────────────────────────┘
```

- 顶部：方法下拉（按 `server` 分组 + 支持按 method_name 搜索），选中后展示只读 `routing_key`。
- 中部：**参数表单由 `params_schema_json` 动态渲染**（`JSON.parse` 后按 `properties` 生成输入框，
  `required` 标红），并提供「JSON 模式」切换（文本域直接编辑原始 JSON，便于复杂参数）。
- 底部：结果区展示 `duration_ms` + `reply` 完整信封（JSON 高亮、可折叠 / 复制）。
  **`reply.code != 0` 也要原样展示**（红色标识）——调试工具的价值就是把失败回显出来，
  不要把它当普通「接口报错」弹 toast 吞掉。

## 后端契约

### `GET /api/v1/message/admin/rpc-debug/methods`

列出全部可测试方法（root 专用，需带 `x-bili-mid` / `x-bili-role: root`）：

```json
{
  "code": 0,
  "msg": "success",
  "data": [
    {
      "method_name": "resolve_ip_region",
      "server": "be-message",
      "routing_key": "message.geoip.rpc.resolve_ip_region",
      "params_model": "ResolveIpRegionParams",
      "params_schema_json": "{\"properties\": {\"ip\": {...}}, \"required\": [\"ip\"], ...}"
    }
  ]
}
```

> 字段均为 **snake_case**（与既有管理端接口一致）；`params_schema_json` 是 JSON 字符串，前端需 `JSON.parse`。

### `POST /api/v1/message/admin/rpc-debug/invoke`

请求体（snake_case）：

```json
{ "method_name": "resolve_ip_region", "payload_json": "{\"ip\":\"114.114.114.114\"}", "timeout": 5 }
```

| 字段 | 说明 |
| --- | --- |
| `method_name` | `GET /methods` 返回的 `method_name` |
| `payload_json` | 参数的**原始 JSON 文本**（不同方法形态不同，由后端按契约严格校验） |
| `timeout` | 超时秒数，1~30，默认 5 |

响应（`code=0` 时 `data` 为一次调用结果）：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "method_name": "resolve_ip_region",
    "routing_key": "message.geoip.rpc.resolve_ip_region",
    "duration_ms": 7,
    "reply": { "code": 0, "msg": "success", "data": { "region": "中国", "isp": "Zenlayer Inc" } }
  }
}
```

错误语义（外层信封的 `code`）：

| 外层 code | 含义 | 前端处理 |
| --- | --- | --- |
| `400` | `payload_json` 不是合法 JSON / 不符合该方法的参数契约 | 表单标红 + 展示 `msg`（含具体字段原因），**不发请求** |
| `404` | 方法未登记 | 提示刷新方法列表 |
| `503` / `504` | RPC 未连接 / 超时 | 提示「服务端 RPC 不可用或超时」 |
| `500` | 其它异常 | 原样展示 `msg`（`类型: 详情`） |

> 注意：`reply.code` 是 **RPC 服务端**的业务结果（如 `get_user_card` 查无此人的 404），
> 与外层信封的 `code`（HTTP 调用本身是否成功）是两层，UI 上必须分开呈现。

## 验收清单

- [ ] 方法下拉展示全部 31 个契约方法，按 `server` 分组、可搜索；
- [ ] 选中方法后 `routing_key` 与参数表单随之切换；`resolve_ip_region` 填公网 IP 可看到属地/运营商；
- [ ] 参数不合法（类型错 / 缺必填）提交后展示 400 的 `msg` 详情，且不发 RPC；
- [ ] `reply.code != 0` 的结果以醒目样式展示完整信封（不吞错、不弹 toast 一闪而过）；
- [ ] 非 root 访问该页（或调用接口返回 403）时给出无权限提示。
