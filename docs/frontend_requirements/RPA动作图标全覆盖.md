# RPA 动作图标全覆盖（前端需求）

> 适用仓库：`Vue3FrontEndDemoExercise`
> 关联后端：`RPA-Browser/docs/内置动作通用化与图标全覆盖计划书.md`
> 关联既有文档：仓库根 `docs/rpa-自定义动作图标计划书.md`、
> `docs/frontend_requirements/工具箱图标与拖拽预览.md`、
> `RPA-Browser/docs/frontend_requirements/动作分类与检索.md`

---

## 1. 背景

当前动作图标是「后端下发 `icon_series`/`icon_id` → 前端 `ActionIcon` 查图库清单 →
未命中渲染 `fallback` 插槽（内置动作按 action_id 取 Element Plus 图标，自定义动作取 `QuestionFilled`）」。
出现两类缺口：

1. 后端有 3 个内置动作没登记图标编号，5 个动作的编号（124~128）在图库 `s_33`（实际 `1..121`）里不存在，
   因此这些动作实际展示的是 Element Plus 兜底图标；
2. 用户保存自定义动作时若未选图标（协议 `0/0`），工具箱 / 动作卡片 / 动作管理 / 流程图里
   统一显示问号 `QuestionFilled`，辨识度差。

需求：**所有 action 都有图标**——内置动作全部指向真实图库资源；自定义动作即使没选图标，
也自动分配一个稳定的图库图标，界面上不再出现问号 / 默认兜底图标。

---

## 2. 需求口径

| # | 需求 | 说明 |
|---|---|---|
| 1 | 内置动作图标全覆盖 | 后端为 30 个内置动作各分配一个真实存在、互不重复的 `s_33` 图标编号；前端无需新增映射 |
| 2 | 自定义动作自动图标 | 新建动作在保存表单里就按动作名分配并**落库**一张图库图标；存量 `0/0` 动作在展示层按动作 id 稳定分配；同一动作各处展示一致 |
| 3 | 保留最后兜底 | 图库清单为空 / 资源 404 时仍回落 `resolveActionTypeIcon`，不报错、不空白 |
| 4 | 图标选择器同步 | 「默认图标」选项改称「自动图标」，预览自动分配结果，文案说明分配规则 |
| 5 | 名称同步 | `get_window` 显示名由「获取窗口」改为「获取 window 属性」；移除已删除的 `bili_reserve` 常量 |

### 2.1 非目标

- 不改 `icon_series=0 / icon_id=0` 的协议语义（仍代表「未选择」，存量动作的自动分配只发生在展示层；新建动作则直接落库具体编号）；
- 不把 Element Plus 图标当作业务图标新增到界面（仅保留清单缺失时的最后兜底）；
- 不改 `src/api/**/hey-api/` 生成代码；后端枚举删除 `BILI_RESERVE` 后，生成 SDK 由用户手动重新同步；
- 不改动作分类体系、不改步骤数据结构、不改 `DroppedItem`。

---

## 3. 交互与展示规格

### 3.1 自动分配规则

- **两条路径**：
  1. 新建动作：`useDebugboxSave.ts#makeSaveForm` 用 `autoAssignActionIcon(name)` 生成
     `icon_series/icon_id` 并随创建请求落库（此时还没有 `action_id`，以动作名为 seed）；
  2. 存量 `0/0` 动作 / 编号越界：`ActionIcon.vue` 在展示层用
     `resolveDisplayActionIconUrl(series, id, seed)` 按动作 id 自动分配，不改协议值。
- 分配算法：以 `seed` 做稳定字符串哈希（FNV-1a），
  对「`s_33` 系列中按编号升序排列的图标列表」取模，得到唯一编号；
- 稳定性：同一 `seed` 在任意页面 / 任意组件 / 刷新前后都得到同一张图标；
  不同动作大概率不同（允许哈希碰撞）；
- 选择器预览：新建对话框传草稿动作名、编辑对话框传 `action_id`，
  与各自实际生效的 seed 保持一致；
- 图库清单为空时不分配，渲染 `fallback` 插槽。

### 3.2 展示点（全部都要有图标）

| 组件 | 传参 |
|---|---|
| `ActionCard.vue` | `:seed="action.action_id"` |
| `ToolboxPanel.vue` 私有/公开动作列表 | `:seed="item.action_id"` |
| `ToolboxPanel.vue` 基础操作树 | `:seed="data.action_id"` |
| `ActionManagement.vue` 动作卡片 | `:seed="item.action_id \|\| item.action_type"` |
| `ActionFlowView.vue` 流程节点 | `:seed="data.actionId"` |
| `ActionDetailDialog.vue` 详情 | `:seed="detail.action_type \|\| String(detail.action_id)"` |
| `ActionIconPicker.vue` 网格 / 自动图标卡片 | 网格传真实 `series/id`；自动图标卡片走自动分配预览 |

拖拽预览（`setToolboxDragGhost`）同样使用自动分配后的 URL，保证拖起来的缩略图与列表一致。

### 3.3 图标选择器文案

- 卡片标题：`自动图标（0 / 0）`；
- 说明：`未选图标时按动作 id 自动分配一张图库图标；图库缺失时回落内置图标`；
- 卡片左侧图标改为预览自动分配的图库图标（不再显示 `DEFAULT_ACTION_ICON` 问号）。

---

## 4. 样式规范

- 不新增 `<style>` / `:style`；尺寸与颜色全部走 Tailwind 原子类与 `theme.css` 语义类；
- 每个功能元素保留带业务语义的 `class`（如 `action-icon`、`action-icon-picker__default`）；
- 组件尺寸只用 `large` / `default`，不使用 `small`。

---

## 5. 验收标准

1. 30 个内置动作在 `/actions/registered` 返回的 `icon_series=33` 且 `icon_id` 互不重复、
   都能在 `actionIconManifest.ts` 中命中（不出现 Element Plus 兜底）；
2. 新建一个不选图标的自定义动作，工具箱 / 动作卡片 / 动作管理 / 详情页 / 流程图
   展示同一张图库图标，且不是问号；
3. 两个不同 id 的自定义动作（大概率）展示不同图标；刷新后图标不变；
4. 手动选了图库图标后，所有展示点以手动选择为准；
5. 清空图库清单（或资源 404）时不报错、不空白，回落内置类型图标；
6. 基础操作树里 `get_window` 显示「获取 window 属性」，不再出现「预约抽奖」；
7. 前端类型检查通过，`hey-api/` 生成文件零改动。
