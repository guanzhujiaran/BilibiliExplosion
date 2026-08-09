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
    │   ├── browser.py         # BrowserManager
    │   ├── proxy.py           # ProxyManager / ProxyRule
    │   ├── message.py         # MessageServiceClient
    │   └── request.py         # get_cookies / get_headers / get_html
    ├── deps/
    │   └── auth.py            # CurrentUser（JWT 依赖）
    └── models/
        ├── response.py        # 响应模型与辅助函数
        ├── response_code.py   # ResponseCodeEnum
        ├── response_msg.py    # ResponseMsgEnum
        ├── pagination.py      # PaginationParams / PageModel
        └── depends.py         # CommonDepends（缓存/分页/验证码/限流）
```

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
