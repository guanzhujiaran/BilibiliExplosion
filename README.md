# BilibiliExplosion

一个自己的爬虫系统

## 功能

- B站，山姆会员店爬取数据（待增加更多感兴趣的api

## 安装

1. 克隆仓库：
   ```bash
   git https://github.com/guanzhujiaran/BilibiliExplosion.git
   ```
2. 安装依赖：
   ```bash
   cd ./FastapiApp
   pip install -r requirements.txt
   npm install
   ```
   3. 安装ipv6代理池
       ```bash
       git clone https://github.com/guanzhujiaran/go-proxy-ipv6-pool-auto.git
       cd go-proxy-ipv6-pool-auto
       cd go-proxy-ipv6-pool
       go mod install
       go build -o
       ```
      - 安装代理所需库
      - ```bash
        apt install ndppd -y
        sysctl net.ipv6.ip_nonlocal_bind=1
         ```
4. 安装unidbg-springboot后端
    ```bash
    git clone https://github.com/guanzhujiaran/unidbgSpringBoot
    mvn clean spring-boot:build
    ```
5. 安装nodejs后端
    ```bash
    git clone https://github.com/guanzhujiaran/puppeteer_Bili.git
   ```
## 使用方法

1. 启动ipv6代理池：
    ```bash
    npm i pm2 -g
    pm2 start pm2.app.js
    ```
2. docker：
   ```bash
   docker-compuse up -d
   ```

## 许可证

MIT