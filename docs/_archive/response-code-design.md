# 统一响应码与异常处理设计规范

> 适用范围：所有后端服务（be-message-service、RPA-Browser 等）经由 `bili-common` 对外暴露 HTTP 接口的统一响应契约。

## 1. 核心约定

- **对外 HTTP 状态码恒为 `200`**，业务状态一律通过响应体 `body.code` 表达。
- 响应体统一结构（见 `bili_common.models.response`）：

  ```json
  { "code": 0, "msg": "ok", "data": {} }
  ```

  - `code`：`int`，业务码（0 成功，非 0 为各类业务失败）。
  - `msg`：`string`，人类可读提示。
  - `data`：业务数据或 `null`。

- 前端（含 `localhost:5173` 开发代理）**只依据 `body.code` 判断业务成败**，不依赖 HTTP 状态码。

## 2. 未登录（重点）

未登录场景（缺少或非法 `x-bili-mid` 请求头等）采用 **B 站官方约定业务码 `-101`**：

```json
{ "code": -101, "msg": "未登录，请提供有效的x-bili-mid请求头", "data": null }
```

- HTTP 状态码：**200**（不是 401）。
- 业务码：**-101**（不是 401，也不是旧的 -1）。

> 历史实现曾返回 `{"code":401,"msg":...,"data":null}` 且 HTTP 401，
> 这与「Http 恒 200、业务码在 body」的契约冲突，会导致前端误判为网络/网关错误。
> 现统一收敛到 `bili-common` 的 `NotLoggedInException` 修复此问题。

## 3. 公共业务码（`bili-common.models.response_code.ResponseCode`）

所有公共业务码集中在 `bili-common` 单一来源，禁止各后端自行硬编码：

| 常量 | 值 | 说明 | HTTP 状态 |
| --- | --- | --- | --- |
| `SUCCESS` | `0` | 成功 | 200 |
| `NOT_LOGGED_IN` | `-101` | 未登录（官方约定） | 200 |
| `INVALID_PARAM` | `400` | 参数错误 / 校验失败 | 200 |
| `UNAUTHORIZED` | `401` | 未授权（仅作为业务码语义，不直接作为 HTTP 状态） | 200 |
| `FORBIDDEN` | `403` | 无权限 | 200 |
| `NOT_FOUND` | `404` | 资源不存在 | 200 |
| `INTERNAL_ERROR` | `500` | 服务器内部错误 | 200 |

> 说明：即便语义上对应 HTTP 4xx/5xx，对外 HTTP 状态始终为 `200`，业务码落到 `body.code`。
> 404 在 RPA-Browser 中仍保留「未找到资源」语义，但同样以 `{code:404,...}` 返回 HTTP 200。

## 4. 异常实现（`bili-common.exceptions`）

- **`BaseException`（业务异常基类）**：携带 `code` / `msg` / `data` / `status_code`(默认 200)，
  经全局异常处理器统一输出 `{code, msg, data}` 且 HTTP 200。
  - `NotLoggedInException`：预设 `code = NOT_LOGGED_IN = -101`，`msg = "未登录，请提供有效的x-bili-mid请求头"`，`status_code = 200`。
- **HTTP 辅助异常**（需带 HTTP 语义时）：`BiliException` / `InvalidUIDException` / `InvalidMidFormatException` / `ResourceConflictException`，均继承 FastAPI `HTTPException` 并附带 `code`，由统一处理器归一化为 HTTP 200 + body。
- **统一注册**：
  - `register_exception_handlers(app)`：一键注册业务异常 + `StarletteHTTPException` + `RequestValidationError` 处理器（供以 bili-common 为唯一异常来源的后端，如 be-message-service）。
  - `register_business_exception_handlers(app)`：仅注册业务异常处理器（供已自行处理 HTTP/校验异常的后端，如 RPA-Browser），避免覆盖既有 handler。

### 各后端接入方式

```python
# be-message-service（以 bili_common 为唯一异常来源）
from bili_common.exceptions import register_exception_handlers
register_exception_handlers(app)

# RPA-Browser（已有本地 HTTP/校验 handler，仅接入业务异常）
from bili_common.exceptions import register_business_exception_handlers
register_business_exception_handlers(app)
```

## 5. 编码规范（避免重复踩坑）

1. 未登录、无权限、参数错误等**一律走业务异常 / 统一响应**，HTTP 状态码恒 200。
2. 公共业务码必须来自 `bili-common.models.response_code`，**禁止在业务代码中硬编码 `-101` / `401` 等字面量**。
3. 新增公共业务码时，先在 `bili-common` 的 `ResponseCode` 中登记，再在需要时派生对应的 `BaseException` 子类。
4. 认证相关异常统一使用 `bili_common.exceptions.NotLoggedInException`，各后端不得再自定义未登录异常。
