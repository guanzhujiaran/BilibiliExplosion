# 前端 SSG（构建期预渲染）计划书

> 目标：让搜索引擎与社交平台抓到**带真实内容的 HTML**。当前是纯 SPA，首屏 HTML 只有一个空 `<div id="app">`，
> 上一轮补的 SEO 标签（title / description / canonical / OG / JSON-LD）要等 JS 执行后才写入 DOM，
> 不执行 JS 的爬虫（Bing、多数社交分享抓取）什么都拿不到。

## 1. 方案选型

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

## 5. 验证方式

- `curl -s dist/client/index.html | grep -c "抽奖"`：预渲染产物必须含真实内容（而非只有骨架）；
- 每个 URL 对应 `dist/client/<path>/index.html` 存在且含 `<title>`、`canonical`、JSON-LD；
- 浏览器实跑：首屏 DOM 含内容、无 hydration mismatch 警告、切换路由 head 正常更新。
