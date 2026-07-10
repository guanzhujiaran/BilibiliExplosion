# BilibiliExplosion

一个自己的爬虫系统

## 功能

- B站，山姆会员店爬取数据（待增加更多感兴趣的api）
- 推送消息里面附带`[deploy]`就可以触发github的workflow，构建对应的docker镜像

## 安装

本项目使用 git submodule 管理全部微服务：`be-fastapi-backend`、`be-message-service`、`go-proxy-ipv6-pool-auto`、`unidbgSpringBoot`、`puppeteer_Bili`、`RPA-Browser`。

克隆时请带上 `--recurse-submodules`，或克隆后初始化：

```bash
git clone --recurse-submodules https://github.com/guanzhujiaran/BilibiliExplosion.git
# 若已克隆：git submodule update --init --recursive
```

一键更新所有微服务到远端最新（等同于 `make update`）：

```bash
git pull && git submodule update --remote --recursive
```

1. 安装 FastAPI 后端依赖（`be-fastapi-backend`）：
   ```bash
   cd ./be-fastapi-backend
   pip install -r requirements.txt
   npm install
   ```

2. 安装消息推送服务（`be-message-service`）：
   ```bash
   cd ./be-message-service
   pip install -r requirements.txt
   ```

3. 安装 ipv6 代理池（`go-proxy-ipv6-pool-auto`）：
   ```bash
   cd ./go-proxy-ipv6-pool-auto/go-proxy-ipv6-pool
   go mod download
   go build -o proxy-pool
   ```
   
   安装代理所需库：
   ```bash
   apt install ndppd -y
   sysctl net.ipv6.ip_nonlocal_bind=1
   ```

4. 安装 unidbg-springboot 后端（`unidbgSpringBoot`）：
   ```bash
   cd ./unidbgSpringBoot
   mvn clean spring-boot:build
   ```

5. 安装 nodejs 后端（`puppeteer_Bili`）：
   ```bash
   cd ./puppeteer_Bili
   npm install
   ```

6. 安装 ollama


## 使用方法

1. 启动ipv6代理池（或者使用supervisor之类的）：
   ```bash
   npm i pm2 -g
   pm2 start pm2.app.js
   ```

2. Docker部署：
   ```bash
   docker-compose up -d
   ```


## 许可证

MIT

## 注意事项
1.使用codebuddy之类的vscode魔改ide时，pylance在插件库找不到的话需要自己安装旧版本，ms-python.python(2023.4.1)和ms-python.vscode-pylance(2023.10.21)