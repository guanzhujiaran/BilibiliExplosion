构建docker镜像，需要能访问github的机器。
```bash
docker build -t ghcr.io/guanzhujiaran/bilibiliexplosion .
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
uv run python -m scripts.judge_grand_prize --dry-run

# 正式执行（默认每批200条，仅判断未标记的记录）
uv run python -m scripts.judge_grand_prize

# 自定义批次大小
uv run python -m scripts.judge_grand_prize --batch-size 500

# 强制重新判断所有记录（覆盖已有结果）
uv run python -m scripts.judge_grand_prize --force-update

# 使用本地的gpu ollama 进行判断，保存到服务器端数据库
uv run python -m scripts.judge_grand_prize --force-update --llm-base-url http://localhost:11434/v1 --llm-token ollama --llm-model "modelscope.cn/unsloth/Qwen3.5-4B-GGUF" --db-host 192.168.81.172 --db-port 10000 --db-user root --db-password 114514

## 使用本地的gpu ollama 进行判断，保存到本地数据库
uv run python -m scripts.judge_grand_prize --force-update --llm-base-url http://localhost:11434/v1 --llm-token ollama --llm-model "modelscope.cn/unsloth/Qwen3.5-4B-GGUF" --db-host localhost --db-port 10000 --db-user root --db-password 114514
```

## rawJsonStr 数据回填脚本

从 `t_lotdyninfo.rawJsonStr` 重新解析并全量更新所有字段（替代原有只回填评论转发数的脚本）：

```bash
cd FastapiApp

# 统计有 rawJsonStr 的记录数
uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --count

# 预演模式（查看哪些记录会被更新，不实际写入）
uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --dry-run

# 回填前 N 条（大表建议分批执行）
uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --limit 500

# 回填全部
uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill

uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --force-update --llm-base-url http://localhost:11434/v1 --llm-token ollama --llm-model "modelscope.cn/unsloth/Qwen3.5-4B-GGUF" --db-host 192.168.81.172 --db-port 10000 --db-user root --db-password 114514

```

回填字段包括：
- 互动数据：`commentCount` / `repostCount` / `likeCount`
- 基本信息：`authorName` / `pubTime` / `dynContent` / `dynamicUrl`
- 抽奖类型：`officialLotType` / `officialLotId`（重新判断 官方/充电/预约）
- `isLot`：官方抽奖=1，预约/充电=0，其余用 `extract_is_lot`
- `isManualReply`：转为 0/1 (bool)
- `t_lot_extra_info` 表：`need_comment` / `need_repost`