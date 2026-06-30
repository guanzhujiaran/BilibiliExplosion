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

## 数据库版本管理 (Alembic)

项目通过 Alembic 管理 6 个 MySQL 数据库的 schema 版本，通过 `-x db=xxx` 指定目标库：

```bash
cd FastapiApp

# 查看各数据库当前版本
alembic -x db=biliopusdb  current
alembic -x db=bilidb      current
alembic -x db=bili_reserve current
alembic -x db=dyndetail   current
alembic -x db=proxy_db    current
alembic -x db=samsclub    current

# 生成迁移脚本 (autogenerate 对比模型与数据库自动生成)
alembic -x db=biliopusdb revision --autogenerate -m "描述此次变更"

# 执行迁移到最新版本
alembic -x db=biliopusdb upgrade head

# 回滚一个版本
alembic -x db=biliopusdb downgrade -1

# 查看迁移历史
alembic -x db=biliopusdb history
```

### 数据库对应关系

| `-x db=` | 数据库 | 主要表 |
|-----------|--------|--------|
| `biliopusdb` | 普通抽奖动态库 | `t_lotdyninfo` / `t_lot_grand_prize_flag` 等 |
| `bilidb` | 话题抽奖库 | `t_topic` / `t_traffic_card` 等 |
| `bili_reserve` | 预约抽奖库 | `t_up_reserve_relation_info` 等 |
| `dyndetail` | 动态详情库 | `bilidyndetail` / `lotdata` 等 |
| `proxy_db` | 代理数据库 | `proxy_tab` / `available_proxy` |
| `samsclub` | 山姆会员店库 | `spu_info` / `spu_category` 等 |

## SVM 大奖判断脚本

对所有已入库的抽奖数据执行 SVM 判断，将结果写入 `t_lot_grand_prize_flag` 子表：

```bash
cd FastapiApp

# 预演模式（查看有多少条待判断，不实际写入）
python3 scripts/judge_all_grand_prize_flags.py --dry-run

# 正式执行（默认每批200条，仅判断未标记的记录）
python3 scripts/judge_all_grand_prize_flags.py

# 自定义批次大小
python3 scripts/judge_all_grand_prize_flags.py --batch-size 500

# 强制重新判断所有记录（覆盖已有结果）
python3 scripts/judge_all_grand_prize_flags.py --force-update
```

## 许可证

MIT

## 注意事项
1.使用codebuddy之类的vscode魔改ide时，pylance在插件库找不到的话需要自己安装旧版本，ms-python.python(2023.4.1)和ms-python.vscode-pylance(2023.10.21)