# be-bilibili-crawler 爬虫推送开关计划书

## 1. 背景

当前爬虫只有一处推送开关：`StatsPlugin.push_result`（`Service/BaseCrawler/plugin/statusPlugin.py:31-37`，
在 `GetOthersLotDynRobotConfig` 里以 `PluginConfig("stats_plugin", StatsPlugin, {"push_result": True})` 打开）。
它的语义是「**运行结束且存在最终失败任务时才推**」，而且：

- 插件挂在 `crawler.run()` 上，而 `GetOthersLotDynRobot.main()` 内部会 `run()` 三次（三个阶段），
  挂在这里会导致一轮推三次，不适合做「开始 / 结束」通知；
- 没有「开始」通知；
- 无法按爬虫分别开关；
- 开关写在代码里的 `PluginConfig`，改一次要改代码 + 重新部署。

## 2. 目标

1. 新增「爬虫开始 / 爬虫结束」两个推送触发点；
2. 两个触发点可分别开关；
3. 按爬虫分别开关（`crawler_name` 粒度，`LotteryApiRobot` 的 DYN / RESERVE 两个实例天然区分）；
4. 全部通过环境变量配置；
5. **默认全关**，需要时在环境变量里打开。

## 3. 方案

### 3.1 配置（默认全关）

`CONFIG.py` 新增：

```python
class CrawlerPushConfig(BaseModel):
    """爬虫开始 / 结束推送开关，默认全关。

    值为逗号分隔的爬虫名（crawler_name），支持 ``*`` 通配全部爬虫。
    环境变量示例：
        CRAWLER_PUSH_START=GET_OTHERS_LOT_DYN,GET_DYN
        CRAWLER_PUSH_END=*
    """
    start: str = ""
    end: str = ""
```

挂到 `Settings`：两个顶层字段 `CRAWLER_PUSH_START` / `CRAWLER_PUSH_END`（字符串），
并用 `Settings.crawler_push` 属性解析成 `CrawlerPushConfig` 供代码使用。
选择顶层字段而不是嵌套模型，是因为 `SettingsConfigDict` 没有开 `env_nested_delimiter`，
嵌套字段无法用 `CRAWLER_PUSH__START` 覆盖（实测读不到）。

匹配规则：
- 空字符串 → 关闭；
- `*` → 全部开启；
- 逗号分隔精确匹配 `crawler_name`（大小写敏感，与 `BackgroundServiceName` 枚举值一致）；
- 同时支持用 `all` 作为通配别名（避免某些 shell 里 `*` 需要转义）。

### 3.2 触发点

放在调度器 `Service/BaseCrawler/launcher/scheduler_launcher.py` 的
`BaseScheduler._run_and_save_exec_time()`：

- 进入时：`start` 开关打开 → 推送「`{crawler_name}` 开始执行」，内容含开始时间；
- 正常结束：`end` 开关打开 → 推送「`{crawler_name}` 执行完成」，内容含开始时间 / 结束时间 / 耗时；
- 任务被「杀旧开新」取消：`end` 开关打开 → 推送「执行被终止」；
- 执行抛异常：`end` 开关打开 → 推送「执行失败」，内容带异常信息。

为什么不放在 `StatsPlugin`：见背景，插件按 `run()` 触发，一轮会推多次；
调度器层天然是「一次调度 = 一次开始 / 一次结束」。

为什么不覆盖 HTTP 手动触发（`/get_new_dyn`）：该入口已有自己的轮次总结推送
（`LotUserPoolService.push_round_summary`），再叠一层会重复。

### 3.3 推送实现

复用 `Utils/推送/PushMe.py`：

- 开始：`a_pushme(..., subject=PushSubject.INFO)`
- 成功结束：`a_pushme(..., subject=PushSubject.SUCCESS)`
- 终止 / 失败：`a_push_error(..., topic=PushSubject.FAILURE)`

推送失败只记日志，不允许影响任务本身（`try/except` 包住）。

## 4. 影响面

- 默认全关，行为与改动前一致（不会突然多出推送）；
- 仅新增配置项与两条推送分支，不改任何爬取逻辑。

## 5. 验证

1. 默认（不设环境变量）：跑一轮调度，无开始 / 结束推送；
2. `CRAWLER_PUSH_START=*`：仅开始推送；
3. `CRAWLER_PUSH_END=GET_OTHERS_LOT_DYN`：仅该爬虫的结束推送；
4. 重启容器后 `settings.crawler_push` 读到新值。

## 6. 本地持久化 + 接口修改（补充）

环境变量改一次要重启容器，不适合「临时开一下」的运营动作，因此再加一层运行时覆盖。

### 6.1 存储

- 统一落一个本地 JSON 文件：`{RUNTIME_DIR}/crawler_push_switch.json`；
- `RUNTIME_DIR` 由环境变量指定，容器内为 `/app/runtime`，由 compose 挂载到
  `docker_vol/fastapi/runtime`（生产）/ `docker_vol/fastapi/runtime_dev`（开发），不写进源码树；
- 文件内容（整体覆盖式保存，写入用「临时文件 + os.replace」保证原子性，权限 0644 便于排查）：

```json
{
  "items": [
    {"crawler_name": "GET_OTHERS_LOT_DYN", "start": true, "end": false}
  ],
  "updated_at": 1793848716
}
```

### 6.2 生效优先级

```
文件里有该爬虫的条目 → 用文件值（source=file）
否则                 → 用环境变量（source=env）
两者都没有            → 关闭
```

### 6.3 接口

前缀 `/api/v1/background_service`：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET  | `/BackgroundService/CrawlerPushSwitch` | 查询：文件内容 + 环境变量原值 + 每个爬虫的生效状态与来源 + 文件路径 |
| POST | `/BackgroundService/CrawlerPushSwitch/Set` | 按 `crawler_name` 覆盖写入（body: `{"items":[...]}`），立即生效、重启保留 |
| POST | `/BackgroundService/CrawlerPushSwitch/Delete?crawler_name=xxx` | 删除该爬虫的文件配置，回退到环境变量 |

### 6.4 验证（dev 容器实测）

```
GET  → state_file=/app/runtime/crawler_push_switch.json，effective 全部 false / source=env
POST Set {"crawler_name":"GET_OTHERS_LOT_DYN","start":true,"end":true}
     → effective: start=true end=true source=file，updated_at 写入
重启容器 → effective 仍为 true / source=file   （持久化生效）
POST Delete → effective 回退 false / source=env  （文件条目清空）
宿主机 docker_vol/fastapi/runtime_dev/crawler_push_switch.json 权限 0644，可直接 cat
```
