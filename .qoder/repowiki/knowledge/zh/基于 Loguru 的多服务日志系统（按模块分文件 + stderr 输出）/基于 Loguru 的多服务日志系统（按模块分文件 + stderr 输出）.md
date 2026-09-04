---
kind: logging_system
name: 基于 Loguru 的多服务日志系统（按模块分文件 + stderr 输出）
category: logging_system
scope:
    - '**'
source_files:
    - be-bilibili-crawler/log/base_log.py
    - be-message-service/app/main.py
    - be-message-service/app/core/config.py
    - RPA-Browser/app/exceptions/handlers.py
    - RPA-Browser/app/config.py
---

## 1. 使用的框架与总体方案

仓库中所有 Python 微服务统一使用 **loguru** 作为日志库，未使用 Python 标准库 `logging`。Node.js/Express 网关 (`be-gateway`) 未发现显式日志初始化代码，业务日志主要通过调用上游 Python 服务或依赖第三方库的默认行为。

- **RPA-Browser**：直接 `from loguru import logger`，在配置加载时打印设置信息；异常处理器、路由、后台任务等各处直接使用全局 `logger`。
- **be-bilibili-crawler**：通过 `log/base_log.py` 中的 `create_logger()` 工厂为每个业务域创建带 `user` 上下文的独立 logger，并绑定到各自的文件 sink。
- **be-message-service**：在 `app/main.py` 启动时 `logger.remove()` 清空默认 sink，再添加 `sys.stderr` 作为唯一输出；开发环境额外追加一个文件 sink 到 `logs/message-service.log`。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `be-bilibili-crawler/log/base_log.py` | 定义 `UserMap` 枚举（各业务域名称），提供 `create_logger()` 工厂，为每个域生成带 UUID 前缀的 logger 实例并写入 `scripts/log/error_{domain}_log.log` |
| `be-message-service/app/main.py` | 应用入口，移除默认 sink 并添加 stderr 输出；根据 `APP_ENV` 决定是否写文件 |
| `be-message-service/app/core/config.py` | 集中声明 `LOG_LEVEL`、`FASTSTREAM_LOG_LEVEL`、`APP_ENV`、`LOG_FILE_DIR` 等日志相关配置 |
| `RPA-Browser/app/exceptions/handlers.py` | FastAPI 全局异常处理器，用 `logger.exception` / `logger.warning` / `logger.error` 记录错误并附带 `error_id` |
| `RPA-Browser/app/config.py` | 配置加载后 `logger.info(f"Settings loaded\n{settings}")` |
| `docker_vol/fastapi/log/` | 运行时生成的各模块 error log 文件目录（如 `error_fastapi_log.log`、`error_MQ_logger_log.log` 等） |

## 3. 架构与约定

### 3.1 多进程安全与异步 I/O
- `be-bilibili-crawler` 的 `create_logger()` 使用 `enqueue=True` 启用线程安全的队列模式，避免多进程并发写入同一文件产生交错。
- 所有文件 sink 均配置 `rotation="10MB"`、`retention="15 days"`（crawler 模块）或 `retention="7 days"`（message-service），并按需开启 `compression="zip"`。

### 3.2 按业务域拆分日志文件
`be-bilibili-crawler` 通过 `UserMap` 枚举集中声明所有日志域（如 `MQ_logger`、`redis_logger`、`BiliGrpcClient_logger`、`zhihu_api_logger`、`official_lot_logger` 等），每个域对应一个独立的 `error_{domain}_log.log` 文件，便于按子系统检索。

### 3.3 结构化上下文（correlation id）
- crawler 模块：`create_logger` 时用 `uuid.uuid4().hex + user.value` 生成唯一标识，通过 `bind(user=...)` 注入到每条记录的 `extra.user` 字段，并用 `filter=lambda record: record["extra"].get("user") == user_uq_value` 确保只写入该域的文件。
- RPA-Browser 异常处理器：为每次未捕获异常生成 `error_id = str(uuid.uuid4())`，并在响应体中返回，便于前端/网关关联追踪。

### 3.4 日志级别与环境差异
- message-service：生产环境 `LOG_LEVEL=WARNING`（仅告警及以上），开发环境可设为 `DEBUG`；`FASTSTREAM_LOG_LEVEL` 单独控制 FastStream 框架自身日志，与业务日志解耦。
- message-service 仅在 `APP_ENV=development` 时将 WARNING+ 写入 `logs/message-service.log`，生产环境不写任何文件，全部走 `stderr` 由 Docker 收集。
- RPA-Browser 没有统一的启动期 sink 配置，各模块直接调用全局 `logger`，默认输出到控制台。

### 3.5 容器化部署
- 所有 Python 服务的业务日志最终都输出到 `stderr`（message-service 显式 `logger.add(sys.stderr, ...)`；RPA-Browser/crawler 默认即 stdout/stderr），由 Docker Compose / K8s 收集，符合 12-Factor 原则。
- `docker_vol/fastapi/log/` 下保留历史生成的 error log 文件，用于本地调试或离线分析。

## 4. 约束与规范

- **禁止使用 Python 标准库 `logging.getLogger`**：仓库中所有 Python 服务均通过 loguru 的 `logger` 单例或 `create_logger` 工厂获取 logger，未见 `import logging` 的业务日志代码。
- **日志级别必须通过环境变量控制**：`LOG_LEVEL`（业务日志）、`FASTSTREAM_LOG_LEVEL`（FastStream 框架日志）、`APP_ENV`（决定是否写文件）均为 pydantic-settings 读取的环境变量。
- **每个业务域必须先在 `UserMap` 中注册**：新增日志域需在 `be-bilibili-crawler/log/base_log.py` 的 `UserMap` 中添加枚举值，再通过 `create_logger(UserMap.xxx)` 获取 logger，保证文件名与路径一致。
- **生产环境禁止写磁盘日志文件**：message-service 明确注释“生产不写任何日志文件，日志全部交给 docker”，crawler 通过 rotation/retention 限制磁盘占用。
- **异常必须带 error_id**：RPA-Browser 的全局异常处理器强制生成 `error_id` 并写入响应体，便于跨服务链路追踪。
- **数据库连接异常特殊处理**：对 `DisconnectionError` / `OperationalError` 且包含 "Lost connection" / "MySQL server has gone away" 的情况，统一返回 HTTP 503 并记录 warning，而非普通 500。