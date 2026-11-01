# RPA 工作流「调度外壳」改造计划书

> 关联：`docs/be-message-统一计划书.md`（5.7 RPA 扩展位 / 5.14 RPA 浏览器实例监管）
> 涉及仓库：`RPA-Browser`（主）、`Vue3FrontEndDemoExercise`（前端）、be-message（推送消费，仅复用既有链路）

## 1. 背景与结论

### 1.1 现状问题

当前前端「新建工作流」弹窗（`src/components/rpa-browser/WorkflowEditDialog.vue`）内嵌了 `DebugBox` 步骤编辑器，保存时先
`createCustomAction/updateCustomAction` 再 `createWorkflow/updateWorkflow`。这带来三个问题：

1. **语义错位**：工作流表 `UserWorkflow` 根本没有 `steps` 字段，步骤真实存放在 `CompositeActionModel.steps`，工作流只持有
   `custom_action_id`。在弹窗里编辑步骤，等于把 action 编辑器复制一份到工作流层。
2. **副作用错位**：保存工作流会以「工作流的名称/描述」在动作库里创建或**覆盖**一个复合操作，污染动作库，并可能覆盖被其他
   资源引用的 action。
3. **缺关键入口**：无法引用「已经调试好的、已有的 action」，用户只能每次重新搭建步骤。

同时后端 `trigger_type/trigger_config` 只是**声明性字段**：`app/scheduler_manager.py` 目前唯一的注册点是
`app/setup.py`（会话清理），没有任何代码读 `UserWorkflow.trigger_type` 去注册定时任务；`UserWorkflow` 也**没有执行目标
浏览器**，无人值守的定时任务无法落地。

### 1.2 结论（本计划书的定位口径）

**工作流 = 调度外壳。** 它只负责：

| 职责 | 说明 |
| --- | --- |
| 引用动作 | `custom_action_id` → 指向一个已存在的复合操作；**action 是多对一共享资产**，工作流不得改写 action 内容 |
| 触发配置 | `trigger_type = manual / cron` + `trigger_config.cron` |
| 执行目标 | `browser_id`（定时运行必须有稳定目标） |
| 发布与启用 | `is_public` / `is_enabled`（沿用既有审批与社区互动） |
| 运行观测 | 上次/下次运行时间、运行记录、失败推送 |

**工作流不提供自己的步骤编辑器（调试界面）。** 步骤编辑与调试归 action 侧，已由
`BrowserStream.vue`（LiveBox 实时画面 + DebugBox 调试面板 + ToolboxPanel 工具箱）与
`EditCustomActionDialog.vue` 完整承担。工作流侧只保留「立即运行一次看结果」的能力。

## 2. 数据模型变更（RPA-Browser）

### 2.1 `UserWorkflow` 增字段

文件：`app/models/database/workflow/models.py`

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `browser_id` | `int \| None` | `None` | 执行目标浏览器；`cron` 触发时必填 |
| `last_run_at` | `datetime \| None` | `None` | 上次运行结束时间 |
| `last_run_status` | `str \| None` | `None` | `running / success / failed` |
| `next_run_at` | `datetime \| None` | `None` | 下次计划运行时间（由 cron 推导并落库，仅为展示与排障） |

`trigger_type` 取值约定统一为 **`manual` / `cron`**（与 `WorkflowCreateRequest` 注释一致）。既有 `TriggerType`
枚举（`manual/scheduled/event`）与未启用的 `WorkflowRecord` 表保持原样不动。

### 2.2 新增 `WorkflowRunRecord`（工作流运行记录）

文件：`app/models/database/workflow/models.py`（表名 `workflowrunrecord`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `int` PK | |
| `run_id` | `str(64)` unique | 运行唯一标识 |
| `workflow_id` | `str(100)` index | 关联工作流 |
| `mid` | `str(255)` index | 触发者（定时任务为工作流所有者） |
| `browser_id` | `str(100)` | 本次执行目标浏览器 |
| `trigger_source` | `str(20)` | `manual` / `schedule`（避免 MySQL 保留字 `trigger`，故加 `_source`） |
| `status` | `str(20)` index | `running` / `success` / `failed` |
| `total` / `success_count` / `failed_count` | `int` | 步骤统计 |
| `execution_id` | `str(64)` index | 关联 `ActionLogRecord.execution_id`，可下钻到步骤级日志 |
| `error_message` | `str(2000)` | 失败原因 |
| `duration_ms` | `float` | 总耗时 |
| `started_at` / `finished_at` | `datetime` | |
| `notified` | `bool` | 失败推送是否已发出（防重复） |

说明：步骤级明细仍复用既有 `ActionLogRecord`（其 `source=workflow`、`workflow_id` 由
`ExecutionEngine.execute_steps` 自动写入，见 `app/services/execution/engine.py:147-176`）。
`WorkflowRunRecord` 只承担「一次运行」的聚合视图，**不受 action 的 `log_enabled` 影响**。

### 2.3 迁移

新增 alembic 迁移：`userworkflow` 加 4 列 + 建 `workflowrunrecord` 表。启动时
`run_alembic_upgrade_head()` + `check_schemas()` 会自动校验，模型与库不一致会拒绝启动。

## 3. 后端服务改造

### 3.1 CRUD（`app/services/execution/crud_service/workflow_crud.py`）

- `create/update/duplicate/fork` 增加 `browser_id` 透传（fork 保持 `browser_id=None`，避免跨用户指向他人浏览器）。
- 新增 `list_scheduling()`：取所有 `is_enabled = true` 且 `trigger_type = 'cron'` 且 `browser_id is not null` 的工作流，供启动时重建任务。
- 新增 `update_run_state(id, status, last_run_at, next_run_at)`。
- 新增 `WorkflowRunCrudService`（新文件 `workflow_run_crud.py`）：`create_running / finish / list_by_workflow / count_by_workflow`。

### 3.2 调度器（新文件 `app/services/execution/workflow_scheduler.py`）

- `sync_workflow_job(workflow)`：按 `is_enabled + trigger_type + cron + browser_id` 决定注册 / 移除 job。
  任务 ID 固定为 `workflow:{workflow_id}`，`replace_existing=True`。
- `remove_workflow_job(workflow_id)`：删除 / 禁用 / 改手动触发时调用。
- `register_all_workflow_jobs()`：`app/setup.py` 启动时调用（在 `scheduler_manager_ist.start()` 之前）。
- `compute_next_run(cron)`：用 `apscheduler.triggers.cron.CronTrigger` 推导下次触发时间，供 `next_run_at` 展示。
- job 回调 `run_workflow_job(workflow_id)`：查库 → 组装执行上下文 → 调用 3.3 的 runner；异常全捕获，不能影响调度线程。

### 3.3 执行器（新文件 `app/services/execution/workflow_runner.py`）

`run_workflow(workflow, *, trigger, mid, browser_id=None)`：

1. 校验 `custom_action_id` 存在且 action 未禁用；否则记 `failed` 并提前返回。
2. 目标浏览器：`trigger='schedule'` 用工作流上的 `browser_id`；`manual` 优先用入参。
3. 取会话：`live_service.get_or_create_browser_session_entry(mid, browser_id, headless=True)`
   —— 定时运行允许**自动拉起会话**；随后 `_resolve_page` 取当前页。
4. 归一化 steps（复用 `execution_router` 中 `workflow_step_adapter` 的既有写法）。
5. 调 `execution_engine.execute_steps(..., workflow_id=..., plugins=...)`，拿到逐步结果。
6. 落 `WorkflowRunRecord`（`execution_id` 与引擎日志同批次），更新 `UserWorkflow.last_run_at / last_run_status / next_run_at`。
7. **失败判定口径（运行结论）**：只有「**未被 `on_error=continue` 容忍的失败**」与「**未知异常**」
   才把整次运行判为 `failed`：
   - Pipeline 在按 `on_error=continue` 跳过某步骤时，给该步骤的 `ActionResult.tolerated = True`；
     被容忍的失败**仍计入 `failed_count`**、仍出现在运行消息与步骤日志里（便于排查），
     但**不参与运行结论**；
   - 未知异常（Pipeline 的 `except Exception` 兜底）与 `on_error=stop`（默认，含重试耗尽）
     产生的失败不带 `tolerated` 标记，判 `failed`，并按下面第 8 条推送失败通知；
   - 例：选择器未命中的 `get_text` 配了 `on_error=continue` → 后续步骤照常执行，运行结论仍为
     `success`（`failed_count > 0` 只作为「过程有瑕疵」的展示信息）。
8. 判失败时经既有推送链路通知：取
   `BrowserService(mid).get_notification_config(session, browser_id)`，
   `push_msg.send("[f]工作流执行失败: {name}", 摘要, config)`；通知失败只告警不抛出。

### 3.4 路由（`app/controller/v1/browser_control/execution/workflow_router.py`）

| 新接口 | 路径 | 说明 |
| --- | --- | --- |
| 立即运行 | `POST /workflows/run` | body `{id}`；`verify_browser_ownership` 取运行时会话，等价手动触发一次并写运行记录 |
| 运行记录列表 | `POST /workflows/runs` | body `{workflow_id, page, per_page}` |
| 运行记录详情 | `POST /workflows/runs/get` | body `{run_id}`，附 `execution_id` 供前端下钻步骤日志 |

既有接口变更：

- `create/update`：接受并校验 `browser_id`；写库后调用 `sync_workflow_job` / `remove_workflow_job`。
- `delete`：先 `remove_workflow_job`。
- 定时触发校验：`trigger_type == 'cron'` 时 `trigger_config.cron` 必填、必须能被 `CronTrigger` 解析、
  且 `browser_id` 必填；不满足返回 400 业务错误。
- `WorkflowListItemResponse/WorkflowDetailResponse` 增加 `browser_id / trigger_type / trigger_config / last_run_at / last_run_status / next_run_at`。

### 3.5 启动注册

`app/setup.py::register_background_tasks()` 追加 `await register_all_workflow_jobs()`（内部自行处理异常，
DB 不可用时不阻塞启动）。

## 4. 前端改造（Vue3FrontEndDemoExercise）

### 4.1 `WorkflowEditDialog.vue` 重写为「配置面板」

移除：`DebugBox`、`ToolboxPanel`、`EditCustomActionDialog`、本地步骤编辑与「保存前先建 action」的双步保存。

保留/新增：

- 元信息：名称、描述、公开、启用。
- **动作选择**：新增 `ActionPickerDialog.vue`（可复用 `ToolboxPanel` 的列表与筛选能力，单选返回 `action_id`），
  选中后**只读展示**步骤数量与摘要（复用 `ActionCard`），并提供「去调试」入口跳转 `BrowserStream` 对应动作。
- 触发配置：手动 / 定时（cron 表达式 + 前端基础格式校验 + 后端返回的 `next_run_at` 展示）。
- 目标浏览器：复用现有 `listFingerprintRouter...` 列表；定时触发时必填。
- 保存：仅调用 `createWorkflow / updateWorkflow`，**不再写 action 库**。
- 运行：**「立即运行」放在列表卡片上**（`workflows/run` 需要已落库的工作流 id，弹窗内的新建态无法运行），
  运行后自动打开「运行记录」查看明细。弹窗内提供「去调试页」跳转 `BrowserStream` 做动作侧调试。

### 4.2 `WorkflowManagement.vue`

- 卡片：展示触发方式（手动 / 定时 + cron）、上次运行、下次运行、上次状态。
- 操作栏：新增「立即运行」「运行记录」；「运行记录」打开弹窗（`WorkflowRunLogDialog.vue`），
  列表展示 `WorkflowRunRecord`，带步骤明细下钻（`execution_id` → 既有操作日志接口）。
- 定时任务在未配置浏览器时给出显式提示，不允许保存为定时。

### 4.3 规则遵循

- 组件全部走 Tailwind 语义化主题类，不写 `<style>`、不用 `:style`；
- 不使用 `size="small"`，统一 default/large；
- 所有外链跳转走 `@/utils/PageOpen/linkPolicy`。

## 5. 兼容与迁移

- 存量工作流：`browser_id` 为空 → 定时任务不注册（保持只能手动运行），前端在编辑时提示补全。
- 存量「工作流 + 自动创建的同名 action」数据不清理：改为引用关系后，工作流仍指向原 action，行为不变。
- 移除前端自动建 action 后，`WorkflowEditDialog` 不再写 `CompositeActionModel`，动作库不再被工作流污染。

## 6. 实现记录（本次已落地）

### 后端（RPA-Browser）
- `app/models/database/workflow/models.py`：`UserWorkflow` +4 字段；新增 `WorkflowRunRecord`、`WorkflowRunStatusEnum`、`WorkflowRunTriggerEnum`
- `alembic/versions/b71f3c9a4d02_workflow_scheduling_shell.py`：迁移（已执行 `upgrade head`，`check_schemas()` 通过）
- `app/models/execution/request_params.py`：`ExecutionRequest` 增加 `execution_id`（调度侧预生成，与运行记录 1:1 关联）
- `app/services/execution/workflow_runner.py`（新）：手动/定时共用执行器 + 失败推送
- `app/services/execution/workflow_scheduler.py`（新）：任务同步 / 启动重建 / 下次运行推导
- `app/services/execution/crud_service/workflow_run_crud.py`（新）+ `workflow_crud.py`（`browser_id`、`list_scheduling`、`update_run_state`）
- `app/controller/v1/browser_control/execution/workflow_router.py`：触发校验、调度同步、`/workflows/run`、`/workflows/runs`、`/workflows/runs/get`
- `app/setup.py`：启动时 `register_all_workflow_jobs()`
- 顺带修复：`workflow_crud.py` 使用 `sqlalchemy.update` 却未导入（导致 `fork` / `enable` / `disable` / 带 `forked_from_id` 的 `delete` 必崩）

### 前端（Vue3FrontEndDemoExercise）
- `src/components/rpa-browser/WorkflowEditDialog.vue`：重写为配置面板（移除 `DebugBox` / `ToolboxPanel` / `EditCustomActionDialog` 与自动建 action 逻辑）
- `src/components/rpa-browser/ActionPickerDialog.vue`（新）：动作选择器
- `src/components/rpa-browser/WorkflowRunLogDialog.vue`（新）：运行记录 + 步骤日志下钻
- `src/views/rpa-browser/WorkflowManagement.vue`：卡片展示触发/上次/下次运行，新增「立即运行」「运行记录」
- SDK 由 `vite.config.ts` 的 hey-api 插件从 `http://localhost:28000/openapi.json` 重新生成（已同步）

## 7. 验收清单

1. 新建工作流：选择已有 action → 定时 `*/5 * * * *` + 选目标浏览器 → 保存成功，工作流详情能看到 `next_run_at`。
2. 停止/禁用/改手动：对应 job 从调度器移除（`scheduler_manager_ist.get_jobs()` 中不再有 `workflow:{id}`）。
3. 到点自动执行：浏览器未启动时能自动拉起会话并执行；`WorkflowRunRecord` 生成 `success` 记录。
4. 失败场景（action 不存在 / 步骤报错）：记录 `failed`，且推送通知到达（未配置通知时不报错）。
5. 「立即运行」：写入 `trigger=manual` 的运行记录并返回逐步结果。
6. 编辑工作流**不会**改变其引用的 action 内容（多对一共享）。
7. 多个工作流引用同一 action，各自触发互不影响。

## 8. 浏览器详情页与「关联的工作流」（2026-10 增量）

### 8.1 需求

工作流列表卡片展示「目标浏览器」后，需要反向入口：

1. 点击工作流卡片上的目标浏览器标签 → 进入**浏览器详情页`；
2. 浏览器详情页展示该浏览器指纹的基本信息，并列出**关联的工作流**（`UserWorkflow.browser_id` 指向该浏览器的工作流），便于用户从浏览器视角排查「这个浏览器被哪些工作流使用」。

### 8.2 后端（RPA-Browser）

- `WorkflowListRequest`（`app/models/workflow/models.py`）新增可选过滤字段 `browser_id: int | None`。
- `WorkflowCrudService.list_by_user / count_by_user`（`app/services/execution/crud_service/workflow_crud.py`）新增同名关键字参数，非 None 时追加 `UserWorkflow.browser_id == browser_id` 条件，与既有 `filter_type` 条件叠加。
- `list_workflows`（`app/controller/v1/browser_control/execution/workflow_router.py`）透传 `request.browser_id`。
- 响应结构不变（仍为 `BasePaginationResp[WorkflowListItemResponse]`，`browser_id` 字段 3.4 节已补齐）。

### 8.3 前端（Vue3FrontEndDemoExercise）

- 新增路由 `detail/:browserId`（`RouteName.RPA_BROWSER_DETAIL`），组件 `src/views/rpa-browser/BrowserDetail.vue`：
  - 浏览器基本信息：复用 `readFingerprintRouter...` 只读展示（名称 / ID / 浏览器 / 平台 / 版本 / 代理 / 创建更新时间）；
  - 关联工作流：调用 `listWorkflows...`（`filter_type: 'all'` + `browser_id`）分页展示，含触发方式、启用状态、上次运行状态，空列表给出空态；
  - 「返回」回到浏览器指纹列表页。
- `WorkflowManagement.vue`：目标浏览器标签（`workflow-card__browser`）可点击，跳转上述详情页。
- 规则遵循：顶层路由组件单根；无 `<style>` / `:style`；列表内部滚动用 `BiliScrollbar` + 分页吸底；图标用 `assets/svgs` 资源。

### 8.4 验收

1. 工作流卡片点击目标浏览器标签 → 进入详情页，URL 带 `browserId`。
2. 详情页展示浏览器基本信息；「关联的工作流」只列出 `browser_id` 指向该浏览器的工作流。
3. 浏览器无关联工作流时展示空态，不报错。
4. 详情页可直接返回指纹列表页；从其他入口（指纹列表 → Stream）进入详情页同样可用。
5. 后端 OpenAPI 变更后前端 SDK 已重新生成（`WorkflowListRequest.browser_id` 类型可用）。

## 9. 工作流执行日志开关与 7 天保留（2026-10 增量）

### 9.1 背景与问题

1. **工作流执行不记录步骤日志**：`run_workflow` 构造执行请求时 `variables={}`，步骤参数不携带
   `log` 选项；内置步骤回落到服务端兜底 `settings.action_log_default_enabled`（默认 `False`），
   自定义复合步骤回落到 `CompositeActionModel.log_enabled`（默认 `False`）。三级开关全部落空 →
   `save_action_log` 直接 return，`action-logs/list` 永远为空。计划书 §2.2 注释中「由
   execute_steps 自动写入」的表述因此不成立（实际受采集开关控制）。
2. **日志无保留策略**：`ActionLogCrudService.cleanup_expired()` 已实现但**从未被调度**，
   `action_log_default_retention_days` 默认 30 天也不会真正生效，日志表只增不减，硬盘扛不住。

结论：日志采集的最终决定权应交回用户——**在工作流上提供「是否记录执行日志」开关**；
同时把全局保留策略收紧为 **7 天**并真正落地周期清理。

### 9.2 数据模型变更（RPA-Browser）

文件：`app/models/database/workflow/models.py`，两处日志开关列改为**三态**（`bool | None`）：

| 模型 | 字段 | 类型 | 取值语义 |
| --- | --- | --- | --- |
| `UserWorkflow` | `log_enabled` | `bool \| None`，默认 `None` | `None`=未设置（听从动作/项目）；`True/False`=本次运行显式开/关 |
| `CompositeActionModel` | `log_enabled` | `bool \| None`，默认 `None` | `None`=未设置（听从工作流/项目）；`True/False`=该复合动作显式开/关 |

迁移：
- `20261016_wf_log_enabled`：`userworkflow` 加 `log_enabled` 列；
- `20261016_log_switch_tristate`：两列改为可空，并把存量 `false` 一律置为 `NULL`
  （存量数据视为「未设置」，避免旧默认值把项目级兜底永久压死）。

### 9.3 采集开关优先级（项目 / 工作流 / 动作）

`resolve_log_option`（`app/services/execution/action_logger.py`）按**从具体到兜底**的顺序解析，
任一级显式取值（`True/False`）即终止链；`None`（未设置）继续向下：

| 优先级 | 开关 | 作用域 | 说明 |
| --- | --- | --- | --- |
| 1（最高） | 执行参数 `log`（`BaseActionParams.log`） | 单次执行的某步骤 | 调试/一次性场景；`enabled` 显式开/关 |
| 2 | **工作流开关** `UserWorkflow.log_enabled` | 一次工作流运行的全部步骤（含嵌套子步骤） | 工作流是「运行容器」，其开关是本次运行的总闸：显式开→全记，显式关→全不记，压制动作级与项目级 |
| 3 | **动作开关** `CompositeActionModel.log_enabled` | 单个复合动作 | 工作流未设置时生效；单操作执行（`/actions/execute`）直接走这一级 |
| 4（兜底） | **项目开关** `settings.action_log_default_enabled` | 全局 | 前面都未设置时的最终兜底（内置操作也回落至此） |

字段级配置（`record_params / record_result / record_variables / only_on_error /
max_payload_length / retention_days`）仍取自动作自身配置，缺失时用兜底默认值；
工作流开关只决定 `enabled`，不覆盖字段级配置。

### 9.4 后端改造

1. **请求/响应模型**（`app/models/workflow/models.py`）：
   - `WorkflowCreateRequest` / `CustomActionCreateRequest` 的 `log_enabled` 默认 `None`（未设置）；
   - `WorkflowUpdateRequest` / `CustomActionUpdateRequest` `log_enabled: bool | None`，
     不传（`None`）表示不修改；
   - 响应体 `log_enabled` 同步为 `bool | None`（导出 JSON 可携带 `null`，导入后仍是未设置）。
2. **CRUD**（`workflow_crud.py` / `action_crud.py`）：
   - `create / update / duplicate / fork` 透传 `log_enabled`；`action_crud.create` 默认参数改为 `None`。
3. **执行链路透传**（`app/services/execution/engine.py` + `workflow_runner.py`）：
   - `execute_steps(..., workflow_log_enabled: bool | None = None)` → executor → `_run_action`
     → `_run_action_core` → `resolve_log_option(mid, action_id, merged, ctx_log_config, workflow_log_enabled)`；
   - `run_workflow` 直接传 `workflow_log_enabled=workflow.log_enabled`（不再构造 `ActionLogOption`）；
   - 复合操作子步骤经 `exec_meta["log_config"]` 继承已解析的最终配置，嵌套步骤一并生效；
   - 单操作执行（`/actions/execute`）不传工作流开关，行为不变。
4. **保留 7 天 + 周期清理**（`app/config.py` + `app/setup.py`）：
   - `action_log_default_retention_days` 默认 `30` → `7`；
   - 新增配置 `action_log_cleanup_interval`（秒，默认 86400）；
   - `register_background_tasks()` 注册间隔任务 `action_log_cleanup`，调用既有
     `ActionLogCrudService.cleanup_expired()`（幂等删除，失败仅告警不阻塞调度）。
5. **MQ 落库（防丢 + 不阻塞执行线程）**（`app/config.py` / `bili_common/core/log_pub.py` /
   `action_logger._persist` / `main.py`）：
   - `action_log_use_mq` 默认 `False` → `True`：日志默认走 RabbitMQ 异步落库，
     不再在 RPA 执行协程里同步写库（投递是 fire-and-forget，复用共享连接）；
   - `publish_action_log` 增加 `persist=True`：消息持久化 + 消费端 durable 队列，
     RabbitMQ 重启不丢日志（此前未设置持久化，属于丢日志缺口）；
   - 消费端沿用：`log_id` 唯一键幂等落库 + 3 次指数退避重试 + 兜底失败记录，异常绝不冒泡；
   - `_persist` 增加**熔断**：投递失败后 30 秒内直接走同步直写，避免队列不可用时
     每条日志都触发一次建连等待拖死执行线程；恢复后自动回到 MQ；
   - `main.py` 消费端启动包 try/except：启动失败仅告警降级（发布端会自动回落同步直写），
     不阻塞服务启动；停机时 `stop_log_consumer` 幂等。

### 9.5 前端改造（Vue3FrontEndDemoExercise）

`src/components/rpa-browser/WorkflowEditDialog.vue`：

- 新增「执行日志」配置区：`el-switch` 控制「记录执行日志」，附说明（记录步骤入参/结果/耗时，
  仅保留最近 7 天，可在运行记录中按 `execution_id` 下钻查看）；
- 编辑态从 `workflowDetail.log_enabled` 回显（`null` 视为关），新建态默认 `false`；
- 保存体 `create/update` 携带 `log_enabled`（布尔值 = 显式开/关；body 为
  `Record<string, unknown>`，不受 SDK 生成时序影响）。

UI 细节见 `docs/frontend_requirements/工作流执行日志开关.md`。

### 9.6 兼容与影响

- 存量工作流 / 存量复合动作的 `log_enabled=false` 经迁移置为 `NULL`（未设置）：
  - 项目兜底仍为 `False` 时整体行为与改造前一致（不记录）；
  - 一旦项目兜底打开，存量工作流/动作立即按兜底采集——这是「项目开关」的预期语义。
- 前端弹窗的开关只会提交布尔值：关 = 显式关闭（可压制动作级与项目级），
  开 = 显式开启；「未设置」只能通过不带该字段的 API 调用 / 导入 JSON 产生。
- 7 天保留为全局策略（`cleanup_expired` 按 `started_at` 删除），不区分用户/工作流；`retention_days=0`
  的永久保留语义保留（配置为 0 时清理任务空转）。
- `WorkflowRunRecord` 聚合记录不受影响（本就不依赖 action 的 `log_enabled`）。
- 日志表写入方从「执行协程同步写库」变为「MQ 异步落库」：执行线程只承担一次
  本地队列投递；RabbitMQ 不可用时自动回落同步写库，日志不丢。

### 9.7 验收

1. 编辑工作流打开「记录执行日志」→ 立即运行 → `action-logs/list` 出现 `source=workflow` 的步骤记录，
   且 `workflow_id` / `execution_id`（= `run_id`）正确，可按执行批次下钻。
2. 关闭开关后运行 → 不产生任何步骤日志（即使动作自身开启了日志）。
3. 复合/循环/分支嵌套步骤：开关开启时子步骤同样落日志，开关关闭时全部不落。
4. 手动执行单操作（`/actions/execute`）行为不变（按动作自身配置 → 项目兜底）。
5. 优先级矩阵：项目开 + 工作流未设置 + 动作未设置 → 记录；项目关 + 工作流开 → 记录；
   项目开 + 工作流关 → 不记录；项目开 + 工作流未设置 + 动作关 → 不记录。
6. 导出 JSON 含 `log_enabled`（可为 `null`），导入后保留该设置。
7. 日志表插入 8 天前的数据 → 周期清理任务执行后该记录被删除，7 天内的保留。
8. 停用 RabbitMQ 后执行工作流：日志自动回落同步直写不丢失，且不出现每条日志
   重复建连导致的执行卡顿（熔断生效）；恢复 RabbitMQ 后回到 MQ 异步落库。
9. 重启 RabbitMQ（队列与消息持久化）→ 停机期间堆积的日志在消费端恢复后被幂等落库。

## 9.8 用户级 debug 模式：执行日志全量采集（2026-10-25 增量）

> UI 需求：`docs/frontend_requirements/工作流执行日志开关.md`（调试模式开关）

### 9.8.1 背景与结论

§9 的三态开关链解决「要不要记」，但排查问题时用户需要**更多**：变量池快照、
成功步骤的入参/结果、超长 payload 不截断、失败带完整 traceback。逐项打开
`record_variables / only_on_error / max_payload_length` 对非技术用户不可操作。

结论：引入**调试模式（debug）**——一个开关把采集强度拉到最满。debug 是
**用户级设置**（曾误做成服务端 env `ACTION_LOG_DEBUG_ENABLED`，已回退），
用户在工作流 / 复合动作的「执行日志」设置里自行选择是否开启。

### 9.8.2 数据模型变更

| 模型 | 字段 | 类型 | 语义 |
| --- | --- | --- | --- |
| `UserWorkflow` | `log_debug` | `bool \| None`，默认 `None` | `None`=未设置；`True`=本次运行强制全量采集 |
| `CompositeActionModel` | `log_debug` | `bool \| None`，默认 `None` | `None`=未设置；`True`=该复合动作强制全量采集 |
| `ActionLogOption` | `debug` | `bool`，默认 `False` | 执行参数 / 父透传配置里的调试标记 |

迁移：`20261025_log_debug`——两表各加一列可空布尔（`None`=未设置，
与 `log_enabled` 同款三态语义；存量数据不受影响）。无新表。

### 9.8.3 采集优先级（debug 出现在任一级即归一化）

| 优先级 | 开关 | 说明 |
| --- | --- | --- |
| 1 | 执行参数 `log.debug` | 单次执行某步骤；JSON 内联 |
| 2 | 父操作透传配置（`debug` 随 `log_config` 继承） | 复合/循环/分支子步骤 |
| 3 | **工作流级** `UserWorkflow.log_debug` | 优先于工作流 `log_enabled`；debug 隐含「开启」，压制动作级与项目级 |
| 4 | 工作流开关 `UserWorkflow.log_enabled` | 本次运行总闸（§9.3 既有） |
| 5 | **动作级** `CompositeActionModel.log_debug` / `log_enabled` | 单操作执行（`/actions/execute`）走这一级；`log_debug=True` 独立生效，不受 `log_enabled` 为 NULL 的门禁阻挡 |
| 6 | 项目兜底 `settings.action_log_default_enabled` | 全局默认 |

归一化（`action_logger._normalize_debug`，在 `resolve_log_option` 出口统一执行）：

- `enabled=True`、`record_params / record_result / record_variables=True`、
  `only_on_error=False`（成功也全记）；
- `max_payload_length=0`（不截断，保证 traceback 等排障信息完整可查）；
- **保留期与体积策略和普通日志完全一致**（仍走 `action_log_default_retention_days`
  与周期清理），不做单独管理；
- 脱敏规则不变（`_redact_sensitive` 照常生效，`llm_api_key` 等仍打码）。

例外：参数级显式 `log: {enabled: false}`（不带 debug）仍优先于工作流 debug——
更具体的配置获胜；服务端没有能压过用户的全局开关。

### 9.8.4 失败 traceback 入库

`engine.py` 的 `except Exception` 分支把 `traceback.format_exc()` 追加进
`result.logs`，随 `ActionLogRecord.logs` 落库。此前 `error_message` 只带
`str(e)`，调用栈只进 loguru stderr，MCP / 前端从库里看不到炸点。

### 9.8.5 后端改造清单

1. **模型**：`ActionLogOption.debug`；两表 `log_debug` 列 + 迁移。
2. **采集**：`action_logger` 新增 `_normalize_debug`，`resolve_log_option`
   新增 `workflow_log_debug` 参数（优先于 `workflow_log_enabled` 判定）；
   `_resolve_db_log_option` 的门禁从「`log_enabled` 非 NULL」扩展为
   「`log_enabled` 非 NULL 或 `log_debug` 为真」。
3. **透传**：`engine.execute_action / execute_steps / _run_action /
   _run_action_core` 串联 `workflow_log_debug`；`run_workflow` 传
   `workflow.log_debug`；复合动作子步骤经 `exec_meta["log_config"]` 继承。
4. **接口**：`WorkflowCreateRequest / WorkflowUpdateRequest` 与两个响应模型、
   `CompositeActionCreateRequest / UpdateRequest` 与响应模型、admin 路由映射、
   `workflow_crud` / `action_crud` 的 create / update / fork 透传、
   `ActionSavePayload`（MCP 落库载荷）、`scripts/import_action_from_json.py`。
5. **JSON 一致性**：动作导出 JSON 增加 `log_debug` 字段（与 `log_enabled` 同址），
   导入后写库；Fork 动作随源动作一并继承（RPA 规范：JSON 与 DB 一致）。

### 9.8.6 验收

1. 工作流开 debug + 关 `log_enabled` 运行 → 仍全量记录（debug 隐含开启）。
2. 工作流开 debug → 每个步骤（含嵌套子步骤）的 `params / result_data /
   variables` 均非空，成功步骤也记录；payload 不截断。
3. 工作流未设置 + 复合动作 `log_debug=true`（`log_enabled=null`）→ 该动作全量记录。
4. 单操作执行带 `log: {"debug": true}` → 该次全量记录。
5. 全部未设置 → 行为与 §9 完全一致（无回归）。
6. 失败步骤的 `logs` 含完整 traceback（`Traceback (most recent call last)`）。
7. 导出 / 导入 JSON 保留 `log_debug`；Fork 工作流 / 动作继承该设置。
8. 7 天保留与周期清理对 debug 记录一视同仁（不单独管理）。

## 10. 运行进度 SSE 推送与重启断点恢复（2026-10 增量）

> 关联：`docs/rpa-会话状态SSE推送计划书.md`（进程内事件总线 + 首帧快照 + 心跳 + 无 Last-Event-ID 的既有范式）
> UI 需求：`docs/frontend_requirements/工作流运行进度与断点恢复.md`

### 10.1 背景与结论

现状三处缺口：

1. **运行期不可观测**：`WorkflowRunRecord` 只在结束时一次性写 `success_count/failed_count`，
   `running` 期间前端只能看到「正在运行」，长循环（如批量处理 200 条资源）没有任何进度；
2. **前端误判**：`/workflows/run` 早已改为异步返回 `status=running`，前端仍按同步语义判断
   `status === 'success'`，因此每次运行都会误报「运行失败：未知错误」；
3. **重启即丢**：`interrupt_stale_running()` 把残留 RUNNING 一律收口为 `interrupted`，
   既不保存执行位置，也没有任何恢复入口，一次 `kill -9` 就白跑。

结论：

- **进度用 SSE 推送**（不用轮询）：复用 `SessionStatusBus` 的进程内总线范式，新增
  `workflow_run_progress` 事件与 `GET /workflows/runs/events?run_id=` 长连接；
- **进度以循环轮次为主轴**（用户视角的「第 3/20 条」），步骤进度为辅，同时下发已用时、
  当前步骤名、成功/失败计数、触发来源、目标浏览器等「尽可能多」的状态；
- **重启恢复以「步骤检查点 + 资源幂等」实现**：保存已完成步骤数，重启后从该步骤继续执行；
  循环内已处理资源由 `WorkflowResourceRecord`（success/skipped）跳过，保证「至少一次」语义下不重复处理。

### 10.2 数据模型变更（RPA-Browser）

`app/models/database/workflow/models.py`：

`WorkflowRunRecord` 新增运行期进度 / 恢复字段：

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `completed_steps` | `int` | 0 | 已完成步骤数（运行中实时递增，= 恢复检查点） |
| `current_step_name` | `str(200)` | `""` | 当前/最近执行的步骤显示名 |
| `current_step_index` | `int` | 0 | 当前步骤在顶层步骤列表中的下标（0 基） |
| `loop_action_name` | `str(200)` | `""` | 当前循环步骤显示名（非循环为空） |
| `loop_index` | `int` | 0 | 当前循环轮次（1 基，0 表示尚未进入循环） |
| `loop_total` | `int` | 0 | 当前循环总轮次；0 = 未知（condition 循环 / 分母运行时才求出） |
| `progress_updated_at` | `datetime \| None` | `None` | 最近一次进度上报时间（心跳，用于判断卡死） |
| `resumable` | `bool` | `False` | 本次运行被中断后是否允许恢复 |
| `resume_of` | `str(64) \| None` | `None` | 恢复来源的运行 ID |
| `resume_count` | `int` | 0 | 连续恢复次数（防重启死循环） |
| `checkpoint_step` | `int` | 0 | 中断时的步骤检查点（= 中断瞬间的 completed_steps） |

`UserWorkflow` 新增：

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `resume_on_restart` | `bool` | `False` | 服务重启后是否自动恢复该工作流本次被中断的运行 |

默认 `False`：恢复是「至少一次」语义，步骤可能已有外部副作用（发私信、点赞），
是否自动重跑必须由用户显式开启；未开启时运行记录提供「继续运行」按钮手动恢复。

迁移：`alembic/versions/20261018_wf_run_progress_resume.py`（`workflowrunrecord` 加 11 列 +
`userworkflow` 加 1 列）与 `alembic/versions/20261018_wf_run_loop_body_progress.py`
（循环体内动作进度 3 列），均带 `server_default`，保证存量行可读。

### 10.3 进度上报器（新文件 `app/services/execution/workflow_progress.py`）

- `WorkflowRunProgressData`（pydantic，SSE 载荷）：`run_id / workflow_id / workflow_name /
  status / trigger_source / browser_id / started_at(UnixTime) / updated_at(UnixTime) /
  total_steps / completed_steps / current_step_name / success_count / failed_count /
  loop_action_name / loop_index / loop_total / loop_total_known / resume_of / resume_count /
  error_message`。时间字段用 `bili_common.core.time_utils.UnixTime`（秒级 int）。
- `WorkflowRunProgressBus`：与 `SessionStatusBus` 同构（`run_id → set[Queue]`、
  队列满丢最旧帧、`bind_loop()` 支持跨线程投递）。
- `iter_workflow_run_progress_events(run, initial, heartbeat_interval)`：首帧全量快照 →
  进度帧 → 心跳注释行；**推送终态帧后结束生成器**（`running` 之外的任何状态）。
- `WorkflowRunProgressReporter`：单个运行的上报器，持有内存快照：
  - `step_started(index, action_id, name)`：写 `current_step_index/current_step_name`，立即推送；
  - `step_finished(success, error=None, result=None)`：`completed_steps += 1`、成功/失败计数 +1，
    **步骤边界强制落库**并推送；传入 `result` 时把动作返回内容渲染成 `detail` 一并推送；
  - `loop_iteration(action_id, name, index, total, depth)`：更新循环进度；仅记录**最外层循环**
    （`depth` 更小的优先，同深度以最新为准），避免嵌套循环把外层轮次覆盖成 1/3；
  - `flush()`：运行结束时把最终快照落库并推送终态；
  - **落库节流**：步骤边界强制写；循环轮次 ≥1s 才写（内存缓存最后一次快照），
    推送不节流（本地队列投递成本可忽略）。
- 与 `ActionLogRecord` 解耦：进度不依赖 `log_enabled`，关节志也照常上报。

### 10.4 执行链路埋点

1. `Scope.__slots__` 增加 `progress`（`WorkflowRunProgressReporter | None`）与
   `progress_top_level`（`bool`），由 `ExecutionEngine.execute_steps` 注入；单操作执行不注入。
2. `Pipeline.execute`：顶层管道（`scope.progress_top_level == True`）在每个步骤开始前调用
   `step_started`、结束后调用 `step_finished`；嵌套管道（循环体/分支体）不重复计数。
   **循环体内动作另有消息埋点**：`body_of_loop=True` 的管道（**任意嵌套层**）里，
   每个动作开始/结束调用 `body_step_started` / `body_step_finished`
   —— 只发**运行消息**，不写 `completed_steps`、不进成功/失败计数
   （循环整体才算一个顶层步骤）。放在 `finally` 里上报，保证成功 / 失败 / 异常 / 重试
   都只发一次终态。
   嵌套循环**照常打印**（打印不落库，层数不是问题）：每层各自记录轮次
   （`_loop_layers: dict[int, LoopLayer]`），消息带 `depth`（1=最外层循环体，2=再内一层…），
   前端按 `depth` 逐级缩进/嵌套展示。**只有进度维度**（两条进度条）仍然只跟踪最外层
   —— 进度条只有一个「本轮动作」槽位，内层不该覆盖外层的 N/N。
3. `LoopStep.execute`（`app/services/execution/pipeline.py`）每轮开始调用 `loop_iteration`，
   携带 `loop_source` 求得的 `total`（`fixed_count` / `json_list` / `variable` / `expression`
   均可得，`condition` 循环为 0=未知）。
   `data` 字段修正：`iterations` = **实际执行轮次**（此前误用循环体内步骤结果条数，
   3 轮 × 4 步会报成 12），另加 `steps` = 循环体内步骤结果条数。`_loop_by_items/count/
   while/until` 四个分支返回 `(results, rounds)`，由 `execute` 统一组装。
4. `run_workflow` 在创建运行记录后构造 reporter 并传给 `execute_steps`；收口时 `flush()`。
   `control_flow.LoopStrategy`（动作级 loop，单操作执行路径）不接入，工作流步骤由
   `PipelineBuilder` 编译为 `Pipeline.LoopStep`，无需重复埋点。

### 10.5 SSE 端点

| 新接口 | 路径 | 说明 |
| --- | --- | --- |
| 运行进度事件流 | `GET /browser/control/workflows/runs/events?run_id=` | `text/event-stream`；首帧当前快照，终态后关闭 |

- 鉴权：`get_auth_info_from_header` + 按 `run_id` 校验 `mid` 归属（不存在/越权返回 404 业务码）。
- 同一条连接承载两类事件：
  - `workflow_run_progress`：`WorkflowRunProgressData` 全量快照（覆盖式）；
  - `workflow_run_log`：`WorkflowRunLogEvent` 增量消息（步骤开始/完成/失败、循环轮次、
    循环结束、运行结束），供前端「运行消息」栏逐条展示。
- `WorkflowRunLogEvent` 字段：`run_id / seq / ts / kind / level / text / detail / action_id /
  action_name / step_index / total_steps / success / duration_ms / error / loop_index / loop_total`；
  `text` 为后端统一拼好的可读文案，`seq` 供前端去重（断线重连会补发缓冲）。
  `kind` 取值：

  | kind | 含义 | 频率 |
  | --- | --- | --- |
  | `step_started` / `step_finished` | **顶层**步骤开始/完成（含失败原因、耗时、返回明细） | 每顶层步骤 2 条 |
  | `loop_iteration` / `loop_finished` | 循环轮次 / 循环结束（**每层**都发，`depth` 标识层） | 每轮 1 条 + 每层结束 1 条 |
  | `body_step_started` / `body_step_finished` | **循环体内**动作开始/完成（带 `loop_index` 与本层轮次） | 每轮 × 循环体动作数 |
  | `run_finished` | 运行结束汇总 | 1 条 |

  **消息全量打印**：循环体内动作与顶层步骤一视同仁——成功/失败都附 `detail`，
  不做条数、内容、层级层面的裁剪；嵌套多少层就打印多少层。

  > **打印 ≠ 落库（务必分清）**：`workflow_run_log` 事件只在内存里经 SSE 转发，
  > 不写运行记录表、不进操作日志、**不占硬盘**，因此不该用「省空间」的理由限制它；
  > 真正需要节流的是落库路径（见下）。消息读起来太密属于**呈现问题**，
  > 由前端按轮次分批收拢解决（前端需求文档 §4.5）。
- **循环提前退出**：`loop_finished` 文案用实际执行轮次与总轮次比对，
  未跑满时写作「循环「X」结束（执行 2/35 轮，提前退出）」，跑满才是「共 N 轮」。
- **`detail`（步骤结果明细）**：`step_finished` 事件额外携带该步骤动作的**返回内容**
  （`ActionResult.data`，如 `fetch_external_data` 的接口响应），让界面不只看「完成了哪一步」，
  还能直接看到「拿到了什么数据」：
  - 由 `WorkflowRunProgressReporter.step_finished(..., result=)` 渲染：
    先 `to_jsonable` 转可序列化结构，再追加 `ActionResult.logs`（如去重统计）；
  - 上限由配置 `workflow_run_log_detail_max_length`（字符）控制，**默认 0 = 不限制**
    ——消息不落库，默认全量打印；仅在慢网络/超大响应需要兜底时才配具体字符数，
    超长走 `shrink_json_payload` 按结构裁剪（键全保留、字符串截断、列表留前缀）
    并追加 `…(已截断)`；无 data 且无 logs 时为 `null`；
  - 只用于推送，不落库（运行记录表不加列），运行记录快照体积不受影响；
  - 序列化工具收敛到 `app/utils/json_utils.py`，与操作日志落库（`action_logger`）共用。
    **注意裁剪口径不必一致**：落库要考虑磁盘，打印不需要。
- 上报器维护最近 1000 条消息的环形缓冲（内存），SSE 建连时**补发**，
  避免半路打开只看到后续步骤；单连接待发送队列 512 帧，避免循环体密集上报时丢消息；
  终态后进入终态帧并关闭连接。
- 显式声明 `responses={200: {"content": {"text/event-stream": {}}}}`（否则 hey-api 不生成 SSE 方法）；
  headers 与既有会话 SSE 一致（`Cache-Control: no-cache` / `X-Accel-Buffering: no`）。
- 新增配置 `workflow_run_sse_heartbeat_interval`（秒，默认 15）。

### 10.6 重启恢复

#### 收口阶段（改造 `interrupt_stale_running`）

- 逐条收口时计算并写入：`checkpoint_step = completed_steps`、`checkpoint_loop_index = loop_index`、
  `resumable = 中断原因属于服务重启/协程取消（不是用户停止、不是执行失败）且 checkpoint_step > 0`；
- 用户手动停止（CANCELLED）与执行失败（FAILED）**不**标记可恢复。

#### 恢复阶段（新函数 `resume_interrupted_runs()`，`main.py` lifespan 启动时调用）

- 在 `start_background_tasks()`（内部完成 `interrupt_stale_running()`）与
  `start_rpc_server()` **之后**执行：恢复出来的运行会立刻执行步骤，HTTP 类动作
  依赖 RPC 链路，必须等 RPC 就绪；早于调度器注册不影响（恢复走独立 task）。
  对每条候选运行：

| 条件 | 说明 |
| --- | --- |
| `status == interrupted` 且 `resumable == true` | 仅服务中断类运行 |
| `resume_count < settings.workflow_resume_max_count` | 默认 3，防重启死循环 |
| `finished_at > now - workflow_resume_max_age_seconds` | 默认 6h，太久的不恢复（浏览器会话早已失效） |
| 工作流 `resume_on_restart == true` 且 `is_enabled == true` | 用户显式授权自动恢复 |
| 该浏览器当前无 `running` 运行 | 不打断正在执行的任务 |

- 命中后调用 `launch_workflow_run(..., resume_from=旧运行)`：
  - 新运行 `resume_of = 旧.run_id`、`resume_count = 旧.resume_count + 1`、
    `checkpoint_step = 旧.checkpoint_step`，`total` 与旧运行一致；
  - 旧运行置 `resumable = false`（保证同一条只被恢复一次，失败不无限重试）。
- 恢复执行体（`run_workflow` 新增 `resume_from` 参数）：
  - `execute_steps(..., skip_steps=checkpoint_step)`：引擎只执行 `steps[checkpoint_step:]`；
    当前步骤是「重跑」而非「跳过」，符合至少一次语义；
  - `total = len(全部步骤)`，`success_count` 初值继承旧运行（进度条不回退）；
  - 循环内中断：整个循环步骤重跑，已成功资源由 `WorkflowResourceRecord` 去重跳过
    （未使用资源记录的工作流会重复处理，这正是默认关闭自动恢复的原因）；
  - 会话由 `get_or_create_browser_session_entry` 重新拉起（与定时运行一致）；
  - 通知：`notify_on_start` 开启时标题追加「（恢复运行 · 第 N 次）」。

#### 手动恢复接口

| 新接口 | 路径 | 说明 |
| --- | --- | --- |
| 继续运行 | `POST /browser/control/workflows/runs/resume` | body `{run_id}`；校验归属 + `resumable` + 无 running，立即返回新 `run_id` |

### 10.7 前端改造（Vue3FrontEndDemoExercise）

- 新增薄封装 `src/api/browser/workflow_run_api.ts`：`subscribeWorkflowRunProgress(runId)`
  基于生成 SDK 的 `client.sse.*` 订阅 `workflow_run_progress`，首帧即渲染；断线由 SDK
  重连（最多 2 次、1.5s 起）；收到终态帧或调用返回的 close() 即断开；鉴权走
  `user_header`，不手改生成代码。
- 新增展示组件 `WorkflowRunProgressBar.vue`（卡片与运行记录弹窗复用）：
  - 进度条：循环中 → `loop_index/loop_total`；否则 → `completed_steps/total_steps`；
    `loop_total_known == false` 用不确定态动画，禁止伪造百分比；
  - 运行时长：基于 `started_at` 本地每秒自增（不依赖推送频率），终态改用 `duration_ms`；
  - 文本：`第 i/N 轮 · 循环「名称」` / `步骤 k/M · 当前步骤` + `成功 a / 失败 b` +
    触发来源 + 恢复次数；60s 无新帧提示「进度较久未更新」。
- `WorkflowManagement.vue` 卡片：`running` 时展示上述进度条；`interrupted` 时提供
  「继续运行」（先查最近一条运行确认 `resumable`）；列表刷新后自动同步订阅集合，
  连接异常则清本地进度并回落列表状态。
- `WorkflowRunLogDialog.vue`：`running` 行复用同一进度条与计时（SSE 实时更新行内步骤数）；
  `interrupted && resumable` 行显示「可恢复」标签与「继续」按钮（调 `/runs/resume`）；
  弹窗关闭/卸载即断开全部订阅。
- **修正 `handleRun`**：拿到 `run_id` 后再订阅进度，开始只提示「已开始运行」，终态才由
  进度帧弹结论 toast；不再按同步语义判断（旧代码必报「运行失败：未知错误」）。
- WorkflowEditDialog 增加「断点恢复 / 重启后自动恢复」开关（绑定 `resume_on_restart`）。
- 时间字段统一按秒级 int 处理（进度帧），运行记录接口的 ISO 字段保持原展示方式。

### 10.8 兼容与影响

- 新增列均有 `server_default`，存量运行记录 `completed_steps=0 / resumable=false`，行为不变；
- `resume_on_restart` 默认 `false`：存量工作流不会因升级后重启而被自动重跑；
- SSE 为新增端点，不影响既有 `/workflows/runs` 轮询能力（前端可降级轮询）；
- 前端 SDK 必须由用户重新生成（新 SSE 端点 + 新响应字段 + 新请求参数），生成代码禁止手改。

### 10.9 验收

1. 运行中订阅 `runs/events`：步骤边界收到事件，`completed_steps` 递增、`current_step_name` 变化。
2. 循环工作流：每轮 `loop_index` 递增，`loop_total` 与配置一致；condition 循环 `loop_total=0`，
   前端显示不确定态。
3. 终态（success/failed/cancelled/interrupted）推送一帧后连接关闭；前端据此停表并刷新列表。
4. 前端不再误报「运行失败：未知错误」（异步 run 语义修正）。
5. `kill -9` 服务后重启：残留 RUNNING 收口为 `interrupted`，`checkpoint_step` = 中断时完成步数。
6. 工作流开启 `resume_on_restart` → 启动后自动拉起新运行，`resume_of` 指向旧运行，
   从 `checkpoint_step` 之后继续；浏览器会话自动重启。
7. 未开启 → 不自动恢复；运行记录出现「继续运行」，手动点击后同样从断点继续。
8. 连续中断超过 `workflow_resume_max_count` 次后不再自动恢复，记录 `resumable=false`。
9. 用户手动停止（cancelled）与执行失败（failed）的运行**不会**被自动恢复。
