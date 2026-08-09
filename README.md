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
├── docker-compose.yml        # 统一编排（mysql/redis/rabbitmq/milvus/postgres/casdoor/各服务/llama.cpp）
├── Dockerfile.mono           # 多阶段构建（crawler / rpa / message 目标）
├── pm2.app.js                # 本地 pm2 启动脚本（ipv6 代理池）
├── dc-dev.yml  Makefile
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
4. `go-proxy-ipv6-pool-auto`：`go mod download && go build -o proxy-pool`（另需 `apt install ndppd -y` + `sysctl net.ipv6.ip_nonlocal_bind=1`）
5. `unidbgSpringBoot`：`./mvnw clean package`
6. `puppeteer_Bili`：`npm install`
7. ollama（本地 LLM，对应 `llama_cpp` / `llama_cpp_gpu_cuda`）：

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve
   # 或 Docker 启动 llama.cpp（无需本机装 ollama）：
   docker compose up -d llama_cpp          # CPU 版
   docker compose up -d llama_cpp_gpu_cuda # 有 NVIDIA GPU 时启用 CUDA 版
   ```

## 使用方法

1. 本地启动 ipv6 代理池（或用 supervisor 等）：

   ```bash
   npm i pm2 -g
   pm2 start pm2.app.js
   ```

2. Docker 部署（推荐）：

   ```bash
   docker compose up -d
   ```

## 许可证

MIT

## 注意事项

1. 使用 CodeBuddy 之类 VSCode 魔改 IDE 时，若 pylance 在插件库找不到，需手动安装旧版本：`ms-python.python` (2023.4.1) 与 `ms-python.vscode-pylance` (2023.10.21)。
2. Milvus 报错无法读写：`sudo chown -R 999:999 ./docker_vol/milvus/data`。
3. WSL2 mirrored 连不上网：重启 winnat（`net stop winnat` → `net start winnat`）。
