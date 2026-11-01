# Fork 上游同步（前端需求）

> 后端计划书：`RPA-Browser/docs/fork-上游同步计划书.md`
> 涉及页面：自定义操作列表/详情、工作流列表/详情、Fork 对话框、编辑表单

## 1. 「可同步」标识展示（图标化）

已按「去标签/去按钮 clutter」要求改为图标表达（2026-10-17 v2）：

- **同步状态图标**（`refresh.svg`，仅 Fork 副本展示，位于卡片右上角名称行）：
  - `has_upstream_update == true` → **warning 色高亮，可点击**，点击即触发同步（含 loading 态）；
  - 否则 → 置灰不可点；
  - 悬停文案由 `syncIconTip` 给出：有更新/已是最新/有本地修饰 variants；
  - 非 Fork 资源不展示该图标。
- **时间信息**：卡片悬浮 tooltip 中展示 `upstream_updated_at` / `last_synced_at`（秒级转本地时间），
  动作详情弹窗（`ActionDetailDialog`）中常驻一行同步状态文字。
- 图标遵循 `.codebuddy/rules/icons.mdc`：一律 `src/assets/svgs/`（`refresh.svg` / `tag.svg` / `more.svg` / `copy.svg`），
  缺失的图标（如编辑）不擅自用 EP 图标凑数，对应操作收进「更多」下拉。

## 2. 手动「同步」入口（图标化）

- **入口**：卡片右上角同步图标（有更新时高亮可点）+ 详情弹窗文字说明；不再有独立「同步上游」按钮。
- **行为**：调用已有接口
  - 操作：`POST /custom_actions/sync`，body `{"action_id": <雪花id>}`
  - 工作流：`POST /workflows/sync`，body `{"id": <数据库id>}`
- **结果处理**：
  - 成功：toast 展示后端返回的 `msg`；`local_overwritten == true` 时追加「（已覆盖本地修改）」；成功后刷新列表（图标恢复置灰）。
  - 失败：toast 展示错误信息。
  - 同步中图标按钮 loading，防重复点击。

## 2.5 卡片整体图标化重构（v2）

- **动作卡片**（`ActionManagement.vue`）：移除「公开/私有」标签、「可同步」徽标、
  「同步上游 / 申请发布 / 重命名 / 删除」文字按钮；保留「查看」主按钮，
  标签编辑改为 `tag.svg` 图标按钮；重命名/申请公开/删除收入 `more.svg`「更多」下拉；
  自动同步与可见性改为带 tooltip 的开关（hover 显示 开/关、公开/私有）。
- **工作流卡片**（`WorkflowManagement.vue`）：同样移除右上角标签与「同步上游/申请发布/删除」按钮，
  复制改为 `copy.svg` 图标按钮，次级操作收入「更多」下拉；调度信息行标签
  （触发方式/运行状态/目标浏览器/日志）承载文本数据，保留。
- **动因**：卡片操作项过多，一屏视觉噪音大；按「主操作文字按钮 + 次级操作图标 + 更多下拉」收敛。

## 3. 自动同步开关

已实现入口（2026-10-17）：

- **入口 1 - Fork 对话框**（`CommunityPage.vue`）：Fork 动作/工作流的确认弹窗内增加
  「开启上游自动同步」勾选框（默认不勾），勾选后随 Fork 请求提交
  （`POST /custom_actions/fork`、`POST /workflows/fork` 的 body 增加 `auto_sync_upstream: boolean`）。
- **入口 2 - 管理列表卡片**（`ActionManagement.vue` / `WorkflowManagement.vue`）：Fork 副本
  （`forked_from_id != null`）的卡片操作栏展示「自动同步」开关，通过更新接口提交：
  操作 `POST /custom_actions/update`、工作流 `POST /workflows/update`
  的 body 增加 `auto_sync_upstream: boolean`（不传=不修改）；失败自动回滚开关状态。
- **文案**：「自动同步」+ 勾选框说明「上游更新后自动同步到我的副本；有本地修改时会跳过并通知」。

## 4. 本地修改提示

- 列表/详情的 `local_steps_modified == true` 时，展示「有本地修改」提示（弱样式，如置灰文字）。
- 语义：该副本修改过会被同步覆盖的内容（操作 steps / 工作流触发配置），
  **自动同步会跳过它**；手动同步仍可用（会覆盖）。
- 可与「可同步」徽标同时出现，二者不互斥。

## 5. 响应字段速查

| 字段 | 类型 | 说明 |
|---|---|---|
| `has_upstream_update` | bool | 上游是否有新版本可同步 |
| `upstream_updated_at` | int \| null | 上游最近更新时间（秒级时间戳） |
| `last_synced_at` | int \| null | 本地最近同步时间（秒级时间戳，null=从未同步） |
| `auto_sync_upstream` | bool | 自动同步开关状态 |
| `local_steps_modified` | bool | 是否有会被同步覆盖的本地修改 |

覆盖接口：操作列表/详情/更新/forks 列表、工作流列表/详情/更新/forks 列表均返回上述字段；
同步接口（`/custom_actions/sync`、`/workflows/sync`）额外返回 `local_overwritten`。

## 6. 自动同步结果

自动同步由后端定时任务完成，结果通过**站内通知**送达（与工作流运行通知同一渠道），
前端无需轮询；收到通知后刷新列表即可看到徽标消失、`last_synced_at` 更新。
