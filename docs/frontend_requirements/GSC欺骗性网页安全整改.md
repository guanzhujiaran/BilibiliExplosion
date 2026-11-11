# Google Search Console「欺骗性网页」安全整改

## 背景

GSC「安全问题」报告提示「欺骗性网页（社交工程）」，示例网址为「不适用」。核查线上 12 个收录页后确认：站点没有钓鱼表单、软件下载诱导、被注入脚本或隐藏关键词；问题是页面通篇使用 B 站（第一方）品牌与官方口径，却没有标示运营方与双方关系，命中 Google [第三方服务规范](https://developers.google.com/search/docs/advanced/security/social-engineering) 中的「标识不明的第三方服务」。

## 需求

1. 全站每个页面顶部显示**可见**的运营方品牌与关系声明，并给出「更多信息」链接。
2. 首页首屏、免责声明页、隐私政策页写明：本站为独立非官方第三方工具；本站账号登录（Casdoor / Gitee）不是 B 站登录；不索取 B 站账号、密码、SESSDATA、bili_jct 或任何 B 站 Cookie；不提供软件下载。
3. 去除 `<title>` / description / author / JSON-LD 里暗示 B 站官方身份的文案（尤其 bilibili 官方 slogan 与「B站官方抽奖信息集合」）。
4. 隐私政策补齐实际使用的第三方服务清单，修正「不与任何第三方分享」与实际脚本不符的描述。
5. 登录引导浮层不再仿 B 站登录口吻，明确「本站账号」；MCP 配置页把 `bili_jwt` 说明改为「本站网关签发的令牌，非 B 站 Cookie」。
6. 关闭预渲染 HTML 注入的视觉隐藏链接（cloaking 信号）。

## 明确不改

- GTM（`GTM-5DDL5WK8`）、Google AdSense（`ca-pub-5783205065512010`）、`Ads.txt`、相关 `preconnect` / `dns-prefetch` 与广告位配置一律保持原样；仅在隐私政策里如实披露。
- 站点名 `SITE_NAME`、主题色等品牌视觉保持原样，靠声明条与标题后缀明确第三方身份。

## 涉及文件

| 文件 | 改动 |
| --- | --- |
| `src/components/CommonCompo/Bili-Header-Compo/items/HeaderBarView.vue` | 全站页头身份声明条 + 免责声明链接 |
| `src/views/HomeView.vue` | 首屏身份说明、页脚免责声明 / 隐私政策链接 |
| `src/views/DisclaimerView.vue` | 新增「非官方第三方服务声明」章节与更多信息链接 |
| `src/views/PrivacyPolicyView.vue` | 新增身份与数据边界章节、第三方服务清单、修正共享条款 |
| `src/config/seo_routes.ts` | `SITE_SLOGAN` / `DEFAULT_DESCRIPTION` |
| `src/config/seo.ts` | 官方抽奖页、更新日志页描述 |
| `nuxt.config.ts` | `author` / `application-name`、`llmsTxt.directive.html = false` |
| `index.html` | Vite 遗留外壳的 `author` / `application-name` |
| `src/i18n/modules/common.ts` | 5 语言登录引导文案 + `loginTipAccountNotice` |
| `src/i18n/modules/generated.ts` | 5 语言首屏口号、身份说明、页脚法律页链接 |
| `src/components/login_page/compo/HeaderDropdownLoginTip.vue` | 登录浮层加本站账号说明 |
| `src/views/rpa-browser/RpaMcpConfigView.vue` | `bili_jwt` 输入框与提示文案 |

## 验收

1. `npm run check:route-root` 通过；新增 / 修改的 `.vue` 无 `<style>` 与 `:style` 绑定，样式走 `theme.css` 语义类。
2. `PRERENDER_API_TARGET=https://serena.dynv6.net npm run build` 后，检查 `dist/client/index.html` 与各收录页 HTML 含可见的身份声明，且不再有视觉隐藏链接。
3. 部署到站点根后，用 GSC「网址检查」分别查看移动版 / 桌面版，再提交安全审核请求。
