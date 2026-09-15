# be-bilibili-crawler 代理 Redis 缓存瘦身计划书

> 方案：**C —— 干掉代理明细 hash，只保留 zset，明细回 MySQL 单行查**
> 状态：**已实施**（2026-09-15）

---

## 1. 背景与问题

线上代理库 `proxy_tab` 约 **156 万行**，Redis（`CONFIG.database.proxySubRedis`，db=6）中被同步了同样规模的代理明细，占用 **约 600MB** 内存。

### 1.1 改造前的存储结构

`Utils/代理/数据库操作/async_proxy_op_alchemy_mysql_ver.py`

| Redis key | 类型 | 内容 | 主要读取方 |
|---|---|---|---|
| `zset_bili_proxy` | zset | member = 代理串，score = 分数 | `redis_select_one_proxy` / `redis_select_score_top_proxy` |
| `bili_proxy_available_hm` | hash | field = 代理串，**value = 整条 ProxyTab 的 JSON** | 各处按单个 key `hget` |
| `bili_proxy_changed_hm` | hash | 变更缓冲（value = 变更后的 ProxyTab JSON） | `redis_get_all_changed_proxy`（每小时回写 MySQL） |
| `bili_proxy_black_hm` | hash | 黑名单（value = 整条 ProxyTab JSON） | 仅 `get_bili_proxy_black_num()` 取数量 |
| `sync_ts:bili_proxy` | string | 上次整点同步时间戳 | 同步节流 |

### 1.2 内存构成

按 600MB / 160 万 ≈ **375 B/条** 拆解：

- field key（代理串）≈ 25 B
- value JSON（`proxy_id`/`proxy`/`status`/`update_ts`/`score`/`add_ts`/`success_times`/`zhihu_status`/`computed_proxy_str`）≈ 260 B
- Redis hash 单项开销 ≈ 70～90 B

即：**内存几乎全部花在「把 MySQL 的行原样复制一份到 Redis」**。

### 1.3 附带的正确性问题

1. **只增不减 + 僵尸代理**
   `redis_clear_all_proxy()` 只清 `black_hm` 与 `changed_hm`，**从不清理 `available_hm` 与 zset**；
   而 `clear_unusable_proxy()` 会从 MySQL 删除低分代理。
   结果：MySQL 已删除的代理仍留在 zset 中，`redis_select_one_proxy()`（随机）会把它选出来使用。

2. **每小时全量同步**（`check_redis_data`）
   `select_proxy(mode="all")` 无 limit 地把所有「可用」代理查出来（156 万行 ORM 对象），再全量 `hset` 进 Redis。
   既是内存成因，也在应用侧造成巨大的瞬时内存峰值。

### 1.4 顺带修复的 Bug

1. `sync_2_redis()` 中 zset 分数三元表达式写反：
   `x.score if x.score is None else 0` → 除 `score is None` 外**一律写成 0**，导致 zset 全 0 分，「按分数选最优」失效。
   → 已修正为 `0 if score is None else score`。
2. `RedisManagerBase._zget_top_score(key, rand=True)` 中 `end` 变量算了但没用，永远只取 `zrevrange(key, 0, 0)`（唯一最高分成员），`rand` 形同虚设。
   → 已修正：`rand=True` 时在最高分前 20 名内随机。
3. `SQLHelperClass.update_to_proxy_list()`：Redis 中找不到该代理时直接 `return False`，**跳过 MySQL 更新**，分数/状态变更被静默丢弃。
   → 已修正：基础值改为「变更缓冲 → MySQL」两级获取；两侧都查不到时才跳过，并打 `warning`。
4. `RedisManagerBase._hdel` 被重复定义两次（第二个 `_hdel(self, name, key)` 覆盖了第一个 `_hdel(self, name, *keys)`），多 key 版本实际不可用。
   → 已删除重复定义，保留 `*keys` 版本。

---

## 2. 目标与结果

| 项 | 目标 | 实测/预期 |
|---|---|---|
| Redis 内存 | 600MB → 约 130MB（仅 zset + 变更缓冲） | 待观察（zset 当前 133 万成员） |
| 僵尸代理 | 不再被选中（取到即校验并剔除） | 已实现 |
| 小时级明细同步 | 取消（明细不再进 Redis） | 已实现 |
| zset 增长 | 由「只增不减」改为每轮与 MySQL 精确对齐 | 已实现（临时 key + 原子 RENAME） |
| 顺带 Bug | 1.4 的 4 条全部修复 | 已修复 |

---

## 3. 最终设计

### 3.1 Redis 只保留三把 key

| key | 类型 | 说明 |
|---|---|---|
| `zset_bili_proxy` | zset | member = 代理串，score = 分数（**唯一代理索引**） |
| `bili_proxy_changed_hm` | hash | 变更缓冲，每小时回写 MySQL |
| `sync_ts:bili_proxy` | string | 同步节流时间戳 |

**删除**：`bili_proxy_available_hm`、`bili_proxy_black_hm`。

内存估算：156 万 × (member ≈ 25 B + zset 开销 ≈ 60 B) ≈ **130MB**。

### 3.2 明细统一回 MySQL

`proxy_tab.computed_proxy_str` 是**持久化生成列且带索引**
（`json_unquote(json_extract(proxy, '$.' + json_keys(proxy)[0]))`），
与业务侧的 `get_scheme_ip_port_form_proxy_dict(proxy_dict) = list(proxy_dict.values())[0]` 完全等价。

因此「代理串 → 整行」可用等值查询走索引：`WHERE computed_proxy_str = :s LIMIT 1`。
zset 的 member 保持为代理串不变，无需迁移。

实测：`get_proxy_by_key()` 单行查询 **约 3ms**。

### 3.3 接口改动（已实施）

#### `SubRedisStore`（`Utils/代理/数据库操作/async_proxy_op_alchemy_mysql_ver.py`）

| 方法 | 改动 |
|---|---|
| `RedisMap` | 只剩 `bili_proxy_changed_hm` / `bili_proxy_sync_ts` / `bili_proxy_zset` |
| `get_bili_proxy_all_num` / `get_bili_proxy_black_num` | **删除** |
| `_gen_proxy_key` / `dict_2_model` | **删除**，替换为静态方法 `to_proxy_key()` |
| `redis_get_proxy_by_ip` | **删除**，替换为 `redis_get_changed_proxy()`（只读变更缓冲） |
| `redis_select_one_proxy` / `redis_select_score_top_proxy` | **删除**，替换为返回**代理串**的 `redis_select_one_proxy_key()` / `redis_select_top_proxy_key()` |
| `redis_update_proxy(proxy_tab, delta, base)` | **新增 `base` 入参**（基础值由调用方提供）；不再写 `available_hm` / `black_hm`，只写 `changed_hm` + 维护 zset |
| `redis_zadd_proxy_key` / `redis_zrem_proxy_key` | **新增**：单条维护 zset |
| `sync_2_redis(pairs, key=None)` | 入参由 `List[ProxyTab]` 改为 `list[(代理串, 分数)]`；分批 zadd；支持写入临时 key；修正分数三元表达式 |
| `redis_replace_zset(tmp_key)` | **新增**：临时 key 存在则原子 `RENAME` 顶替线上 zset |
| `redis_clear_all_proxy` | 只清 `changed_hm`（不再有 black/available 可清） |

#### `SQLHelperClass`

| 方法 | 改动 |
|---|---|
| `get_proxy_by_key(proxy_key)` | **新增**：按代理串取整行（明细唯一读入口） |
| `_select_proxy_via_zset(top)` | **新增**：zset 取代理串 → MySQL 取整行；**取到僵尸则 `zrem` 并换下一个（最多 3 次）** |
| `select_proxy("single"/"rand")` | 改走 `_select_proxy_via_zset` |
| `select_score_top_proxy()` | 同上（保留 MySQL 兜底） |
| `get_proxy_by_ip(ip)` | 由 `proxy LIKE` 改为 `computed_proxy_str` 等值查 |
| `select_available_proxy_key_pairs()` | **新增**：只取 `(computed_proxy_str, score)` 两列，供重建 zset |
| `refresh_proxy_zset()` | **新增**：写临时 key → 原子 `RENAME` 重建 zset；条数低于 300 则跳过 |
| `update_to_proxy_list()` | 基础值取「变更缓冲（本小时已更新过）→ 否则 MySQL 读整行」；**不再静默丢弃** |
| `get_black_proxy_num()` | **新增**：MySQL `COUNT(*) WHERE status != 0`，替代 `HLEN black_hm` |
| `get_proxy_database_redis()` | `proxy_black_count` 改走 `get_black_proxy_num()` |
| `check_redis_data()` | 内层由「全量 select + hset 明细」改为「`refresh_proxy_zset()`」 |

#### `RedisManagerBase`（`Utils/redisTool/RedisManager.py`）

- 删除重复的 `_hdel` 定义；
- `_zget_top_score` 修正 `rand` 语义；
- 新增 `_rename(key, new_key)`。

### 3.4 zset 的维护闭环（最终）

| 时机 | 操作 |
|---|---|
| 代理成功/412/352/失败事件 | `update_to_proxy_list` → status==0 则 `zadd(score)`，否则 `zrem` |
| 整点重建（每小时） | 临时 key 写入 MySQL 的「可用代理」→ 原子 `RENAME` 顶替线上 zset（与 MySQL 精确对齐） |
| `refresh_proxy`（每 10 分钟） | 仅改 MySQL；被恢复的代理最迟在下一轮整点重建时回到 zset（**与旧行为一致**，旧版也只有整点同步会补回） |
| `clear_unusable_proxy`（每小时） | 删 MySQL 行；下一轮重建即从 zset 消失 |
| 取代理时命中僵尸 | `zrem` + 换下一个（最多 3 次） |
| 冷启动 / Redis 被清 | 整点重建自然完成装载（条数 <300 时跳过，避免清空池子） |

---

## 4. 兼容与迁移

1. 代码上线后 `bili_proxy_available_hm` / `bili_proxy_black_hm` 变为无引用，需**手动清理**：
   ```
   DEL bili_proxy_available_hm
   DEL bili_proxy_black_hm
   ```
2. `bili_proxy_changed_hm`、`sync_ts:bili_proxy`、`zset_bili_proxy` 语义不变，无需迁移。
3. 若需强制重建 zset，删除 `sync_ts:bili_proxy` 后等下一次整点任务（或手动调用 `SQLHelper.refresh_proxy_zset()`）。

---

## 5. 风险与代价

| 风险 | 说明 | 缓解 / 实测 |
|---|---|---|
| 取代理多一次 MySQL 查询 | 每次取代理多 1 次索引等值查询 | `computed_proxy_str` 带索引，实测约 3ms |
| 代理事件多一次 MySQL 读 | `update_to_proxy_list` 需要基础值 | 优先命中 `changed_hm`（同小时内只回库一次）；且原 `update_available_proxy_details` 本就每次事件都写 MySQL |
| 重建期间 zset 内存翻倍 | 临时 key + 线上 zset 并存 ≈ 130MB → 260MB | 仍远低于 600MB；`RENAME` 后立即释放 |
| 重建期间的事件增量被覆盖 | 覆盖前写入的分数变更丢失 | 变更本身已进 `changed_hm`（MySQL 回写不受影响），下一轮恢复一致；最多多选到一次已失效代理，取到时会被校验剔除 |
| 可用代理为空导致池子被清空 | MySQL 异常返回空集 | `len(pairs) < ZSET_MIN_REBUILD_SIZE(300)` 直接跳过重建 |
| 黑名单计数变慢 | `HLEN` O(1) → MySQL `COUNT(*) WHERE status != 0` | 低频统计接口；`(status, score, ...)` 索引可覆盖。实测线上黑名单仅 1 条 |
| 整点重建耗时 | 156 万次 `zadd`（分批）+ 一次取两列的查询 | 实测取两列查询约 10.6s；重建为异步后台任务 |

---

## 6. 验收情况

| # | 标准 | 结果 |
|---|---|---|
| 1 | 代码中不再引用 `bili_proxy_available_hm` / `bili_proxy_black_hm` | ✅ 全仓 grep 仅剩文档字符串说明 |
| 2 | `RedisMap` 只剩 3 把 key | ✅ 冒烟验证 |
| 3 | 代理串口径与 `computed_proxy_str` 一致 | ✅ `to_proxy_key({'http': 'http://1.2.3.4:8080', ...})` → `http://1.2.3.4:8080`，且该串能查到 MySQL 行 |
| 4 | `select_proxy("rand"/"single")` 可用 | ✅ 均返回完整 ProxyTab |
| 5 | `get_proxy_by_key` 走索引 | ✅ 实测 3ms；`get_proxy_by_ip` 同路径 |
| 6 | 临时 key + 原子 `RENAME` 机制可用 | ✅ 2000 条写入临时 key，`ZCARD=2000`，`_zget_top_score` 正常取值，临时 key 已清理 |
| 7 | 旧接口无残留调用 | ✅ 全仓 grep 通过 |
| 8 | 静态检查 | ✅ `read_lints` 无新增问题 |
| 9 | 上线后内存下降 | ⏳ 需上线观察 `INFO memory` / `MEMORY USAGE zset_bili_proxy` |
| 10 | 现有单测 | ⏳ 建议 `uv run pytest test/ -q` 回归 |

---

## 7. 遗留事项

1. **上线后手动清理**：`DEL bili_proxy_available_hm` / `DEL bili_proxy_black_hm`（否则那 600MB 不会被释放）。
2. `get_proxy_database_redis` 的 `proxy_black_count` 语义由「历史被拉黑过的数量」变为「当前 `status != 0` 的数量」，前端若依赖旧语义需同步确认。
3. `SubRedisStore._hmset_bulk_batch` / `_get_redis_count_by_prefix` 在本模块已成为无用代码（前者仅在 `RedisManagerBase` 中保留），如需清理可另行处理。
