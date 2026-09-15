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
7. 失败时（`failed_count > 0` 或整体异常）经既有推送链路通知：取
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
