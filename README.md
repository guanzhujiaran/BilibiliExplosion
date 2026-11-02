# BilibiliExplosion

一个自建的 B 站（及山姆会员店等）数据采集与自动化系统。采用 git submodule 聚合多个微服务，通过 Docker Compose 一键编排，覆盖爬虫、签名计算、RPA 浏览器、消息推送与前端网关。

## 功能

- B 站抽奖（动态 / 官方 / 话题 / 预约）、山姆会员店等数据采集（待增加更多 API）
- 统一消息推送（PushMe / PushPlus / 邮箱 / Bark / 钉钉 / 飞书 / Server 酱 / 企业微信 / Ntfy / WxPusher 等）
- 本地 LLM 大奖判定（SVM + LLM 二阶段）
- 推送消息中包含 `[deploy]` 可触发 GitHub Workflow，构建对应 Docker 镜像

## 项目一览

| 子工程 | 语言 / 技术 | 角色 | README |
| --- | --- | --- | --- |
| `be-bilibili-crawler` | Python / FastAPI | 核心爬虫后端 + 数据 API | [README](be-bilibili-crawler/README.md) |
| `be-message-service` | Python / FastAPI + FastStream | 统一消息推送微服务 | [README](be-message-service/README.md) |
| `RPA-Browser` | Python / FastAPI + Playwright | RPA 浏览器自动化服务 | [README](RPA-Browser/README.md) |
| `puppeteer_Bili` | Node.js / Express | 前端网关 + 账号/抽奖后端 | [README](puppeteer_Bili/README.md) |
| `unidbgSpringBoot` | Java / Spring Boot | B 站签名计算服务 | [README](unidbgSpringBoot/README.md) |
| `go-proxy-ipv6-pool-auto` | Go | 自动 IPv6 代理池 | [README](go-proxy-ipv6-pool-auto/README.md) |
| `bili-common` | Python | 后端公共依赖库（被上述 Python 服务复用） | [README](bili-common/README.md) |

## 技术栈

| 类别 | 技术 |
| --- | --- |
| 后端 | Python 3.12/3.13（FastAPI）、Java 17（Spring Boot）、Node.js 18+（Express）、Go |
| 数据 | MySQL 8、Redis、PostgreSQL、Milvus（向量） |
| 消息 | RabbitMQ（FastStream） |
| 自动化 | Playwright / Patchright、unidbg、Puppeteer |
| 推理 | llama.cpp / Ollama（Qwen 等） |
| 编排 | Docker Compose |
| 依赖管理 | uv（Python）、Maven（Java）、npm（Node） |

## 目录结构

```
BilibiliExplosion/
├── docker-compose.yml        # 生产编排（mysql/redis/rabbitmq/milvus/postgres/casdoor/各服务/llama.cpp/go-proxy）
├── docker-compose.dev.yml    # 开发编排（基础设施 + 爬虫容器 23333（IS_DEV=1 不爬取）+ 只读查询 23336 + nginx/go-proxy）
├── Dockerfile.mono           # 多阶段构建（crawler / crawler-query / rpa / message 目标）
├── Makefile
├── bili-common/              # 公共依赖库
├── be-bilibili-crawler/      # 核心爬虫后端
├── be-message-service/       # 统一消息推送
├── RPA-Browser/              # RPA 浏览器
├── puppeteer_Bili/           # 前端网关 + Node 后端
├── unidbgSpringBoot/         # 签名计算
├── go-proxy-ipv6-pool-auto/  # IPv6 代理池
└── docker_vol/               # 各中间件数据卷
```

## 安装

本项目使用 git submodule 管理微服务：`be-bilibili-crawler`、`be-message-service`、`go-proxy-ipv6-pool-auto`、`unidbgSpringBoot`、`puppeteer_Bili`、`RPA-Browser`。（`bili-common` 为 monorepo 内共享包，非 submodule。）

克隆时请带上 `--recurse-submodules`，或克隆后初始化：

```bash
git clone --recurse-submodules https://github.com/guanzhujiaran/BilibiliExplosion.git
# 若已克隆：git submodule update --init --recursive
```

一键更新所有微服务到远端最新（等同于 `make update`）：

```bash
git pull && git submodule update --remote --recursive
```

后端均使用 **uv** 管理环境与依赖，请先安装 uv：

```bash
pip install uv
# 或
curl -LsSf https://astral.sh/uv/install.sh | sh
```

各子工程安装方式（详见各自 README）：

1. `be-bilibili-crawler`：`uv sync` + `npm install`
2. `be-message-service`：`uv sync`
3. `RPA-Browser`：`uv sync`
4. `go-proxy-ipv6-pool-auto`：`docker compose up -d --build go-proxy-server`（NDP 代答已内置在程序里，不再需要 ndppd；宿主要求 `sysctl -w net.ipv6.ip_nonlocal_bind=1`）
5. `unidbgSpringBoot`：`./mvnw clean package`
6. `puppeteer_Bili`：`npm install`
7. ollama（本地 LLM，对应 `llama_cpp`）：

  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ollama serve
  # 或 Docker 启动 llama.cpp（无需本机装 ollama）：
  docker compose up -d llama_cpp          # CPU 版（生产编排只包含这一版）
  ```

  > 生产编排 `docker-compose.yml` 只保留 CPU 版 `llama_cpp`：GPU 版带 `nvidia` 设备预留，
  > 在无 nvidia 容器运行时的机器上会让整条 `docker compose up -d` 中断，因此已移除。
  > 需要 GPU 推理时用 `docker-compose.dev.yml` 的 gpu profile
  > （`docker compose -f docker-compose.dev.yml --profile gpu up -d`）。

## 使用方法

1. 启动 ipv6 代理池（已容器化，`network_mode: host`，无需 pm2）：

   `go-proxy-server` 挂在独立 profile `ipv6-proxy` 下，**默认 `docker compose up -d` 不会起它**，
   因为它必须在「持有公网 IPv6 前缀、且独占该 /64 的 NDP 代答」的那台机器上跑（目前是生产端）。
   同一个 /64 上跑两个实例会互相抢答，光猫邻居缓存被覆盖后对方所有随机出口都会 `i/o timeout`，
   停掉一台还要等缓存过期几分钟才恢复。

   ```bash
   # 生产端：构建并启动/更新（显式指定服务名会忽略 profile）
   docker compose up -d --build go-proxy-server
   # 需要连它一起全量启动时
   docker compose --profile ipv6-proxy up -d
   ```

2. 本地开发（dev 编排）：

  ```bash
  docker compose -f docker-compose.dev.yml up -d     # 基础设施 + 两个爬虫容器
  cd Vue3FrontEndDemoExercise && npm run dev         # 前端 5173
  ```

  本地有**两个**应用容器（同一镜像的两个 target）：

  | 容器 | 端口 | 角色 | 库 |
  | --- | --- | --- | --- |
  | `be-bilibili-crawler-query` | 23336 | 只读查询（`query_main.py`）+ **RPC 服务端**（`FastapiApp.rpc.*`，全部只读取数） | **生产库 / 生产 Redis**（`CRAWLER_QUERY_*`），数据是真实的 |
  | `be-bilibili-crawler` | 23333 | **与生产同一角色**（`SERVICE_ROLE` 默认 `crawler`，入口 `main:app`） | 本地 mysql（root，可写）；`IS_DEV=1` 只关掉定时任务 / 监控任务（**不自动爬取**），迁移 / schema 校验 / Milvus / **MQ 入库消费（写库通道）**照常；不提供 RPC |

  `be-bilibili-crawler` 与生产**同一个容器角色**，`bili_data` 的入库消费者（**写库通道**）都在这个进程里。
  两条通道分工明确（2.70.0）：**RPC 只做只读取数**，服务端在 query 容器（`get_*` / `check_*`）；
  **写库走普通 MQ 消息**（`BiliLotDataPublisher` → crawler 的入库消费者），不用 RPC ——
  所以爬虫容器没起，RPA / be-message 取数也照常可用
  （旧的 `SERVICE_ROLE=api` 容器不挂 MQ 路由、既没有写库消费者也没有 RPC 服务端，已废弃）。
  「开发环境不自动爬」靠环境变量 `IS_DEV=1`，想跑真实爬取时改成 `0`。
  `Add*` 与爬虫回写都落本地库，不会碰生产。

  分流由前端 dev server 的 `/api` 代理完成（见 `nuxt.config.ts` 的 `server.proxy`）：

  | 请求 | 去向 |
  | --- | --- |
  | 抽奖查询 `Get*` / `Search*` / `lottery_*` | 本地查询容器 `localhost:23336` |
  | 爬虫状态 `Get*ScrapyStatus`、`Add*`、`zhuanlan`、rpa、message、casdoor | 本机 `localhost:9923` 的网关 |

  网关的 `BILI_CRAWLER_URI` 指向 `23333`（爬虫容器）、`BILI_CRAWLER_QUERY_URI` 指向 `23336`。
  `Add*` 落在**查询**容器上仍然没有路由（404），所以走前端直连查询容器那条链路
  **本地不可能误写生产库**。

  两个目标是 `nuxt.config.ts` 里的常量（`QUERY_API` / `GATEWAY_API`），
  需要连远端网关时改那两行即可，不引入额外环境变量。
  改了爬虫代码重启对应容器即可生效（源码已 bind mount）。


3. Docker 部署（推荐）：

   ```bash
   docker compose up -d
   ```

## 许可证

MIT

## 注意事项

1. 使用 CodeBuddy 之类 VSCode 魔改 IDE 时，若 pylance 在插件库找不到，需手动安装旧版本：`ms-python.python` (2023.4.1) 与 `ms-python.vscode-pylance` (2023.10.21)。
2. Milvus 报错无法读写：`sudo chown -R 999:999 ./docker_vol/milvus/data`。
3. WSL2 mirrored 连不上网：重启 winnat（`net stop winnat` → `net start winnat`）。
