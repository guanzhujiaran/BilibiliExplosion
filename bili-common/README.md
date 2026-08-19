# bili-common

BilibiliExplosion 后端各微服务共享的**公共依赖库**。把统一响应封装、鉴权、数据库/Redis 连接、浏览器实例、代理管理、消息推送等通用能力抽到一处，供 `be-bilibili-crawler`、`be-message-service`、`RPA-Browser` 以 uv 路径依赖方式直接引用，避免重复造轮子。

## 功能

- 统一响应模型与辅助函数（`ResponseModel` / `response_data` / `success_response` / `error_response`）
- FastAPI 依赖注入封装（缓存 / 分页 / 验证码 / IP·用户限流）
- JWT 鉴权依赖（`CurrentUser`）
- 异步 MySQL（SQLAlchemy 2.x）/ Redis 连接与依赖
- Playwright 无头 Chromium 浏览器管理（`BrowserManager`）
- 代理管理（`ProxyManager` / `ProxyRule`）
- 消息推送客户端（`MessageServiceClient`，对接 `be-message-service`）
- RPC 公共设施与契约（`bili_common.rpc`）：`rpc_safe` 装饰器、`RpcClient` 通用客户端、按系统分模块的 RPC 契约（抽奖 / pptr 用户 / 站外推送）
- 站外推送 MQ 公共发布函数（`bili_common.core.message_pub`）：fire-and-forget 把推送请求发布到 `message.push` 队列，不需要管返回
- 日志、网页抓取辅助（`get_cookies` / `get_headers` / `get_html`）

## 技术栈

| 类别 | 技术 |
| --- | --- |
| 语言 | Python 3.12+ |
| Web / 模型 | FastAPI / Pydantic v2 |
| 数据库 | SQLAlchemy 2.x + aiomysql（MySQL） |
| 缓存 | Redis（异步） |
| 浏览器 | Playwright（Chromium） |
| 消息 | FastStream（RabbitMQ） |
| 依赖管理 | uv |

## 目录结构

```
bili-common/
├── pyproject.toml
└── bili_common/
    ├── __init__.py            # 统一导出：db / redis / browser / message 等
    ├── exceptions.py          # 统一异常
    ├── core/
    │   ├── config.py          # Settings（mysql / redis / rabbitmq / baseUrl）
    │   ├── database.py        # engine / Base / AsyncSessionLocal / get_db / get_session
    │   ├── redis.py           # get_redis
    │       ├── browser.py         # BrowserManager
    │   ├── proxy.py           # ProxyManager / ProxyRule
    │   ├── message.py         # MessageServiceClient
    │   ├── message_pub.py     # publish_push_message（站外推送 MQ 公共发布，fire-and-forget，需 faststream）
    │   └── request.py         # get_cookies / get_headers / get_html
    ├── deps/
    │   └── auth.py            # CurrentUser（JWT 依赖）
    ├── rpc/                   # RPC 公共设施（按系统/模块分文件夹）
    │   ├── __init__.py        # 统一导出（顶层只导出纯契约，safe/client 按需子模块）
    │   ├── base.py            # RpcMethodName / 路由键前缀 / 白名单
    │   ├── safe.py            # rpc_safe 装饰器（RPC 服务端异常转回包，需 loguru）
    │   ├── client.py          # RpcClient 通用客户端（FastStream Direct Reply-To，需 faststream）
    │   ├── lottery.py         # 抽奖 RPC 契约（crawler 服务端 ↔ RPA-Browser 客户端）
    │   ├── pptr_user.py       # pptr 用户 RPC 契约（be-message 服务端 ↔ be-gateway 客户端）
    │   └── push.py            # 站外推送 RPC 契约（be-message 服务端 ↔ 其它系统客户端）
    └── models/
        ├── response.py        # 响应模型与辅助函数
        ├── response_code.py   # ResponseCodeEnum
        ├── response_msg.py    # ResponseMsgEnum
        ├── pagination.py      # PaginationParams / PageModel
        └── depends.py         # CommonDepends（缓存/分页/验证码/限流）
```

> 注：`models/` 下的 `rpc.py` / `rpc_params.py` / `pptr_user_rpc.py` / `push_rpc.py`
> 现为**兼容转发层**（re-export 自 `bili_common.rpc.*`），保证存量引用零改动。
> `rpc/safe.py` 依赖 `loguru`、`rpc/client.py` 与 `core/message_pub.py` 依赖 `faststream`，
> 均按需导入，不进入顶层导出。

### 站外推送 MQ 公共发布（fire-and-forget）

任何系统只需把推送请求丢进 `message.push` 队列即可，**不需要管返回**：

```python
from bili_common.core.message_pub import publish_push_message

# 发布到 message_exchange / message.push（队列绑定由 be-message-service 维护）
await publish_push_message(
    title="[w] 任务失败",
    content="某个工作流执行失败，请检查",
    push_type="text",
    config={"push_plus_token": "xxx"},  # 或直接传 PushChannelConfig / None（回落全局配置）
    amqp_url="amqp://guest:guest@rabbitmq:5672/",  # 缺省从环境变量 RABBITMQ_URL 读取
)
```

与 RPC 方式（`message.push.rpc.*`，同步等返回）互补；与 HTTP `POST /api/v1/message/push`
（面向终端用户）并存，本函数面向服务端系统调用。

## 安装与启动

本工程作为本地包被其它工程以路径依赖引入，自身用 uv 安装开发依赖：

```bash
cd bili-common
uv sync
```

其它工程在 `pyproject.toml` 中声明：

```toml
[tool.uv.sources]
bili-common = { path = "../bili-common" }

[dependencies]
bili-common = "*"
```

Docker 构建时通过 `UV_NO_EDITABLE=1` 强制按非 editable 安装，使其复制进 site-packages，不依赖宿主机绝对路径。

## 配置

`bili_common.core.config.Settings` 通过环境变量读取：

| 变量 | 说明 |
| --- | --- |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | MySQL 连接 |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | Redis 连接 |
| `RABBITMQ_HOST` / `RABBITMQ_PORT` / `RABBITMQ_USER` / `RABBITMQ_PASSWORD` | RabbitMQ 连接 |
| `BASE_URL` / `SERVER_NAME` / `SERVER_ADDRESS` | 服务标识 |

```python
from bili_common.core.config import settings
print(settings.mysql_host)
```

## 与其它服务的关系

- **被依赖方**：`be-bilibili-crawler`、`be-message-service`、`RPA-Browser` 均以 uv 依赖方式引用本包
- 统一响应 / 鉴权模型被所有微服务共用，保证 API 结构一致
- `MessageServiceClient` 通过 RabbitMQ 对接 `be-message-service`

## 附录：核心模块用法

### 统一响应

```python
from bili_common.models.response import success_response, error_response
from bili_common.models.response_code import ResponseCodeEnum
from bili_common.models.response_msg import ResponseMsgEnum

@router.get("/demo")
async def demo():
    return success_response(data={"hello": "world"})

@router.get("/fail")
async def fail():
    return error_response(code=ResponseCodeEnum.NOT_FOUND, msg=ResponseMsgEnum.NOT_FOUND)
```

### 依赖注入

```python
from bili_common.models.depends import CommonDepends, PaginationParams

@router.get("/list")
async def list_(
    cache=CommonDepends.use_cache(ttl=60),
    pagination: PaginationParams = CommonDepends.use_pagination(),
):
    if cache is not None:
        return cache
```

| 方法 | 说明 |
| --- | --- |
| `use_pagination()` | 解析 page/size |
| `use_cache(ttl)` / `use_set_cache` / `use_del_cache` | Redis 缓存读写 |
| `use_verification_code_cache(key, default)` | 验证码缓存 |
| `use_ip_rate_limit` / `use_user_rate_limit` | 限流 |

### 鉴权

```python
from bili_common.deps.auth import CurrentUser

@router.get("/me")
async def me(current_user: CurrentUser = Depends(CurrentUser())):
    return success_response(data={"sub": current_user.sub})
```

### 数据库 / Redis / 浏览器 / 代理 / 消息

```python
from bili_common.core import get_db, get_session, get_redis, AsyncSessionLocal, Base, engine
from bili_common.core.browser import BrowserManager
from bili_common.core.proxy import ProxyManager, ProxyRule
from bili_common.core.message import MessageServiceClient

async with BrowserManager(headless=True) as browser:
    page = await browser.new_page()

client = MessageServiceClient()
await client.send_message(payload)
```

### 日志

```python
from bili_common.core.log import logger
logger.info("hello from bili-common")
```
