# 前端 SSG（构建期预渲染）计划书

> 目标：让搜索引擎与社交平台抓到**带真实内容的 HTML**。当前是纯 SPA，首屏 HTML 只有一个空 `<div id="app">`，
> 上一轮补的 SEO 标签（title / description / canonical / OG / JSON-LD）要等 JS 执行后才写入 DOM，
> 不执行 JS 的爬虫（Bing、多数社交分享抓取）什么都拿不到。

## 0. 方案变更（最终形态：无头浏览器预渲染）

> 下文 §1~§7 是最初的「Vike renderToString（SSR/SSG）」方案与实施记录，仍然有效但**已被替换**——
> 因组件里大量浏览器 API + 数据都在 `onMounted` 里取，Node 端渲染要额外做 SSR 兼容改造，成本偏高。
> 现改为**构建后用无头浏览器抓取**，SSR 兼容那层全部不需要。

**当前流程**：`vike build --mode prod`（产出前端资源）→ `node scripts/prerender.mjs`
（起 `vike preview`：按 `renderer/+onRenderHtml.ts` 输出外壳 HTML 并把 `/api` 反代到后端 →
Playwright 逐个打开收录 URL → 等首屏渲染出内容 → 把渲染后的 DOM 连同页面实际加载到的数据
写回 `dist/client/<path>/index.html`）。

**实测验证（2026-09-21）**

```
PRERENDER_API_TARGET=https://serena.dynv6.net npm run build
→ 客户端 ✓ built / ✓ built，预渲染 10/10 成功
→ 产物数据核对：official 页 total=345、首条 opus/1247774079235129382
   与生产接口「相同筛选参数」返回完全一致（生产 total=32081 是本页默认筛选前的总数）
→ preview 的 /api 代理探测 total=32081 = 生产（不是本地 30511），确认数据源正确
→ 浏览器（Playwright）：首屏快照即渲染、客户端刷新后「筛选结果 345」、无 hydration/mismatch
   报错；屏蔽第三方脚本后零 PAGEERROR
```

**健壮性**：列表请求失败时**不再清空已有列表**（`clearOnlyWhenEmpty`）——
首屏可能来自静态快照，若因一次网络抖动就清零，页面反而比 SPA 更差。

| 关注点 | 做法 |
| --- | --- |
| 数据进 HTML | 页面正常在浏览器里跑（`onMounted` 照旧），DOM 快照天然带数据 |
| 首屏不闪 / 不重复请求 | 采集：`collectSsrData()`（`VITE_PRERENDER_COLLECT=1` 时生效）→ 脚本读 `window.__PRERENDER_DATA__` → 注入为 `window.__SSR_DATA__` → 客户端 `loadSsrData()` 复用 |
| 水合 | 客户端用 `createApp().mount()`（非 hydrate），Vue 接管并重建 DOM，**没有水合不匹配** |
| Vike 的角色 | 只提供 SPA 外壳（`ssr: false` / `prerender: false`）+ 客户端入口注入 + dev/preview；路由仍由 vue-router 负责（catch-all `/*`） |
| 预渲染清单 | `src/config/seo_routes.ts`，与 sitemap / robots 同源 |
| 环境变量 | `PRERENDER_API_TARGET`（默认 `http://localhost:9923`）、`PRERENDER_CHROMIUM`（自定义 chromium 路径）、`PRERENDER_SKIP_THIRD_PARTY=0`（不屏蔽第三方脚本） |

**前提**：构建与预渲染都需要后端在线（hey-api 生成 SDK 要拉本地 `openapi.json`；预渲染要真实接口数据）。

### 数据源策略（重要）

HTML 里的数据来自 `PRERENDER_API_TARGET`，且是**构建时刻的快照**：

- **生产构建必须指向生产接口**，否则会把本地开发库的数据写进上线产物：
  ```bash
  PRERENDER_API_TARGET=https://serena.dynv6.net npm run build
  ```
  脚本在检测到目标仍是 `localhost` 时会打印醒目告警。
- **客户端加载后仍会重新拉取最新数据**（快照只用于首屏渲染，不会让用户停在旧列表）。
- 因此快照的时效 = 构建频率，建议把预渲染纳入发布流程，或按需定时重建。
- 需要登录态的页面可用 `PRERENDER_COOKIE` 带凭证抓取；当前清单里的页面都是匿名可读
  （已实测生产接口 `GetOfficialLottery` / `GetReserveLottery` / `GetChargeLottery` /
  `GetTopicLottery` 匿名返回 200）。

**因此已删除/回滚的东西**：`onServerPrefetch` 预取、`src/app/ssr_shim.ts`、createApp 的 ssr 分支、
服务端 `baseUrl`、Element Plus SSR provider。SSR 兼容相关的 `typeof window` 判断予以保留（无害，
且以后若要上真 SSR 可直接复用）。

## 1. 方案选型（原 SSR/SSG 方案，已弃用）

| 决策项 | 结论 | 理由 |
| --- | --- | --- |
| SSR 还是 SSG | **SSG（prerender）** | 生产是静态托管 dist、无常驻 Node 进程；SSG 输出静态 HTML，SEO 效果等价，部署不变 |
| 框架 | **Vike**（`vike` + `vike-vue`） | `vite-plugin-ssr` 已停止维护并更名为 Vike；Vike 原生支持 `prerender: true` + 参数化路由 URL 列表 |
| 路由 | **保留 vue-router**，Vike 用 catch-all 路由承接 | 现有路由表 27KB、含大量守卫 / meta / keep-alive 策略，迁到 Vike 文件系统路由成本过高 |
| 渲染器 | **自定义 `+onRenderHtml` / `+onRenderClient`**（不直接套用 vike-vue 默认实现） | 需要：① 以现有 `index.html` 为 HTML shell（保住 GTM / Adsense / busuanzi 脚本）；② 复用 `@vueuse/head`（现有 SEO 逻辑零改造）；③ 按 URL 白名单决定是否真 SSR |
| 覆盖范围 | **先 SEO 关键页面**，其它页面输出「空壳 + meta」 | 用户中心 / RPA / 消息 / 管理端本就 `noindex`，且大量依赖浏览器 API，SSR 收益为负 |

## 2. 架构

```
src/
  pages/
    +route.ts                     # catch-all：'/*'（所有 URL 命中同一 Vike page）
    +Page.vue                     # 只渲染 <App/>（App.vue 内含 RouterView + keep-alive）
    +onBeforePrerenderStart.ts    # 构建期返回要预渲染的 URL 列表（SEO 白名单）
  renderer/
    +config.ts                    # prerender: true / clientRouting: true / ssr 白名单策略
    +onRenderHtml.ts              # 服务端：白名单 URL → renderToString；其余 → 空壳 + head
    +onRenderClient.ts            # 客户端：createApp + router.push + mount（幂等，支持后续导航）
  app/
    createApp.ts                  # 两端共用的 app 工厂（pinia / router / i18n / head / 图标）
```

**关键设计**

1. **SSR 白名单**：`src/config/seo.ts` 导出 `SEO_PRERENDER_ROUTES`（与 `vite-plugin-sitemap` 的 `SEO_INDEXABLE_ROUTES` 同源）。
   白名单内 → `renderToString` 真渲染；白名单外 → 只输出 HTML shell + head（等价 SPA 空壳），避免为登录页 / 浏览器 API 页面做 SSR 改造。
2. **head 两套机制不冲突**：
   - 预渲染 HTML 的 head：由 `@vueuse/head` 的 `renderHeadToString()` 在 `+onRenderHtml` 里注入（复用现有 `useRouteSeo` 全部逻辑）；
   - 客户端运行后：Vike 注入的静态 SEO 标签带 `data-seo-ssr`，由 `useRouteSeo` 在挂载时移除，交回 `@vueuse/head` 按路由动态维护。
3. **数据预取**：白名单页面当前在 `onMounted` 拉数据 → SSR 时不会执行，HTML 仍是空壳。
   需为这些页面补 `onServerPrefetch(() => loadXxx())`（客户端仍走 onMounted，现有 `loadSeq` 保证幂等）。
4. **clientRouting 幂等**：Vike 开启客户端路由后，站内 `<a>` 与 `router-link` 都可能触发 `onRenderClient`。
   实现里若目标 URL 与 `router.currentRoute` 一致则不重复 push，避免双重导航。
5. **HTML shell 仍用 index.html**：以 `?raw` 读入并替换 `<div id="app">` 内容、移除旧的 `/src/main.ts` 入口脚本，
   由 Vike 自动注入 client entry 与 preload。

## 3. 分阶段

| 阶段 | 内容 | 验收 |
| --- | --- | --- |
| P1（本轮） | 装依赖、Vike 插件与 CLI、pages/renderer 骨架、SEO 清单同源、首页预渲染跑通 | `vike build` 产出 `dist/client/index.html`，其中含首页真实内容 + 完整 SEO 标签 |
| P2 | 白名单页面补 `onServerPrefetch`；浏览器 API（localStorage / Clarity / Casdoor / vditor / flv.js / echarts）SSR 隔离 | 关键页面 HTML 含列表/详情真实数据 |
| P3 | 全量页面输出（白名单外为空壳）、`vite-plugin-sitemap` 与预渲染清单同源、nginx 静态托管验证 | 每个 URL 有对应 HTML；`curl` 可见内容；sitemap 与预渲染清单一致 |

## 4. 风险与回滚

- **风险**：SSR 期间访问 `window/document/localStorage` 直接崩溃 → 用白名单 + 空壳兜底，把影响面锁在少数页面；逐页开启。
- **风险**：水合不匹配（客户端与服务端 DOM 不一致）→ 主题/尺寸等依赖 localStorage 的初始化只在客户端执行，服务端用默认主题。
- **回滚**：Vike 只新增文件 + 改 `vite.config.ts`/`package.json` scripts；出问题把 scripts 改回 `vite`、移除 `vike()` 插件即回到纯 SPA。

## 5. P1 实施记录（已跑通）

**产物**：`vike build` 输出 10 个静态 HTML（`dist/client/index.html` 及各页面目录 `index.html`），
纯静态托管即可（Vike 提示 "your app is fully pre-rendered and can be statically deployed"）。

| 页面 | 预渲染 title | canonical |
| --- | --- | --- |
| `/` | 爆破哔哩哔哩弹幕视频网 - ( ゜- ゜)つロ 乾杯~ - bilibili | `https://serena.dynv6.net/` |
| `/app/lot-data/bili-data/official` | 官方抽奖 - B站抽奖数据 - 爆破哔哩哔哩弹幕视频网 | 对应路径 |
| 其余 8 个页面 | 各自「页面 - 父级 - 站点名」 | 对应路径 |

**浏览器实测**：首屏水合后 `description / canonical / og:title` 各 1 份（无重复）、静态兜底标签清零；
SPA 跳转到 `/app/lot-data/bili-data/official` 后 title 变为「官方抽奖 - ...」，说明客户端 head 由
`useRouteSeo` 正常接管；无 hydration mismatch 报错。

**踩坑与修复（同类页面改造时直接复用）**

1. `App.vue`：`window.innerHeight` / `outerWidth` 在 setup 顶层访问 → SSR 安全化；
   `isInit` 在 SSR 下必须为 `true`（否则 HTML 只有加载遮罩）；
   `el-dialog` 类弹层只在 `isMounted` 后渲染。
2. `ScrollButtons.vue` / `LoadingMoreContainer.vue`：`window.innerHeight` 初始化 → SSR 按 0 处理。
3. `@vueuse/head` 的 `renderHeadToString()` 是**异步**的，必须 `await`（漏了会注入 `undefined`）。
4. Element Plus SSR 需要 `ID_INJECTION_KEY` / `ZINDEX_INJECTION_KEY` 两个 provider。
5. urql 必须在服务端也安装 provider（山姆页直接 `useQuery`，缺 provider 会抛错）。
6. `src/app/createApp.ts` 里 `type App` 与 `import App from '@/App.vue'` 同名 → dev（esbuild）报
   "Identifier App has already been declared"，必须给 Vue 的 `App` 类型取别名。
7. `vike dev` 默认端口 3000 → 在 `vite.config.ts` 固定 `server.port: 5173`，保持与 nginx 反代一致。
8. 多个 pinia store 在**模块加载期**就引用 `localStorage` → `src/app/ssr_shim.ts` 兜底（过渡方案）。

**已知待办**：Element Plus 仍打印 `IdInjection / ZIndexInjection` 警告（疑似 element-plus 被打成两份，
待用 `resolve.dedupe` 或 `ssr.noExternal` 收敛）；页面正文目前不含接口数据（P2 补 `onServerPrefetch`）。

## 6. P2 实施记录（真实数据进 HTML）

**做法**：`src/app/ssrData.ts` 提供「服务端预取 → 序列化进 HTML → 客户端首屏复用」的快照机制。

- 页面组件：`onServerPrefetch()` 里拉数据 + `setSsrData(key, 快照)`；
- 数据消费方（`useLotteryData`）：初始化时 `getSsrData(key)`，有值即用，并返回 `hydratedFromSsr` 让 `onMounted` **跳过重复请求**；
- `+onRenderHtml.ts`：渲染前 `clearSsrData()`（每页独立），渲染后把快照写成 `window.__SSR_DATA__`（`<` 转义防脚本提前闭合）；
- `+onRenderClient.ts`：创建应用**之前** `loadSsrData(window.__SSR_DATA__)`，保证首屏与服务端一致。

**结果**（预渲染 HTML 正文长度，改造前均约 650 字符）

| 页面 | 正文长度 | 下发数据 |
| --- | --- | --- |
| 官方抽奖 | 656 → **60040** | 筛选参数 14 项 + 列表 10 条（total 30511） |
| 充电抽奖 | → **29435** | 14 项 + 10 条（total 26102） |
| 预约抽奖 | → **11141** | 14 项 + 10 条（total 60831） |
| 话题抽奖 | → **7249** | 14 项 + 10 条（total 27） |

**浏览器实测**：`window.__SSR_DATA__` 存在、列表首屏即为服务端数据、**无 hydration mismatch**、
title 正确；SPA 跳转 head 仍由 `useRouteSeo` 正常接管。

**附带修复**：`runtime_config.ts` 在 SSR 下改用绝对 `baseUrl`（`VITE_SSR_API_BASE`，默认本地网关
`http://localhost:9923`，因为 Node 无法请求相对 URL）；`useLotteryData` 的轻提示改为 SSR 安全的
`notifyError`（服务端没有 DOM）。

**P2 未覆盖**（后续可再加）：名人堂（数据由懒加载子组件驱动）、爬虫状态页、山姆会员店（GraphQL）、
以及动态详情类页面（`?dynId=` / `?lottery_id=` / `/app/moment-detail/:id`：URL 无法穷举，
纯静态托管下无法预渲染，需要真 SSR 服务才能覆盖，届时可复用同一套 `ssrData` 机制）。

## 7. 验证方式

- `curl -s dist/client/index.html | grep -c "抽奖"`：预渲染产物必须含真实内容（而非只有骨架）；
- 每个 URL 对应 `dist/client/<path>/index.html` 存在且含 `<title>`、`canonical`、JSON-LD；
- 浏览器实跑：首屏 DOM 含内容、无 hydration mismatch 警告、切换路由 head 正常更新。
