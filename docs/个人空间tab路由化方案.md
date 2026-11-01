# 个人空间 tab 路由化（路由已改，组件拆分待执行）

## 已完成

`src/router/index.ts`：`/app/space/:mid` 改为**嵌套路由**（布局壳 + 4 条子路由）

| 路径 | name | 组件 |
| --- | --- | --- |
| `/app/space/:mid` | `MOMENT_USER_SPACE` | `MomentSpaceView.vue`（布局壳） |
| `/app/space/:mid`（空子路径） | `MOMENT_USER_SPACE_HOME` | `tabs/SpaceHomeTab.vue` |
| `/app/space/:mid/dynamic` | `MOMENT_USER_SPACE_DYNAMIC` | `tabs/SpaceDynamicTab.vue` |
| `/app/space/:mid/favlist` | `MOMENT_USER_SPACE_FAVORITES` | `tabs/SpaceFavoritesTab.vue` |
| `/app/space/:mid/settings` | `MOMENT_USER_SPACE_SETTINGS` | `tabs/SpaceSettingsTab.vue` |

注意：`tabs/*.vue` 四个文件尚未创建，当前状态跑不起来，必须先完成组件拆分。

## 待执行：组件拆分

### 1. `MomentSpaceView.vue` 改为布局壳
- 保留：用户资料头部、tab 栏、blocked 判断、SEO / 2.56.0 登录态与 302 逻辑
- 删除：四个 tab 的内容模板 + 各自业务逻辑
- 新增：`<router-view />` + `provide` 共享状态

### 2. 状态共享（provide/inject）
父组件拉取并 provide，子组件只读 + 通过事件请求父组件刷新。

| 状态 | 提供者 | 消费者 | 刷新时机 |
| --- | --- | --- | --- |
| `profile` / `spaceMid` / `isOwnSpace` | 父（loadProfile） | 全部 tab | 进入页面 / mid 变化 |
| `blocked` | 父 | 全部 tab（被拉黑只显示提示） | 同上 |
| `favFolders` / `showFavorites` | 父（loadFavorites） | FavoritesTab | 收藏 tab 挂载 / 增删改后 |
| 动态列表 `items` / `statusMap` | DynamicTab 自己 | — | tab 挂载时 |

关键约束：`favFolders` 由父持有，新建/编辑/删除收藏夹后 emit 给父重新 `loadFavorites()`，不要在子组件改本地副本。

### 3. 左侧导航用 el-menu（不再手写 router.push）
`<el-menu :router="true" :default-active="activeMenuIndex">`，`el-menu-item` 的 `index` 填相对路径
（`''` / `dynamic` / `favlist` / `settings`），点击自动 push，无需 switchTab。
高亮由 `route.name` 映射：`default-active` 绑 `activeMenuIndex` computed，删掉
`activeTab` / `resolvedActiveTab` ref。

### 3.1 收藏夹选中态走 query（对齐 B 站）
路径 `/app/space/:mid/favlist`，选中夹放 query：
- `fid`：收藏夹 id（可分享直达某个夹）
- `ftype`：收藏夹类型，`create` = 我创建的

点收藏夹 -> `router.push({ query: { fid, ftype: 'create' } })`；
组件内 `watch(() => route.query.fid)` 切换右栏内容；进入页面无 `fid` 时默认选 `isDefault` 的夹并回填 query。

### 4. 既有引用需同步
- `router.push({ name: 'MOMENT_USER_SPACE', params: { mid } })`（4 处：`UserBriefCell` / `UserCard` / `MomentFeedList` / `LotteryCommentItem`）指父路由会默认渲染主页；若想跳动态页要改成 `MOMENT_USER_SPACE_DYNAMIC`
- `src/config/seo.ts` 的 `MOMENT_USER_SPACE` SEO 配置需补 3 个子路由

## 执行顺序
1. 建 `src/views/moment/tabs/` 与 4 个组件骨架
2. 父组件改造：provide + 内容模板搬进对应子组件
3. 逐 tab 验证（主页 / 动态 / 收藏 / 设置）
4. 改 4 处跳转 + `seo.ts`
5. `vue-tsc` 复验

## 2.58.0 已落地（组件拆分完成）

新增文件：

| 文件 | 职责 |
| --- | --- |
| `tabs/spaceContext.ts` | `provide/inject` 契约：`MomentSpaceContext` + `useMomentSpace()` |
| `tabs/SpaceHomeTab.vue` | 主页（数据总览占位 + 个人简介） |
| `tabs/SpaceDynamicTab.vue` | 动态列表（私有状态：items / statusMap / 分页 / 点赞 / 删除） |
| `tabs/SpaceFavoritesTab.vue` | 收藏（左栏收藏夹 + 右栏内容 + 增删改弹窗） |
| `tabs/SpaceSettingsTab.vue` | 设置（主页展示收藏开关） |

与原计划不一致 / 补充的实现决策：

1. **el-menu 用具名路由跳转，不用相对路径**：`:router="true"` 时 element-plus 执行的是
   `router.push(index)`，而 vue-router 对 `'dynamic'` 这种相对串会解析成**兄弟路径**
   （`/app/space/123` → `/app/space/dynamic`），且 `''` 根本不会导航。
   因此 `index` 只作高亮键，跳转改用 `:route="{ name, params: { mid }, query: {} }"`。
2. **收藏夹选中态走 query**：`?fid=xxx&ftype=create`；无 / 失效 fid 时选中 `isDefault`
   的夹并 `router.replace` 回填，收藏夹列表变化（新建 / 删除 / 他人公开状态变化）时兜底修正。
3. **状态归属**：`favFolders` / `showFavorites` / `blocked` / 空间资料全在布局壳；
   子组件增删改收藏夹后调 `refreshFavorites()` 重新拉取，不在本地改副本。
   布局壳用 `profileVersion`（资料重载）/ `dynamicVersion`（发布成功）通知子 tab 重拉，
   子 tab 记录 `loadedVersion`，首屏那次自增被吸收，不会重复请求。
4. **落地页统一 = 空间主页（空子路径）**：点头像 / 用户名 / 头像下拉「个人空间」进入，
   一律落到主页，跳转必须用**子路由 name** `MOMENT_USER_SPACE_HOME`：
   vue-router 解析 `{ name: 'MOMENT_USER_SPACE' }` 只匹配到壳路由（`matched = [父]`），
   不带空子路由 → 壳内 `<RouterView>` 渲染不出内容（白屏）。
   为此 `SpaceHomeTab` 不再做「他人空间自动跳动态」的兜底，他人空间 tab 栏也补上「主页」入口
   （对齐 B 站：主页 / 动态 / 收藏），保证落地后有对应 tab 高亮。
   `/app/space`（无 mid，2.56.0 登录态归位入口）也 `replace` 到 `/app/space/{uid}`（主页），
   并把 `MOMENT_MY_SPACE` 一并映射到主页高亮，避免归位前高亮闪到「动态」。
5. **顺带修掉两个旧问题**：
   - `App.vue` 的 `routeViewKey` 对嵌套路由取**父路由 path**，`/app/space/1` 与
     `/app/space/2` 复用同一个 keep-alive 实例（`onMounted` 不再触发）。现在补了
     `watch(route.params.mid)` + `onActivated`，按 mid 去重后补加载。
   - 旧模板里收藏 tab 的右栏内容写在 `<section>` 之外（已修正结构）。
6. **跳转点清单**（共 7 处，全部指向主页 `MOMENT_USER_SPACE_HOME`）：
   `UserBriefCell` / `UserCard` / `MomentFeedList` / `LotteryCommentItem` /
   `TopicFeedView` / `MomentDetailView` / 动态卡片内头像跳转。
7. `seo.ts` 补齐 4 条子路由描述；`MOMENT_USER_SPACE` 保留。

体检结果：`npm run check:route-root`（5 个空间相关组件全部通过）、
`npx vue-tsc --noEmit`（本次改动文件 0 错误，仓库内其余报错为改动前既有问题）。

