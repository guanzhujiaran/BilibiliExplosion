# Spec: 管理端 bili-crawler 数据汇总面板

## 1. 目标
在 `/app/admin` 管理后台新增「bili-crawler 数据汇总」面板，按**抽奖类型（lottype / business_type）**维度展示 crawler 侧 `lotdata` 表的汇总统计。

### 必做指标（按抽奖类型分组）
1. **未开奖数**：`lottery_time > now AND status = UNFINISHED(0)` —— 即「还没到开奖时间」的数据量
2. **昨日新增**：`created_at ∈ [今日00:00 − 1d, 今日00:00)`
3. **本周新增**：`created_at >= 本周一 00:00`
4. **本月新增**：`created_at >= 当月1号 00:00`

### 额外指标（本次一并实现）
5. **累计总量** `total`：各类型 `COUNT(*)`
6. **24h内即将开奖** `drawing_soon_24h`：`status=0 AND lottery_time ∈ (now, now+86400]`
7. **待抓开奖结果积压** `pending_result`：`status=0 AND lottery_time <= now AND lottery_result IS NULL`
8. **大奖数量** `grand_prize`：`JOIN t_lot_extra_info ON lottery_id WHERE is_grand_prize=1`
9. **数据新鲜度** `latest_created_at`：全表 `MAX(created_at)`（用于判断爬虫是否在跑）
10. **生成时间** `generated_at`

### 分组口径
只按 **business_type** 分组，覆盖 `LotteryBusinessType`：
- `1` = 官方/转发抽奖（Official）
- `10` = 预约抽奖（Reserve）
- `12` = 充电抽奖（Charge）

话题抽奖（topic，走 CV 抽取）、直播抽奖（live，Redis）、第三方抽奖动态（biliopusdb `t_lotdyninfo`）**不在 `lotdata` 表内**，本次不纳入；作为后续可选扩展记录在 §7。

## 2. 影响范围（精确文件清单）

### 后端 `be-bilibili-crawler`
| 文件 | 改动 |
|---|---|
| [ApiRoutes/\_\_init\_\_.py](file:///home/minato/BilibiliExplosion/be-bilibili-crawler/ApiRoutes/__init__.py) | `RouterPaths` 增加 `GET_LOTTERY_DATA_SUMMARY = "/GetLotteryDataSummary"`（插在 `GET_OTHERS_LOT_DYN_DETAIL` 之后，L115 附近，归入「获取类路由」注释块）；`RouterNames` 增加 `GET_LOTTERY_DATA_SUMMARY = "get_lottery_data_summary"`（对应位置 L220 附近） |
| [Models/lottery_database/bili/LotteryDataModels.py](file:///home/minato/BilibiliExplosion/be-bilibili-crawler/Models/lottery_database/bili/LotteryDataModels.py) | 文件末尾新增响应模型 `LotteryTypeSummary` 与 `LotteryDataSummaryResp`（pydantic `BaseModel`） |
| [Service/GrpcModule/GrpcSrc/SQLObject/DynDetailSqlHelperMysqlVer.py](file:///home/minato/BilibiliExplosion/be-bilibili-crawler/Service/GrpcModule/GrpcSrc/SQLObject/DynDetailSqlHelperMysqlVer.py) | `SQLHelper` 类内新增 `async def get_lottery_data_summary(self)`（沿用 `async_session()` + `@log_sql_retry_wrapper()` 模式，参考已有聚合方法写法） |
| [controller/v1/lotttery_database/bili/LotteryData.py](file:///home/minato/BilibiliExplosion/be-bilibili-crawler/controller/v1/lotttery_database/bili/LotteryData.py) | 新增 `@router.get(RouterPaths.GET_LOTTERY_DATA_SUMMARY, ...)` → `api_GetLotteryDataSummary(t: NoCacheTs = None)`，返回 `CommonResponseModel[LotteryDataSummaryResp]`。**不加 `@cache`**（管理端要求实时）。 |

### 前端 `Vue3FrontEndDemoExercise`
| 文件 | 改动 |
|---|---|
| [src/api/lottery_data/bili/lottery_database_bili_api.ts](file:///home/minato/BilibiliExplosion/Vue3FrontEndDemoExercise/src/api/lottery_data/bili/lottery_database_bili_api.ts) | 新增 `getLotterySummary()`，用 raw client `client.get({url:'/api/v1/lottery_database/bili/GetLotteryDataSummary', query:{t:Date.now()}})`，返回 `RootObject<LotteryDataSummaryResp>` |
| `src/views/admin/BiliCrawlerSummaryView.vue`（**新建**） | 汇总页面：顶部统计卡片 + 分类型 `el-table`（含「合计」行）。样式参考 `BrowserQuotaView.vue` / `AdminOverview.vue`（plain div + tailwind-like class + el-*），用 `biliMessage` 报错、含 loading 态 |
| [src/router/index.ts](file:///home/minato/BilibiliExplosion/Vue3FrontEndDemoExercise/src/router/index.ts) | ADMIN children 增加路由 `path:'bili-crawler-summary'`, `name:'AdminBiliCrawlerSummary'`, `component: BiliCrawlerSummaryView`, `meta:{title:'数据汇总', requiresAdmin:true, hidden:true}` |
| [src/views/admin/AdminLayout.vue](file:///home/minato/BilibiliExplosion/Vue3FrontEndDemoExercise/src/views/admin/AdminLayout.vue) | 导航菜单新增一项指向上述路由（Element Plus 图标 `DataAnalysis`） |
| [src/views/admin/AdminOverview.vue](file:///home/minato/BilibiliExplosion/Vue3FrontEndDemoExercise/src/views/admin/AdminOverview.vue) | （可选，低风险）概览页加入口卡片/链接 |

## 3. 接口契约

`GET /api/v1/lottery_database/bili/GetLotteryDataSummary?t=<ms>`

- 鉴权：沿用 `be-gateway` 对该前缀的 `jwtAuthOptional`（登录可选），与兄弟接口一致；管理可见性由前端路由 `requiresAdmin` 控制。
- 缓存：`@cache` 不启用；响应头沿用项目既有的 no-store 处理（不新增）。

响应（`CommonResponseModel` 包一层 `{code,msg,data}`）：
```jsonc
{
  "generated_at": 1760000000,        // 服务端 unix 秒
  "latest_created_at": 1759999999,   // 可为 null
  "types": [
    {
      "business_type": 1,
      "type_name": "官方抽奖",
      "total": 123,
      "not_drawn": 45,
      "drawing_soon_24h": 8,
      "pending_result": 3,
      "grand_prize": 2,
      "new_yesterday": 10,
      "new_this_week": 66,
      "new_this_month": 300
    }
    // 10 预约抽奖, 12 充电抽奖 同结构；即使计数为 0 也必须出现
  ]
}
```

## 4. 计算口径（后端 SQL）

**主查询（单次 GROUP BY，索引友好）**：对 `lotdata` 按 `business_type` 分组，用 `func.sum(case(...))` 一次算出 `total / not_drawn / drawing_soon_24h / pending_result / new_yesterday / new_this_week / new_this_month`。

时间边界用服务端本地时区（Asia/Shanghai），与既有代码保持一致：以 `datetime.datetime` 计算「今日0点 / 本周一0点 / 当月1号0点」，再转 unix 秒参与 SQL 比较。

**第二查询**：`lotdata JOIN t_lot_extra_info`（`lottery_id` 相等，`is_grand_prize=1`）按 `business_type` 分组 `COUNT(*)`，得到 `grand_prize`。

**第三查询**：全表 `MAX(created_at)`。

**组装**：固定遍历 `[Official(1), Reserve(10), Charge(12)]`，从字典取结果，缺省补 0，保证 3 个类型齐全；`type_name` 用固定中文名（官方抽奖 / 预约抽奖 / 充电抽奖）。累计/合计行由前端对 `types` 求和得到（后端不返回 totals，保持简单）。

## 5. 验证步骤
1. 后端语法：`cd be-bilibili-crawler && python -m py_compile controller/v1/lotttery_database/bili/LotteryData.py Models/lottery_database/bili/LotteryDataModels.py Service/GrpcModule/GrpcSrc/SQLObject/DynDetailSqlHelperMysqlVer.py ApiRoutes/__init__.py`（用项目 `.venv`）
2. 若本地 DB 可用：直接调 `GET .../GetLotteryDataSummary`，确认 3 类型齐全、数值与库内 `SELECT COUNT(*) ...` 抽样一致。
3. 前端类型检查：`cd Vue3FrontEndDemoExercise && npx vue-tsc --noEmit`（或 `npm run build` 的等价脚本，先看 `package.json`）。
4. 路由/菜单：dev 起服务访问 `/app/admin/bili-crawler-summary`，确认需登录管理员、卡片与表格渲染正常、错误走 `biliMessage`。

## 6. 需要用户确认 / 已定决策
- **[需批准]** 是否按上述方案执行（尤其：额外 5 项指标是否都要、是否只在 `/app/admin` 内可见）。
- 已定：分组口径 = 仅 `business_type`(1/10/12)；「新增」以 DB `created_at`（收录时间）为准；接口保持与兄弟接口同级鉴权（登录可选），不做后端管理员强校验。
- 已定：`AdminOverview.vue` 的概览卡片为可选，默认实现。

## 7. 本次不实现（后续可选扩展）
- 话题抽奖 / 直播抽奖 / 第三方动态抽奖 的同类统计（数据源在独立存储，需另接）。
- 趋势图（近 N 天每日新增折线）、各类型「参与人数」分布、即将开奖 Top N 明细列表、爬虫健康度联合展示。
- 定时快照/历史对比（需新增快照表或缓存层）。
