# BilibiliExplosion

一个自己的爬虫系统

## 功能

- B站，山姆会员店爬取数据（待增加更多感兴趣的api）
- 推送消息里面附带`[deploy]`就可以触发github的workflow，构建对应的docker镜像

## 安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/guanzhujiaran/BilibiliExplosion.git
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
   go mod download
   go build -o proxy-pool
   ```
   
   安装代理所需库：
   ```bash
   apt install ndppd -y
   sysctl net.ipv6.ip_nonlocal_bind=1
   ```

4. 安装unidbg-springboot后端
   ```bash
   git clone https://github.com/guanzhujiaran/unidbgSpringBoot
   cd unidbgSpringBoot
   mvn clean spring-boot:build
   ```

5. 安装nodejs后端
   ```bash
   git clone https://github.com/guanzhujiaran/puppeteer_Bili.git
   cd puppeteer_Bili
   npm install
   ```
6. 配置goaccess
    ```
   
   ```
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