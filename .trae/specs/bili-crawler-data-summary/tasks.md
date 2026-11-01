# Tasks: 管理端 bili-crawler 数据汇总面板

> 依赖 Spec: [spec.md](./spec.md)。执行前需用户批准。

- [ ] T1 后端路由常量
  - 文件：`be-bilibili-crawler/ApiRoutes/__init__.py`
  - 改动：`RouterPaths.GET_LOTTERY_DATA_SUMMARY="/GetLotteryDataSummary"`；`RouterNames.GET_LOTTERY_DATA_SUMMARY="get_lottery_data_summary"`
  - 验证：`python -m py_compile ApiRoutes/__init__.py`

- [ ] T2 响应模型
  - 文件：`be-bilibili-crawler/Models/lottery_database/bili/LotteryDataModels.py`（末尾）
  - 改动：新增 `LotteryTypeSummary`、`LotteryDataSummaryResp`（字段见 spec §3）
  - 验证：`py_compile`

- [ ] T3 SQL 汇总方法
  - 文件：`be-bilibili-crawler/Service/GrpcModule/GrpcSrc/SQLObject/DynDetailSqlHelperMysqlVer.py`
  - 改动：`SQLHelper.get_lottery_data_summary(self)`：主 GROUP BY 聚合 + 大奖 JOIN 查询 + MAX(created_at)；固定 1/10/12 类型补 0
  - 验证：`py_compile`；有 DB 时抽样核对

- [ ] T4 接口
  - 文件：`be-bilibili-crawler/controller/v1/lotttery_database/bili/LotteryData.py`
  - 改动：新增 `api_GetLotteryDataSummary`（GET，`NoCacheTs`，无 `@cache`，`response_model=CommonResponseModel[LotteryDataSummaryResp]`）
  - 验证：`py_compile` \+ 实际请求

- [ ] T5 前端 API 方法
  - 文件：`Vue3FrontEndDemoExercise/src/api/lottery_data/bili/lottery_database_bili_api.ts`
  - 改动：`getLotterySummary()` → raw `client.get` 带 `t`
  - 验证：`vue-tsc --noEmit`

- [ ] T6 汇总视图
  - 文件：新建 `Vue3FrontEndDemoExercise/src/views/admin/BiliCrawlerSummaryView.vue`
  - 改动：统计卡片 + 分类型 `el-table`（含合计行）+ loading + `biliMessage` 错误处理
  - 验证：build/type check

- [ ] T7 路由注册
  - 文件：`Vue3FrontEndDemoExercise/src/router/index.ts`
  - 改动：ADMIN children 加 `bili-crawler-summary`，`meta.requiresAdmin=true, hidden:true`
  - 验证：访问 `/app/admin/bili-crawler-summary`

- [ ] T8 导航入口
  - 文件：`Vue3FrontEndDemoExercise/src/views/admin/AdminLayout.vue`
  - 改动：新增菜单项（icon `DataAnalysis`）
  - 验证：菜单可见、点击跳转

- [ ] T9（可选）概览页入口
  - 文件：`Vue3FrontEndDemoExercise/src/views/admin/AdminOverview.vue`
  - 改动：加入口卡片/链接
  - 验证：跳转正常

- [ ] T10 验证与汇报
  - 后端 `py_compile`；前端 `vue-tsc --noEmit`；如可运行则端到端看一眼
  - 中文汇报：改动文件链接 + 未实现的后续可选扩展（spec §7）
