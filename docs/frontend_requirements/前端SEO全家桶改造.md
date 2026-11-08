# 前端 SEO 改用 @nuxtjs/seo 全家桶

## 需求

前端原有一套半自研 SEO：`useRouteSeo.ts` 手写 `useHead` 拼 18 个 meta / canonical /
JSON-LD `<script>`，`index.html` 放静态兜底标签，`public/robots.txt` 手写，
`@nuxtjs/sitemap` 独立注册。现要求改成**直接用 `@nuxtjs/seo` 做完整的 SEO**，
站点级与页面级标签、结构化数据、robots / sitemap / 社交图 / 链接检查 / AI 可读性
统一交给全家桶，业务层只保留文案与节点差异。

## 范围

- Nuxt 4.6.1 SSG（`nuxt generate` + nginx 静态托管），预渲染白名单仍是
  `src/config/seo_routes.ts` 的 `SEO_INDEXABLE_ROUTES`。
- 站点级常量（域名 / 站点名 / 默认描述 / 默认关键词 / 语言 / canonical query 白名单）
  集中在 `src/config/seo_routes.ts`，供 `nuxt.config.ts` 与运行时代码共用。
- 业务文案（`ROUTE_SEO`、`usePageSeo` 的 7 个页面级覆盖）与列表页 `ItemList` /
  详情页 `SocialMediaPosting` / 面包屑节点保留，但改为 Schema.org 节点（不带 `@context`）。

## 模块职责（全部由 `@nuxtjs/seo` 一键安装）

| 配置键 | 职责 |
| --- | --- |
| `site` | 权威域名、站点名、描述、`defaultLocale`、`separator`、`trailingSlash`；全家桶据此生成绝对 URL 与 `<html lang>` |
| `seo` | 标题模板 `%s - 站点名`、canonical 默认规则（query 白名单）、`og:url` / `og:site_name` / OG-Twitter 默认标签、站点级 meta；`useRouteSeo` 再显式维护一份响应式 canonical / og:url，保证 SPA 导航后也更新 |
| `robots` | `robots.txt`（`disallow`）；页面级 `<meta name="robots">` 由 `useSeoMeta()` 统一输出（`metaTag: false`） |
| `sitemap` | `sitemap.xml`；与预渲染白名单同源，保留 lastmod / changefreq / priority |
| `schemaOrg` | `WebSite` / `WebPage` / `Organization` 默认图 + `@graph` / `@context`；页面级 `useSchemaOrg()` |
| `ogImage` | `zeroRuntime: true`；静态分享图 `public/og-image.png` + `og-image.alt.txt` 由 seo-utils 注入 |
| `linkChecker` | 预渲染后扫描站内死链，只报告不阻断发布 |
| `aiReady`（默认） | `/llms.txt`、`/llms-full.txt`、每页 `.md`、Markdown 版 link 标签 |
| `skewProtection` | 关闭：纯静态 nginx 托管不需要版本轮询，避免历史 hash 资源混入 `dist` |

### 按官方 guide 追加的优化

- **无需额外 nginx 配置**：robots 模块的 `X-Robots-Tag` 只在 Nitro 服务端发送，但预渲染 HTML 里的
  `<meta name="robots">` 已由 `useSeoMeta()` 在构建期写入（SPA 导航也会更新），`robots.metaTag: false`
  避免模块重复输出；静态托管不需要补 header。
- **`sitemap.zeroRuntime: true`**：预渲染 sitemap 并移除运行时 sitemap 代码（官方静态站点推荐）。
- **`linkChecker.failOnError: true`**：把死链检查升级为发布门禁（外链不抓取，不受第三方波动影响）。
- **`og:image:secure_url`**：seo-utils 自动生成 `og:image` 时不带该字段，由 `useSeoMeta()` 补齐。
- `site.twitter` 未配置：项目没有 X/Twitter 账号，不输出虚假的 `twitter:site` / `twitter:creator`。

## 界面 / 行为不变项

- 标题口径仍是「官方抽奖 - B站抽奖数据 - 爆破哔哩哔哩弹幕视频网」，首页仍是完整品牌标题；
- 列表页 description 仍带实时收录条数，详情页仍按接口内容覆盖标题与描述；
- 登录 / 管理员 / 404 / 缺 `id` / `dynId` 的详情页仍 `noindex,nofollow`；
- 全站跳转 no-referrer 兜底不变（`index.html` 的 `<meta name="referrer">` 与 `linkPolicy.ts`）。

## 验收

1. `nuxt prepare` 通过，`#imports` 中存在 `useSeoMeta` / `useRobotsRule` / `useSchemaOrg`；
2. `nuxt generate` 产出各收录页 HTML，且 `<head>` 内只有一份 title / description / canonical /
   robots，含 `og:*` / `twitter:*` / `application/ld+json` / llms 链接；
3. 产物存在由模块生成的 `robots.txt`（含 disallow 与 sitemap 链接）、`sitemap.xml`、
   `llms.txt`；仓库里不再有静态 `robots.txt` 与 `data-seo-static` 标签；
4. 首页 JSON-LD 含 `WebSite` / `WebPage` / `Organization`，列表页含 `BreadcrumbList` +
   `ItemList`，详情页含 `SocialMediaPosting`；
5. 浏览器实跑：SPA 路由切换后标题 / 描述 / 结构化数据随路由变化，无 hydration 报错。

## 依赖约束（npm 特有）

- `@nuxtjs/seo` 通过 Nuxt 的 `moduleDependencies` 从**项目根** `node_modules` 解析子模块；
  npm 会把 `nuxt-og-image` / `nuxt-schema-org` / `nuxt-seo-utils` 嵌套到
  `@nuxtjs/seo/node_modules`（因 Unhead 版本冲突），导致 `nuxt prepare` 报
  `The module nuxt-og-image could not be loaded`。因此这三个包必须显式装成顶层依赖，
  版本不低于 `@nuxtjs/seo` 的 `moduleDependencies` 要求；
- 已卸载遗留的 `@vueuse/head`（源码零引用），它把 `@unhead/vue` 锁在 1.x，
  与全家桶要求的 3.4.2+ 冲突；
- 升级 `@nuxtjs/seo` 时，这四个包版本需一起对齐。
- `nuxt generate` 是纯静态输出：AI Ready 生成的 `.md` 页面与 `<link rel="alternate">` 可用，
  但 `Accept: text/markdown` 的 307 协商中间件需要常驻 Node 服务，静态托管下不生效（构建会提示）。
