---
kind: error_handling
name: 统一业务异常与响应码体系（bili-common 全局异常处理器）
category: error_handling
scope:
    - '**'
source_files:
    - bili-common/bili_common/exceptions.py
    - bili-common/bili_common/models/response_code.py
    - bili-common/bili_common/models/response.py
    - docs/_archive/response-code-design.md
    - RPA-Browser/app/exceptions/handlers.py
    - RPA-Browser/app/models/common/exceptions/base_exception.py
    - RPA-Browser/app/routes.py
    - be-message-service/app/exceptions.py
---

## 1. 采用的系统/方案

仓库采用基于 FastAPI 的「统一业务异常 + 统一响应码」模式，核心由公共包 bili-common 提供：
- 所有后端服务（be-message-service、RPA-Browser、be-bilibili-crawler 等）对外 HTTP 接口遵循同一契约：HTTP 状态码恒为 200，业务成败通过响应体 body.code 表达。
- 认证失败（未登录）使用 B 站官方约定业务码 -101，而非 HTTP 401。
- 通过 register_exception_handlers(app) / register_business_exception_handlers(app) 在应用启动时注册全局异常处理器，将各类异常归一化为 {code, msg, data} 的 JSON 响应。

该设计在 docs/_archive/response-code-design.md 中作为跨服务规范文档明确声明，并由 bili_common.exceptions 实现。

## 2. 关键文件与职责

- bili-common/bili_common/exceptions.py：定义统一业务异常基类 BaseException、HTTP 辅助异常 BiliException、预置异常（NotLoggedInException、InvalidUIDException、ResourceConflictException 等），并提供 register_exception_handlers / register_business_exception_handlers 两个注册函数。
- bili-common/bili_common/models/response_code.py：集中定义所有后端共享的业务码枚举 ResponseCode（SUCCESS=0、NOT_LOGGED_IN=-101、INVALID_PARAM=400、INTERNAL_ERROR=500 及大量自定义业务码）。
- bili-common/bili_common/models/response.py：定义统一响应模型 StandardResponse(code, msg, data) 及 success_response / error_response / custom_response 构造器。
- docs/_archive/response-code-design.md：规范文档，声明「HTTP 恒 200、业务码在 body、未登录用 -101、禁止硬编码业务码」等强制约定。
- RPA-Browser/app/exceptions/handlers.py：RPA-Browser 本地异常处理器：覆盖 HTTP/校验/自定义业务/全局兜底，并额外处理数据库连接丢失（返回 503 + SERVICE_UNAVAILABLE）。
- RPA-Browser/app/models/common/exceptions/base_exception.py：RPA-Browser 领域异常集合（浏览器/指纹/WebRTC/插件相关），继承本地 BaseException，注释明确「未登录已收敛到 bili_common.NotLoggedInException」。
- be-message-service/app/exceptions.py：消息服务领域异常（如 CommentNotInteractiveException），继承 bili-common 的 BiliException，由全局处理器统一归一化。
- RPA-Browser/app/routes.py：调用 register_business_exception_handlers(app) 接入 bili-common 业务异常处理器。

## 3. 架构与约定

### 三层异常体系

1. 公共业务异常（bili_common.exceptions.BaseException）：默认 status_code=200，to_response() 输出 {code, msg, data}，msg 经 i18n _() 延迟翻译。
2. HTTP 语义异常（bili_common.exceptions.BiliException 及其子类）：继承 FastAPI HTTPException，携带 code 属性，供网关/监控按 HTTP 语义识别；处理器将其包装为 {code, msg, data}。
3. 各服务领域异常：如 RPA-Browser 的 BrowserFingerprintNotFoundException、WebRTCStreamNotActiveException，以及 be-message-service 的 CommentNotInteractiveException，均通过 code + msg 描述业务错误。

### 全局异常处理器策略

register_exception_handlers 注册四类处理器：
- BaseException：_business_exception_handler → HTTP 200，直接返回 exc.to_response()
- StarletteHTTPException：_http_exception_handler → 原 status_code（≥500 才保留），取 exc.detail 或 exc.code 填充 body，404 仅 warning 日志
- RequestValidationError：_validation_exception_handler → HTTP 400，返回 {code: INVALID_PARAM, msg, data: exc.errors()}
- Exception（兜底）：_unhandled_exception_handler → HTTP 500，生成 error_id，DEV 环境附带 traceback，生产环境仅返回 error_id

RPA-Browser 在此基础上扩展了数据库连接丢失检测（DisconnectionError / OperationalError 含 Lost connection / MySQL server has gone away → 503 + SERVICE_UNAVAILABLE）。

### 响应体统一结构

所有成功/失败响应均为 StandardResponse：{"code": 0, "msg": "ok", "data": null}。前端（Vue3FrontEndDemoExercise）只依据 body.code 判断成败，不依赖 HTTP 状态码。

### 接入方式

- be-message-service：以 bili-common 为唯一异常来源，调用 register_exception_handlers(app)。
- RPA-Browser：已有本地 HTTP/校验处理器，仅调用 register_business_exception_handlers(app) 接入业务异常，避免覆盖既有 handler。

## 4. 约定与约束

以下规则来自规范文档与代码实现，具有实际约束力：

1. HTTP 状态码恒为 200：除参数校验失败（400）和兜底未捕获异常（500）外，所有业务异常必须返回 HTTP 200，业务状态通过 body.code 表达。违反此约定会导致网关/监控误判为协议层错误。（来源：docs/_archive/response-code-design.md 第 7 行、exceptions.py 第 124-131 行注释）
2. 未登录必须使用 NotLoggedInException：业务码固定 -101，HTTP 200，禁止自行定义未登录异常或返回 HTTP 401。（来源：response-code-design.md 第 20-33 行、base_exception.py 第 28-29 行注释）
3. 业务码必须来自 ResponseCode 枚举：禁止在业务代码中硬编码 -101 / 401 等字面量。（来源：response-code-design.md 第 76-78 行）
4. 新增公共业务码需先在 ResponseCode 登记：再派生对应异常或使用 error_response。（来源：response-code-design.md 第 78 行）
5. 未捕获异常必须带 error_id：用于服务端日志与客户端响应的关联追踪；DEV 环境附带 traceback，生产环境仅暴露 error_id。（来源：exceptions.py 第 195-232 行）
6. i18n 支持：异常 msg 通过 _() 延迟翻译，确保按请求上下文语言返回。（来源：exceptions.py 第 61 行、_http_exception_handler 第 163 行）
7. 数据库连接丢失特殊处理：RPA-Browser 将 Lost connection / MySQL server has gone away 识别为 503 + SERVICE_UNAVAILABLE，并建议客户端重试。（来源：RPA-Browser/app/exceptions/handlers.py 第 76-105 行）

## 5. 与其他模块的关系

- 前端（Vue3FrontEndDemoExercise）：消费统一 {code, msg, data} 响应，根据 code 分支处理（如 -101 跳转登录）。
- 网关（be-gateway）：转发下游 Python 服务的统一响应，无需感知 HTTP 状态码差异。
- RPC 层（bili-common/rpc）：通过 rpc_safe 装饰器将 ResourceConflictException 等业务异常还原为统一业务码，保持 RPC 与 HTTP 边界一致。
- 日志系统：所有异常路径均通过 loguru 记录，包含 method、path、traceback（DEV）、error_id，便于跨服务排查。