# be-bilibili-crawler 生产库抽奖数据同步脚本计划书

> 方案：**新增 `scripts/database/sync_lottery_from_prod/` 脚本，源=生产库（`.env.fastapi.prod`），目标=本地开发库（全局 settings，即 dev 覆盖后的值），MySQL 层按 ORM 模型做「拓扑排序 + 列交集 + keyset 分页 + upsert」的全量/增量同步**
> 状态：**已实施**

---

## 1. 背景与问题

本地开发时经常需要一份**与生产一致的抽奖数据**来调试接口 / 复现问题（如中奖榜、官方抽奖卡片、第三方抽奖动态列表）。当前做法是手工 `mysqldump` 再导入，存在以下问题：

1. 手工选库选表，容易漏表（`lotdata` / `t_lot_extra_info` / `bili_atari_info` / `t_lotdyninfo` / `t_up_reserve_relation_info` 等跨 4 个库，且 `t_lot_extra_info` 在 dyndetail 与 biliopusdb 各有一份、结构不同）；
2. 不处理外键依赖顺序，直接导入会报 1452；
3. 全量覆盖会冲掉本地开发库里有意的改动，也无法只做增量刷新；
4. 生产 / 开发两套连接散落在 `.env.fastapi.prod` / `.env.fastapi.dev` 里，没有统一入口。

## 2. 目标

- 一条命令把**生产库的抽奖数据**同步到**本地开发库**，默认 upsert（不删本地多出的行），可用 `--truncate` 做精确镜像；
- 连接信息默认来自环境文件，支持 CLI 覆盖，不硬编码任何地址；
- 同步过程可见：每张表的源行数、写入行数、耗时、跳过原因都有日志与汇总；
- 只同步 MySQL 抽奖数据；Redis / Milvus / alembic_version 明确不在范围内。

## 3. 同步范围（表清单）

以 ORM 模型为单一事实来源（与 `create_database.py` 的 4 个抽奖库一致）：

| 库 | 表 | 说明 |
|---|---|---|
| dyndetail | `lotdata`、`t_lot_extra_info`、`bili_user_info`、`bili_atari_info`、`bilidyndetail`、`article_pub_record` | 官方/预约/充电抽奖主表 + 中奖记录 + 动态详情 |
| biliopusdb | `t_lotmaininfo`、`t_lotuserinfo`、`t_lotdyninfo`、`t_riddynid`、`t_lotuserspaceresp`、`t_lot_extra_info` | 第三方抽奖动态流水线 |
| bili_reserve | `t_reserve_round_info`、`t_up_reserve_relation_info` | 预约抽奖 |
| bilidb | `t_traffic_card`、`t_click_area_card`、`t_topic_creator`、`t_topic_item`、`t_functional_card`、`t_top_details`、`t_activity_lottery`、`t_activity_match_lottery`、`t_activity_match_task`、`t_era_jika`、`t_era_lottery`、`t_era_task`、`t_era_video`、`t_capsule`、`t_topic` | 话题抽奖 |

**排除** `bilidb.t_spaceseries`：B 站播放列表缓存，不属于抽奖数据（约 400 万行，同步它只会拖慢脚本）。

## 4. 方案设计

### 4.1 源 / 目标连接解析

- **目标（本地开发库）**：复用全局 `settings`（`CONFIG.py` 的 env_file 为 `(.env.fastapi.prod, .env.fastapi.dev)`，dev 覆盖 prod，即本地视角 `localhost:10000`）；`--db-host/--db-port/--db-user/--db-password` 经 `scripts/_cli_utils.apply_cli_overrides` 覆盖。
- **源（生产库）**：独立构造，不读全局 settings（避免 dev 值污染）。默认读 `.env.fastapi.prod` 的 `MYSQL_*`（`--source-env` 可换文件）；优先级 `--source-db-*` > 环境变量 `SYNC_SOURCE_MYSQL_HOST/PORT/USER/PASSWORD` > env 文件。
- URI 统一走 `sqlalchemy.URL.create` 组装，密码特殊字符自动转义。

### 4.2 写入策略

- **upsert（默认）**：`INSERT ... ON DUPLICATE KEY UPDATE`，更新集 = 同步列去掉主键列；不删除目标库多出的行，可反复执行（幂等）。
- **`--truncate`**：先按**逆拓扑序** `DELETE FROM` 清空目标表，再全量写入，得到与生产精确一致的镜像（不用 `TRUNCATE`，避免外键与隐式提交问题）。
- **`--dry-run`**：只连通性检查 + 统计源/目标行数，不写任何数据。

### 4.3 正确性处理

- **外键拓扑排序**：按 `Table.foreign_key_constraints` 建依赖图，Kahn 拓扑排序后按序写入；`--truncate` 用逆序删除。有环则告警并退回清单原序。
- **列交集**：同步列 = ORM 列 ∩ 源库实际列 ∩ 目标库实际列，且排除 `Computed` 列（如 `bilidyndetail.rid_int`）；任一侧缺表则告警跳过该表（容忍开发库未迁移到最新）。
- **keyset 分页**：按主键元组 `WHERE (pk...) > (:last...) ORDER BY pk... LIMIT n` 翻页，避免大表 OFFSET 深页退化；单列主键自动退化为主键比较。
- **写重试**：单批 upsert 失败按死锁/超时类错误重试 3 次（指数退避），仍失败则记该表失败并继续其他表，退出码非 0。

### 4.4 用法

```bash
# 预览：只看两边连接与各表行数，不写库
uv run python -m scripts.database.sync_lottery_from_prod.sync_lottery --dry-run

# 全量同步（源默认 .env.fastapi.prod；生产 mysql 主机在容器网络内，本地跑需覆盖）
uv run python -m scripts.database.sync_lottery_from_prod.sync_lottery \
    --source-db-host <生产库地址> --source-db-port 3306 \
    --source-db-user root --source-db-password <密码>

# 只同步 dyndetail 的 lotdata 一张表
uv run python -m scripts.database.sync_lottery_from_prod.sync_lottery --database dyndetail --table lotdata

# 精确镜像（先清空目标表再写入）
uv run python -m scripts.database.sync_lottery_from_prod.sync_lottery --truncate
```

## 5. 边界与风险

1. **生产库只读**：脚本对源库只 `SELECT`，所有写操作只作用于目标库；仍建议先用 `--dry-run` 确认目标库指向本地开发库。
2. **数据量**：全量约数千万行（`t_up_reserve_relation_info` / `t_top_details` / `t_topic_item` 等大表），耗时与批次大小相关，可用 `--database/--table` 缩小范围、`--batch-size` 调整。
3. `max_allowed_packet`：含 LONGTEXT 的表（`bilidyndetail`）批次过大可能报 1153，调小 `--batch-size` 即可。
4. 不同步 `alembic_version`（迁移版本由各库 alembic 自行管理）、不同步 Redis / Milvus。
5. 目标库表结构比源库旧时，缺失列不参与同步（以源库值为准的列才能落库）；列缺失会在日志中体现。

## 6. 验证

1. `--dry-run`：源/目标连通，各表行数统计正确；
2. 本地开发库自同步（源=目标=`localhost:10000`）实跑：upsert 幂等，行数不变，无外键错误；
3. `--database bili_reserve --table t_reserve_round_info` 单表实跑通过；
4. `--table` / `--database` 过滤、`--truncate` 删除顺序、拓扑排序在自同步场景验证。
