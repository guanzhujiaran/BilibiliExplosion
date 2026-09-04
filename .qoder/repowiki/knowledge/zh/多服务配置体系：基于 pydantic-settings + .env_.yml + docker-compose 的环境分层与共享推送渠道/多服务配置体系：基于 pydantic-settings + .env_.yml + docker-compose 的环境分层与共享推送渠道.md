---
kind: configuration_system
name: 多服务配置体系：基于 pydantic-settings + .env/.yml + docker-compose 的环境分层与共享推送渠道
category: configuration_system
scope:
    - '**'
source_files:
    - RPA-Browser/app/config.py
    - RPA-Browser/.env.dev
    - be-bilibili-crawler/CONFIG.py
    - be-bilibili-crawler/.env.fastapi.dev
    - be-message-service/app/core/config.py
    - be-message-service/app/main.py
    - be-gateway/ExpressServerEnd/config/config.yml
    - be-gateway/ExpressServerEnd/config/index.js
    - be-gateway/nodejs_backend.config.js
    - Vue3FrontEndDemoExercise/.env.development
    - Vue3FrontEndDemoExercise/.env.prod
    - bili-common/bili_common/models/push.py
    - docker-compose.yml
---

## 1. 整体方案

本仓库是一个多语言、多服务的聚合平台（Python FastAPI、Node.js Express、Vue3 前端、Go IPv6 代理、Java Spring Boot），每个子服务各自维护独立的配置系统，但通过 **统一的 `MESSAGE_CONFIG` JSON 环境变量** 在 Python 服务间共享推送渠道配置。配置来源按优先级叠加：**环境变量 > `.env` 文件 > 代码默认值**；容器编排由 `docker-compose.yml` 集中注入运行时参数。

- Python 侧统一使用 `pydantic_settings.BaseSettings` + `SettingsConfigDict(env_file=...)` 加载配置，并通过 Pydantic 模型对字段做类型校验与结构化嵌套。
- Node.js 网关使用 PM2 (`pm2.app.js`) 启动 Express，并通过 `js-yaml` 读取 `ExpressServerEnd/config/config.yml` 作为业务配置。
- Vue3 前端通过 Vite 的 `VITE_*` 前缀 `.env.development` / `.env.prod` 注入构建期常量。
- 所有服务依赖（MySQL、Redis、RabbitMQ、Postgres、Casdoor）的连接信息通过 `docker-compose.yml` 的 `environment` 段注入，避免硬编码。

## 2. 关键文件与位置

| 服务 | 配置文件 | 说明 |
|---|---|---|
| RPA-Browser | `RPA-Browser/app/config.py` | 定义 `Settings(BaseSettings)`，加载 `.env.prod`/`.env.dev`，暴露 `settings` 单例与 `CONF.Path` |
| be-bilibili-crawler | `be-bilibili-crawler/CONFIG.py` | 定义 `Settings(BaseSettings)`，加载 `.env.fastapi.prod`/`.env.fastapi.dev`，并封装 `DataBaseConfig`、`SqlAlchemyConfig`、`RabbitMQConfig` 等派生配置 |
| be-message-service | `be-message-service/app/core/config.py` | 定义 `Settings(BaseSettings)`，加载 `app/.env`，包含 EdgeRank、分片、ID 生成、Casdoor 等大量运行时开关 |
| be-gateway (Node) | `be-gateway/ExpressServerEnd/config/config.yml` + `config/index.js` | YAML 业务配置（salt、jwt_secret、level_config、mq_config），PM2 通过 `nodejs_backend.config.js` 传入 `--env=prod|dev` |
| Vue3 前端 | `Vue3FrontEndDemoExercise/.env.development` / `.env.prod` | `VITE_API_BASE_URL`、`VITE_BILI_ENV`、`VITE_CASDOOR_*` 等构建期变量 |
| bili-common | `bili-common/bili_common/models/push.py` | 跨服务共享的 `PushChannelConfig` SQLModel，被 RPA-Browser、be-bilibili-crawler、be-message-service 复用 |
| 容器编排 | `docker-compose.yml` | 集中注入各服务的环境变量（如 `MYSQL_PASSWORD`、`RABBITMQ_USER`、`MESSAGE_CONFIG`、`CASDOOR_*`） |

## 3. 架构与设计约定

### 3.1 配置加载顺序与覆盖规则

- **RPA-Browser**：`SettingsConfigDict(env_file=("../.env.prod", "../.env.dev"))`，先 prod 后 dev，后者覆盖前者；`case_sensitive=False`，`extra="ignore"`。
- **be-bilibili-crawler**：`env_file=(".env.fastapi.prod", ".env.fastapi.dev")`，同样先 prod 后 dev。
- **be-message-service**：`env_file=("app/.env",)`，仅加载单个 `.env`。
- 所有服务均通过 `model_post_init` / property 在加载后做二次处理（如 message-service 将证书中的字面量 `\n` 转为真实换行、限制连接池上限不超过 100）。

### 3.2 共享推送渠道配置（`MESSAGE_CONFIG`）

三个 Python 服务（RPA-Browser、be-bilibili-crawler、be-message-service）都定义了结构完全一致的 `PushChannelConfig`（Bark、钉钉、飞书、企业微信、Telegram、SMTP、PushMe、PushPlus、Ntfy、WxPusher 等渠道），并通过同一个 `MESSAGE_CONFIG` JSON 环境变量注入：

```
MESSAGE_CONFIG='{"pushme_key":"...","smtp_server":"...","tg_bot_token":"..."}'
```

- RPA-Browser 和 be-bilibili-crawler 将其作为全局兜底配置（当 per-user 未提供时）。
- be-message-service 在消费者中解析该 JSON 为 `PushChannelConfig`，实现“发送方不关心接收方如何消费”的解耦。
- 公共契约集中在 `bili-common/bili_common/models/push.py` 的 `PushChannelConfig`（SQLModel），确保序列化/反序列化一致。

### 3.3 数据库与中间件连接串

- MySQL：各服务通过 `mysql+aiomysql://user:pass@host/db?charset=utf8mb4` 形式拼接，连接池大小、`pool_pre_ping`、`pool_recycle` 在 `CONFIG.py` 中集中声明。
- Redis：be-bilibili-crawler 用多个 `db` 号区分用途（proxy_db 用 db15、lotData 用 db2 等）。
- RabbitMQ：统一使用 `amqp://user:pass@rabbitmq:5672/?heartbeat=180`，心跳 180s 与长耗时 RPC 匹配。
- Postgres：message-service 直连 pptr 库（PPTR_Bili_Lot）用于用户展示信息只读查询。

### 3.4 运行期开关与特性门控

- `RUNNING_MODE` / `IS_DEV`：控制是否启动定时任务、日志级别等。
- `alembic_auto_migrate`：应用启动时自动执行 Alembic 迁移（RPA-Browser、message-service 均支持）。
- `require_approval_enabled`：RPA-Browser 强制审批开关。
- `edgerank_*`：message-service 的推荐排序算法权重、召回路开关、个性化开关等数十个可调参数，全部以环境变量形式暴露。
- `comment_pre_audit` / `dm_pre_audit`：评论/私信的“先审后发”开关。

### 3.5 前端配置

- Vite 构建期变量必须以 `VITE_` 前缀才能在浏览器端访问。
- 开发环境 `VITE_BILI_ENV=dev`，生产环境 `VITE_BILI_ENV=prod`，用于切换 Casdoor 组织名、分析 ID 等。
- 生产环境通过后端代理 `/api/v1/casdoor` 访问 Casdoor，因此前端无需配置 `VITE_CASDOOR_SERVER_URL`（或指向外部域名）。

### 3.6 Node.js 网关配置

- PM2 通过 `nodejs_backend.config.js` 定义两个 app：`nodejs_express_backend_nginx`（prod）和 `dev_nodejs_express_backend_nginx`（dev, --port=9926）。
- 业务配置集中在 `ExpressServerEnd/config/config.yml`，含密码盐、JWT secret、等级经验表、cron 计划、RabbitMQ 连接及 RPC 超时。
- `config/index.js` 用 `fs.readFileSync` + `js-yaml.load` 同步读取 YAML，并在模块加载时打印全量配置。

## 4. 约束与规范

1. **新增配置项必须加到 `BaseSettings` 子类并带默认值**，禁止裸 `os.environ.get("XXX")` 散落各处。
2. **敏感信息（密码、token、密钥）不得写入库**，一律走环境变量或 `.env`，且 `.env` 不应提交（各服务 `.gitignore` 已忽略）。
3. **跨服务共享的配置（如推送渠道）必须在 `bili-common` 中定义单一模型**，其他服务引用该模型而非各自复制一份。
4. **Docker 部署时所有服务连接信息通过 `docker-compose.yml` 的 `environment` 注入**，容器内不允许硬编码主机名或端口。
5. **连接池上限受保护**：message-service 在 `model_post_init` 中强制 `mysql_pool_size + mysql_max_overflow ≤ 100`，防止误配导致 MySQL Too many connections。
6. **日志级别与环境绑定**：production 默认 `WARNING`，development 可设 `DEBUG`；业务日志输出到 stderr，由 Docker 收集，不写文件（除非 `APP_ENV=development` 且指定 `LOG_FILE_DIR`）。
7. **Alembic 迁移默认随应用启动自动执行**（`alembic_auto_migrate=True`），可通过环境变量关闭。
8. **前端 `VITE_*` 变量仅在构建期可用**，运行时无法修改；后端动态配置应通过 API 或环境变量热更新。

## 5. 适用性判断

本仓库存在完整且成体系的配置系统：每个 Python 服务使用 `pydantic-settings` 进行强类型配置加载，Node.js 服务使用 YAML + PM2，前端使用 Vite 环境变量，并由 `docker-compose.yml` 统一编排注入。推送渠道配置通过 `bili-common` 的共享模型实现跨服务一致性。因此该类别完全适用。