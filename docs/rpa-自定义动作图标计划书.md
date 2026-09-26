# RPA 自定义动作「图标」改造计划书

> 关联：`docs/be-message-统一计划书.md`（5.7 RPA 扩展位）、`docs/rpa-workflow-调度外壳计划书.md`
> 涉及仓库：`RPA-Browser`（后端字段与接口）、`Vue3FrontEndDemoExercise`（图标映射与选择器）
> 前置规范：`.codebuddy/rules/icons.mdc`（界面图标一律使用 `src/assets/svgs/` 下的 SVG）

## 1. 背景与目标

自定义动作（`ca_xxx`）目前只有名称/描述/标签用于区分，在工具箱、动作卡片、动作管理列表里辨识度低。
本改造允许用户在「保存为自定义动作 / 编辑自定义动作」时**选取一个图标**，提升区分度。

设计口径（按需求约定）：

- 后端只存两个 **int**：`icon_series`（系列编号）+ `icon_id`（系列内编号）；
- **后端不做语义校验**，只限制 int 不超出最大范围；
- **前端负责映射**（系列 + id → 实际图标），遇到不在前端支持范围内的系列/id，一律回落到**默认图标**；
- `icon_series = 0` 或 `icon_id = 0` 视为「默认图标」。

## 2. 数据模型（RPA-Browser）

`app/models/database/workflow/models.py` → `CompositeActionModel` 增加：

| 字段 | 类型 | 范围 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `icon_series` | `int` | `0 ~ 999999` | `0` | 图标系列编号；0 = 默认图标 |
| `icon_id` | `int` | `0 ~ 99999999` | `0` | 系列内编号；0 = 默认图标 |

范围约束落在请求模型上（非法值由 FastAPI 直接返回 422），DB 模型上同样保留 `ge/le` 作为兜底。
**DB 不建 check 约束**：语义完全由前端决定，后端只保证「是范围内的 int」。

> 上限为何是 6 位 / 8 位：实际图库中系列编号最大 `9004`、图片编号最大 `9946760`（7 位），
> 最初的 `99 / 999` 会把真实资源编号全部拒掉。当前上限仍只是「int 范围兜底」，
> 远小于 int32 上限，且**不涉及数据库变更**（纯 Pydantic 约束，无需迁移）。

## 3. API 变更

`app/models/workflow/models.py`：

- `CompositeActionCreateRequest` / `CompositeActionUpdateRequest`：新增 `icon_series` / `icon_id`（可选，带范围校验）；
- `CompositeActionDetailResponse` / `CompositeActionListItemResponse`：回传 `icon_series` / `icon_id`。

`app/services/execution/crud_service/action_crud.py`：

- `create` / `update` 增加参数并落库；
- `fork` 复制原动作的图标（保持视觉一致）。

`app/controller/v1/browser_control/execution/action_router.py`：

- `create` / `update` 透传字段；
- 5 处响应构造点补齐字段（create / get / update / list / forks）。

## 4. 迁移

新增 alembic 迁移：`compositeactionmodel` 增加 `icon_series` / `icon_id` 两列（`INTEGER NOT NULL`，默认 0）。
存量数据自动为 0，即默认图标。

## 5. 前端（Vue3FrontEndDemoExercise）

### 5.1 资源约定（`public` 下静态托管目录）

动作图标是**内容图库**（可能是 png 等位图，不是纯 SVG，规模达数千张 / 数百 MB），因此资源放在
项目根 `action-icons/`（**不在 `public/`**）：Web 服务器**原样托管、不参与打包、不加内容 hash**；不进产物，部署时单独同步到站点根（见 `docs/前端部署说明.md`）。

```
action-icons/{分类}/s_{系列编号}_{系列名称}/i_{图片编号}_{图片名称}.{扩展名}
```

> 变更说明：初版曾放在 `src/assets/action-icons/` 并用 `import.meta.glob` 按需加载，
> 但位图 URL 会被编译成「导出 URL 的 JS 模块」，导致 dist 体积 ≈ 图库体积（580MB+）、
> 构建期数千个碎片 chunk、运行时每个图标多一次请求。已迁移到 `public/` + 清单方案。

| 示例 | 解析结果 |
| --- | --- |
| `FGO头像/s_1_saber/i_100100_阿尔托莉雅.png` | 分类=FGO头像, series=1 saber, id=100100 阿尔托莉雅, png |
| `s_2_数据抓取/i_1_提取标题.svg` | 分类=空, series=2 数据抓取, id=1 提取标题, svg |
| `s_0_默认/i_0_默认.svg` | 默认图标 |
| `s_1/i_3.png` | 系列名/图片名可省略，仍可解析 |

- **分类层可省略**（允许多层嵌套，仅紧邻系列目录的那一层会被当作分类名）；
- 系列名 / 图片名**可省略**，且**仅供前端展示**，不参与后端存储
  （后端仍只收 `icon_series` / `icon_id` 两个 int）；
- ⚠️ **分类只用于前端组织展示**，`s_{系列编号}` 必须在所有分类下**全局唯一**：
  后端没有分类字段，同编号跨分类会互相覆盖（开发态会打印冲突告警）；
- 名称允许含下划线、点（按最后一个 `.` 切扩展名）；不符合约定命名的文件会被忽略；
- **系列编号规则（方案 A：全局连续）**：按「分类名升序 → 分类内顺序」全库**连续编号、不留跳号**；
  因后端只存 `icon_series` 一个 int，编号必须**全局唯一**。当前分配：
  `FGO头像 1~27`、`Saber脸 28~33`、`指令纹章 34~38`、`礼装 39~43`。
  新增资源一律**追加到末尾**（新增分类则整段接在其后）。
  **内置动作不保留专属系列号**：其图标直接复用现有系列 `s_1`（`FGO头像/s_1_saber`）的 `i_1~i_16`，
  与后端 `BuiltinActionIconId`（1~16）一比一对应（见 §5.5），因此不会占用或阻塞连续编号。
- **图片编号规则**：每个系列内 `i_{编号}` 按升序**连续 `1..N`**；编号与文件名中的名称无关（名称仅供展示，可省略）。
  ⚠️ **编号一旦被自定义动作引用（DB `icon_series` / `icon_id`）就不可再重排** —— 重排前必须确认「已引用组合数 = 0」。
- 资源规模参考（当前实际）：4 个分类 / 43 个系列 / 4087 张
  （`FGO头像` 452、`Saber脸` 978、`指令纹章` 204、`礼装` 2453），均为 png；
  系列编号 `1~43`（连续）、图片编号 `1..N`。
  另注：后端 int 上限需够宽（见 §2）——历史资源曾使用 7 位官方编号（如 `9946760`）；
- **「编号 → 文件」映射靠清单**：文件名含中文业务名，无法由 `series/id` 反推，故由
  `scripts/gen-action-icon-manifest.mjs` 扫描目录生成 `src/utils/rpa/actionIconManifest.ts`
  （自动生成、勿手改；约 400KB，随 `rpa-browser` 路由懒加载，不进主包）；
  `npm run dev` / `npm run build` 已挂 `pre` 钩子自动重建，也可手跑 `npm run icons:manifest`；
- **收益**：dist 体积与图库规模解耦（回到几 MB）、构建不再处理 580MB 资源、
  运行时不再有「先加载 wrapper chunk 再加载图片」的双重请求，图片可由 Nginx / CDN 单独分发；
- **代价**：失去打包器的内容 hash 与引用校验。资源增删改后必须重建清单，
  可用 `npm run icons:manifest:check` 在 CI 里拦截「清单过期」。

- **多格式支持**：`svg / png / jpg / jpeg / webp / gif`，统一作为静态资源用 `<img>` 渲染；
  路径含中文业务名（如 `i_220_概念礼装经验卡：九字兼定.png`），必须逐段 `encodeURIComponent`
  后再拼 URL，不能用裸字符串。
- 同一「系列+编号」同时存在 SVG 与位图时，**SVG 优先**（在清单生成阶段去重）。
- **放入资源 + 重建清单即生效**：`src/utils/rpa/actionIcon.ts` 只读清单、不扫磁盘；
  资源增删改后执行 `npm run icons:manifest`（约 1 秒）。
- **默认图标不由图库提供**：未选自定义图标时沿用**前端既有的内置默认**（内置动作按
  `action_id` 取类型图标，其余回落 `QuestionFilled`，见 `src/utils/rpa/actionTypeIcon.ts`）。
  图库只需提供「具体图标」，无需 `s_0_*` 资源。
- 图库内的 SVG 由 `<img>` 加载，**不继承 `currentColor`**，颜色需在文件内部写死；
  最佳实践是自带 `viewBox` 而不写死宽高，尺寸交给调用方 class（`w-6 h-6`）控制。
  （需要跟随文字颜色变化的图标请放 `src/assets/svgs/`，走 `?component` 组件加载。）

### 5.2 兜底规则（前端职责）

1. `icon_series = 0` 或 `icon_id = 0`（未选择自定义图标）→ 内置默认图标；
2. 系列/编号在前端无对应资源（编号不存在、目录为空等）→ 同样回落内置默认图标，
   **不报错、不空白**；
3. 实现上：`resolveActionIcon` 未命中一律返回 `null`，由各调用点通过
   `ActionIcon` 的 `fallback` 插槽渲染内置默认图标
   （`DEFAULT_ACTION_ICON` / `resolveActionTypeIcon`）。

`resolveActionIcon` 统一返回**同步组件**（`Component | null`），由 `ActionIcon.vue` 用
`<component :is>` 渲染；组件内部就是一个 `<img :src="静态资源 URL">`，惰性创建并缓存。

调用方无需区分形态，只传 `series` / `id` 与尺寸 class。

### 5.3 已完成的改造

| 文件 | 改造 |
| --- | --- |
| `src/utils/rpa/actionIcon.ts`（改造） | 不再用 `import.meta.glob`，改为读取清单 `actionIconManifest.ts` 构建 `系列编号 → {系列名, 分类, 图标表}` 注册表；运行时 URL = `` `/action-icons/${dir}/${file}` ``（**站点根绝对路径**，逐段 `encodeURIComponent`；**不可用 `import.meta.env.BASE_URL`** —— Nuxt 客户端它是 `/_nuxt/`，拼出来是 `/_nuxt/action-icons/…` 必然 404 破图）；`ActionIcon.vue` 直接渲染 `<img>` 并在 `@error` 时回落 fallback；导出 `resolveActionIconUrl` / `getDefaultActionIcon` / `isDefaultActionIcon` / `hasActionIcon` / `getActionIconName` / `getActionIconSeriesName` / `getActionIconCategory` / `getActionIconSeries` / `getActionIconCategories` / `formatActionIconSeriesLabel` / `hasAnyActionIcon` / `ACTION_ICON_DIR` |
| `scripts/gen-action-icon-manifest.mjs`（新） | 扫描 `public/action-icons/`（分类层可选）解析 `series/id/名称/扩展名`，SVG 优先去重、跨分类同编号告警，生成 `src/utils/rpa/actionIconManifest.ts`（含 TS 接口，避免 TS 逐键推断超大字面量）；支持 `--check` 校验清单是否最新 |
| `src/utils/rpa/actionTypeIcon.ts`（新） | 内置动作类型图标表（由 `ActionCard` 原 `iconMap` 抽出）+ `DEFAULT_ACTION_ICON`（`QuestionFilled`）+ `resolveActionTypeIcon()`；作为图库未命中时的**统一默认图标** |
| `src/components/rpa-browser/ActionIcon.vue`（新） | 统一图标渲染器：`<component :is>` 渲染异步组件（SVG / 位图形态差异已被注册表抽象）；未命中时渲染 `fallback` 插槽；`inheritAttrs: false` + `v-bind="$attrs"` 让尺寸/颜色 class 透传 |
| `src/components/rpa-browser/ActionIconPicker.vue`（新） | 「默认图标」卡片 + **可搜索的系列下拉**（`编号 · 系列名`，多于一个分类时按分类分组）+ 编号/名称网格；`v-model:series` / `v-model:id`；格子显示 `#编号` 与名称（截断 + tooltip）；无资源时给出目录路径提示。系列数量可达数十个，故用下拉而非分段控件 |
| `src/components/rpa-browser/useDebugboxSave.ts` | 保存表单新增 `iconSeries` / `iconId`（统一 `makeSaveForm` 初始化），两个创建请求体带上 `icon_series` / `icon_id` |
| `src/components/rpa-browser/DebugBox.vue` | 「保存为自定义动作」对话框接入图标选择器 |
| `src/components/rpa-browser/EditCustomActionDialog.vue` | 编辑态回显图标 + 可修改，更新请求体带上两字段 |
| `src/components/rpa-browser/ActionCard.vue` | 图标映射抽到 `actionTypeIcon.ts`；用 `ActionIcon` 渲染自定义图标，`fallback` 为 `resolveActionTypeIcon(action_id)`（行为与改造前一致） |
| `src/components/rpa-browser/ToolboxPanel.vue` | 私有/公开列表条目用 `ActionIcon`，`fallback` 由原 `Bell` 改为统一默认图标；基础操作树用后端下发的 `icon_series`/`icon_id` 渲染（`fallback` 为原 `Tools`） |
| `src/views/rpa-browser/ActionManagement.vue` | 动作卡片名称行用 `ActionIcon`，`fallback` 为统一默认图标 |
| `src/components/rpa-browser/debugbox-types.ts` | `ActionDetail` / `DroppedItem` 增加 `icon_series` / `icon_id` |
| `src/components/rpa-browser/useDebugboxItems.ts` | 拖入新条目（主列表 / 分支）时携带 `icon_series` / `icon_id`（仅渲染用，不参与步骤序列化） |

### 5.4 待用户提供

1. 在项目根 `action-icons/` 下按
   `{分类}/s_{系列编号}_{系列名称}/i_{图片编号}_{图片名称}.{ext}` 放置资源
   （分类层可省略；`ext` 可为 `svg` / `png` / `jpg` / `jpeg` / `webp` / `gif`），
   然后执行 `npm run icons:manifest` 重建清单。
   **已就位**（2026-09-15 全局重排后）：`FGO头像` 452 张（`s_1~s_27`）、`Saber脸` 978 张（`s_28~s_33`）、
   `指令纹章` 204 张（`s_34~s_38`）、`礼装` 2453 张（`s_39~s_43`），各系列内 `i` 编号统一为 `1..N`；
2. **不需要**提供默认图标资源：未选图标时沿用前端内置默认（`actionTypeIcon.ts`）；
   16 个内置操作的图标**复用现有图库资源**（不再是 `s_101_*`，见 §5.5），无需额外准备；
3. 系列划分与每系列数量——**由目录结构自动推导**，无需提前声明；
   只需注意后端范围上限：`icon_series ≤ 999999`、`icon_id ≤ 99999999`。

### 5.5 内置操作（基础操作）默认图标——复用现有系列

内置操作的图标**不在前端硬编码**，由后端统一分配编号，且**不占用专属系列号**：

- 系列号：`BUILTIN_ACTION_ICON_SERIES = 1`
  —— 即复用现有系列 `FGO头像/s_1_saber`。因此内置动作不再保留 `101` 这类专属号，
  不会占用、也不会阻塞图库的全局连续编号（见 §5.1）；
- 编号表 `BuiltinActionIconId`（`app/models/execution/action_params.py`）：`1~16` 分别对应 `s_1` 的 `i_1~i_16`：

| 编号 | 操作 | 编号 | 操作 | 编号 | 操作 | 编号 | 操作 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | click 点击 | 5 | navigate 导航 | 9 | new_page 新页面 | 13 | print 打印参数 |
| 2 | input 输入 | 6 | screenshot 截图 | 10 | get_text 获取文本 | 14 | loop 循环 |
| 3 | wait 等待 | 7 | llm LLM | 11 | get_window 获取窗口 | 15 | composite 复合操作 |
| 4 | scroll 滚动 | 8 | hover 悬停 | 12 | fetch_external_data 获取外部数据 | 16 | if_else 条件判断 |

- `BuiltinActionType.icon` → `(1, 编号)`；`ActionMetadata` / `ActionMetadataResponse` 增加
  `icon_series` / `icon_id`，由 `/actions/registered` 一并返回；
- 前端链路：`/actions/registered` → `ToolboxPanel` 基础操作树渲染图标 →
  拖拽 payload 携带 `icon_series`/`icon_id` → `DroppedItem` → `ActionCard` 渲染
  （`ActionCard` 取 `action.icon_series ?? action.action_detail?.icon_series`）；
- 资源对应（当前已就位，无需改动）：`s_1_saber/i_1_阿尔托莉雅·潘德拉贡.png` … `i_16_兰斯洛特.png`。
  若日后想换成专属图标，把常量改指向其它**现有**系列即可（或新建系列并按 §5.1 编号规则排号）；
- **兜底**：对应资源缺失时前端回落内置类型图标（`resolveActionTypeIcon`），不报错、不空白。

## 6. 验收清单

1. 创建自定义动作时不选图标 → 落库 `0/0`，各处展示**内置默认图标**（沿用改造前后端既有默认）。
2. 选择某系列某编号 → 落库对应 int，工具箱/动作卡片/动作管理列表展示同一图标。
3. 直接改库把 `icon_series` 改成前端未支持的系列（如 `99`）→ 前端展示默认图标，不报错。
4. 请求传入超范围值（如 `icon_id = 100000`）→ 后端返回 422，不落库。
5. Fork 他人公开动作 → 新动作继承原图标。
6. 放入位图资源（如 `s_1_交互操作/i_2_抓取.png`）→ 选择器显示 `2 · 交互操作` 系列与 `#2 抓取`，选中后各处以 `<img>` 展示。
7. 文件名不带名称（如 `s_1_交互操作/i_3.svg`）→ 选择器只显示 `#3`，不报错。
8. 同一「系列+编号」同时放 `i_3.svg` 与 `i_3.png` → 以 SVG 为准。
9. 目录名不符合约定（如 `wrong/i_1_x.png`）→ 被忽略，不影响其他资源解析。
10. 资源放在分类目录下（如 `FGO头像/s_1_saber/i_100100_阿尔托莉雅.png`）→ 选择器能列出该系列与编号，
    标签显示系列名（多分类时带分类前缀）。
11. 两个分类下出现相同系列编号 → 开发态打印冲突告警（不是静默覆盖）。
12. 编号取实际值（如 `icon_id = 9946760`）→ 后端接受；超过 8 位（如 `100000000`）→ 422。
13. 未配置任何资源时 → 选择器显示目录指引；展示侧保留原有类型图标，不空白、不报错。
14. `/actions/registered` 返回的 16 个内置操作各自带 `icon_series = 1` 与**唯一** `icon_id`（1~16）。
15. 工具箱「基础操作」树中 16 个内置动作分别显示 `s_1` 的 `i_1~i_16`（阿尔托莉雅…兰斯洛特），
    `ActionCard` 同样显示该图标。
16. 对应资源缺失（如把 `s_1` 清空）→ 基础操作树与 `ActionCard` 回落内置类型图标（`resolveActionTypeIcon`），不报错。
