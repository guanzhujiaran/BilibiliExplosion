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

   > `rpa-browser` 使用 **host 网络**（`network_mode: host`），直接监听宿主机 `28000`，
   > 以便 WebRTC offer 带出宿主机公网 IPv6 host 候选、让外网手机直连媒体；
   > 依赖服务一律走 `127.0.0.1:<宿主机映射端口>`。`28000` 必须用
   > `scripts/docker/rpa-host-firewall.sh` 限制来源（仅 loopback 与 Docker 网段），
   > 媒体 UDP `32768:60999` 按需放行。**Docker Desktop 不支持 host 网络，仅限 Linux 宿主机。**

## 自动部署（脚本一键式）

整套部署只依赖 **bash + git + docker compose**：服务器上的 timer 轮询 `origin/main`，
发现新提交就调 `scripts/deploy/remote_deploy.sh` 完成「依赖层判定 → 按需重建镜像 →
重启容器 → 健康检查 → 失败自动回滚 → 记录」。不引入 Jenkins / GitHub Actions 之类的外部编排。

| 文件 | 作用 |
| --- | --- |
| `scripts/deploy/install_auto_deploy.sh` | 一键安装/卸载 systemd timer（替代 cron，跑完即退） |
| `scripts/deploy/auto_deploy.sh` | 一次轮询：判断是否有新提交、失败退避、暂停开关、日志 |
| `scripts/deploy/remote_deploy.sh` | 真正的发布动作（含 `flock` 互斥、健康检查、回滚） |

为什么是「服务器主动拉」：生产机在内网/家里，不需要可被外部回连的 SSH，也不用把私钥寄存在第三方；
拉不到就什么都不做，不会留下「部署到一半」的状态。

> `docker-compose.yml` 里业务服务源码是 **bind mount**，镜像只承载依赖层。
> 所以**发布 = 服务器上更新工作区 + 重启容器**；只有 `Dockerfile.mono` / `uv.lock` / compose
> 文件变化时才 rebuild。

### 一次性安装（生产机，仓库根目录执行）

```bash
sudo bash scripts/deploy/install_auto_deploy.sh --interval 120
#   --user deploy   指定跑部署的系统用户（默认 sudo 调用者）
#   --dry-run       只打印 systemd unit 内容
#   --uninstall     卸载
```

装完即生效：`biliexplosion-auto-deploy.timer` 每 120s 跑一次，跑完即退。

前置条件（缺一不可）：

1. 仓库已克隆到生产机、`.env` 已按 `.env.example` 配好、`docker_vol/` 已创建；
2. 执行部署的用户**在 docker 组内**，且能 `git fetch` 根仓库与所有 submodule
   （私有仓库需 deploy key / credential helper；服务器走代理时配置 `git config --global http.proxy`）。

### 日常操作

```bash
bash scripts/deploy/auto_deploy.sh --status          # 本地 SHA / 远端 SHA / 上次成功 / 是否暂停
systemctl list-timers biliexplosion-auto-deploy.timer
systemctl start biliexplosion-auto-deploy.service    # 立刻跑一次，不等 timer
tail -f docker_vol/deploy/auto.log                   # 部署记录（自动轮转 5MB）
touch docker_vol/deploy/pause                        # 维护窗口：暂停自动部署
rm -f docker_vol/deploy/pause                        # 恢复

# 手工发布（与自动部署共用一把锁，不会并发）
DEPLOY_PATH=/opt/BilibiliExplosion ./scripts/deploy/remote_deploy.sh
DRY_RUN=1 SERVICES="be-bilibili-crawler" ... ./scripts/deploy/remote_deploy.sh   # 演练，不改工作区
REBUILD=1 ... ./scripts/deploy/remote_deploy.sh                                 # 强制重建镜像
```

保护机制：

| 场景 | 行为 |
| --- | --- |
| 自动 / 手工 / timer 同时触发 | `flock` 互斥，后到的直接跳过，下个周期重试 |
| 工作区有未提交改动 | 拒绝发布（退出码 2；`FORCE=1` 覆盖），自动部署会退避 30 分钟并告警 |
| 健康检查失败 | 自动 `git reset --hard` 回上一个 SHA + 重建重启，并对该版本退避 30 分钟 |
| 同一版本反复失败 | 30 分钟内不重试，避免「回滚 → 重试 → 回滚」死循环 |
| 维护窗口 | `touch docker_vol/deploy/pause` |

健康检查用 `docker compose port` 反查宿主机端口（不写死）：crawler `23333/health`、
query `23336/health`、message `18739/health`；另外 `docker compose ps` 里出现 `exited` /
`restarting` 也算失败。

### 完整交付链路（没有 CI 服务器也能跑）

```text
开发机改代码 → git push → 生产机 timer 拉取并发布 → 健康检查 → 失败自动回滚
```

```bash
# 1. 开发机：改代码 → 提交 → 推送
git add -A && git commit -m "feat: xxx" && git push origin main

# 2. 生产机：什么都不用做（timer 每 2 分钟自动拉取并发布）
#    想立刻发就执行：
systemctl start biliexplosion-auto-deploy.service

# 3. 看结果
tail -n 50 docker_vol/deploy/auto.log
docker compose ps
```

发布脚本自己完成「依赖层判定 → 按需重建 → 重启 → 健康检查 → 失败回滚 → 记录」，
所以不需要外部 CI 来做这些编排；单测/语法检查在提交前本地跑即可：

```bash
cd be-bilibili-crawler && uv run pytest test -q \
  --ignore=test/test_prize_extract_flow.py --ignore=test/test_other_routers.py \
  --ignore=test/test_background_service.py --ignore=test/test_get_others_lot_round.py \
  --ignore=test/test_lottery_data.py --ignore=test/test_chatgpt.py
```

## 许可证

MIT

## 注意事项

1. 使用 CodeBuddy 之类 VSCode 魔改 IDE 时，若 pylance 在插件库找不到，需手动安装旧版本：`ms-python.python` (2023.4.1) 与 `ms-python.vscode-pylance` (2023.10.21)。
2. Milvus 报错无法读写：`sudo chown -R 999:999 ./docker_vol/milvus/data`。
3. WSL2 mirrored 连不上网：重启 winnat（`net stop winnat` → `net start winnat`）。
