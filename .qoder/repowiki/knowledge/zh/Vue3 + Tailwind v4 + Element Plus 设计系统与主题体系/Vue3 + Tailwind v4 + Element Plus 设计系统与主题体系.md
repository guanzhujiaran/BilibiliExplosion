---
kind: frontend_style
name: Vue3 + Tailwind v4 + Element Plus 设计系统与主题体系
category: frontend_style
scope:
    - '**'
source_files:
    - Vue3FrontEndDemoExercise/src/assets/theme.css
    - Vue3FrontEndDemoExercise/src/assets/app-tailwind.css
    - Vue3FrontEndDemoExercise/vite.config.ts
    - Vue3FrontEndDemoExercise/package.json
    - Vue3FrontEndDemoExercise/src/stores/theme.ts
    - Vue3FrontEndDemoExercise/src/stores/hue_theme.ts
---

## 1. 使用的系统/框架

- **前端框架**：Vue 3 + Vite（`vite.config.ts`），使用 `@vitejs/plugin-vue`、`@vitejs/plugin-vue-jsx`。
- **样式方案**：Tailwind CSS v4（`tailwindcss: ^4.3.3`，通过 `@tailwindcss/vite` 插件集成），配合 `daisyui` 作为组件级扩展，以及 `@tailwindcss/typography` 排版插件。
- **UI 组件库**：Element Plus（`element-plus`），通过 `unplugin-vue-components` + `ElementPlusResolver` 按需自动注册；同时引入 `@headlessui/vue`、`@heroicons/vue` 等轻量 UI 包。
- **图标方案**：`unplugin-icons` + `unplugin-auto-import`，按 `Icon` 前缀自动导入 SVG 图标（启用 `ep` 集合即 Element Plus Icons）。
- **主题持久化**：Pinia store（`src/stores/theme.ts`、`hue_theme.ts`）+ `pinia-plugin-persistedstate`，将主题模式与色相主题写入 localStorage。
- **国际化**：`vue-i18n`，文案集中在 `src/i18n/`。

## 2. 关键文件

- `Vue3FrontEndDemoExercise/src/assets/theme.css` — 全局设计令牌（spacing / radius / text / color / gradient / animation 变量），并通过 `@theme { ... }` 语法注入 Tailwind v4 的 theme 层。
- `Vue3FrontEndDemoExercise/src/assets/app-tailwind.css` — 入口样式，声明 `@layer base, element, utilities, theme, elementDark, components`，加载 Element Plus 亮/暗主题、DaisyUI、Typography，并集中定义业务类（渐变背景、等级色、搜索框、cyber 风格、抽奖卡片特效等）。
- `Vue3FrontEndDemoExercise/vite.config.ts` — 构建配置：Tailwind v4 插件、SVG loader（禁用 svgo）、Sitemap、AutoImport、Components（ElementPlusResolver）、hey-api OpenAPI → SDK 生成。
- `Vue3FrontEndDemoExercise/package.json` — 依赖清单，确认 Tailwind v4、Element Plus、DaisyUI、unplugin-*、hey-api 等工具链。
- `Vue3FrontEndDemoExercise/src/stores/theme.ts` — 明/暗/自动主题切换，基于 `@vueuse/core` 的 `useDark`，通过给 `<html>` 添加 `light/dark` class 驱动。
- `Vue3FrontEndDemoExercise/src/stores/hue_theme.ts` — 运行时动态覆盖 Element Plus 各语义色（primary/success/warning/danger/error/info）为任意 hue，支持历史记录与随机生成。
- `Vue3FrontEndDemoExercise/.eslintrc.cjs`、`.prettierrc` — 代码风格规范（ESLint + Prettier）。

## 3. 架构与设计约定

### 设计令牌（Design Tokens）
所有视觉常量集中在 `theme.css` 的 `@theme` 块中，以 CSS 自定义属性形式暴露：
- 间距：`--spacing-base` 为 4px 基准，派生 `--spacing-1`…`--spacing-40`。
- 圆角：`--radius-xs`…`--radius-full`。
- 字号/行高：`--text-xs`…`--text-5xl`、`--leading-*`。
- 颜色：统一映射到 Element Plus 的 `--el-color-*` 变量（primary/success/warning/danger/error/info 及其 light/dark 变体），并额外定义业务渐变（`--color-gradient-module-*`、`--color-gradient-hero-*`、`--color-gradient-bili-data`、`--color-gradient-lottery-item`、`--color-gradient-shopping`）。
- B 站用户等级色：`--color-level-0..6-from/to/track`，用于经验条与徽章。
- 动画：`--animate-sidenav-jelly`、`--animate-sidenav-wobble` 等。

这些 token 被 `app-tailwind.css` 的 `utilities` 层以 `.bg-gradient-*`、`.bili-level-bg-*`、`.bili-level-fill-*`、`.bili-level-track-*` 等 utility 类暴露给组件使用。

### Element Plus 深度定制
通过覆盖大量 `--el-*` CSS 变量（尺寸、字体、圆角、菜单高度、按钮高度、表单间距、通知宽度、抽屉圆角、popover 内边距、分页字号、tag 字号、switch 核心高度、loading spinner 大小等），使 Element Plus 组件在尺寸、圆角、字号上完全对齐项目的设计系统。`theme.css` 中明确注释“Element Plus 组件尺寸覆盖”“Element Plus 字体大小覆盖”“Element Plus 间距覆盖”。

### 主题系统
- **明/暗模式**：`theme.ts` 用 `useDark({ selector: 'html' })` 在 `<html>` 上切换 `light/dark` class；`app-tailwind.css` 通过 `@custom-variant dark (&:where(.dark, .dark *))` 提供 Tailwind 的 `dark:` 变体。
- **色相主题**：`hue_theme.ts` 运行时把 `--el-color-{role}` 指向 Tailwind 的 `--color-{hue}-*` 变量，实现一键换肤（red/orange/amber/yellow/lime/green/emerald/teal/cyan/sky/blue/indigo/violet/purple/fuchsia/pink/rose 共 17 种 hue）。
- **持久化**：主题模式存于 `localStorage` 的 `theme-store` 键，色相主题历史存于 `el-theme-store`。

### 响应式策略
- 基于 Tailwind 断点（`sm:`、`md:`、`lg:`）进行布局调整，例如 `.bili-lottery-card-arr-container` 使用 `gap-5 sm:gap-3 md:gap-4 lg:gap-6` 和 `grid-template-columns: repeat(auto-fit, minmax(min(100%, 28rem), 1fr))` 实现自适应网格。
- 安全区适配：`.safe-area-padding` 使用 `env(safe-area-inset-*)` 处理刘海屏。

### 样式组织
- 通过 `@layer` 分层：`base`（html/body 重置）、`element`（Element Plus 样式）、`utilities`（业务 utility 类）、`theme`（Tailwind 自定义主题）、`elementDark`（暗色覆盖）、`components`（业务组件样式如 lottery card、search box、cyber 风格）。
- 顺序保证后声明层优先级更高，便于覆盖第三方组件样式。

### 图标与资源
- SVG 图标通过 `unplugin-icons` 自动导入，统一使用 `IconXxx` 形式。
- 业务 SVG 资源位于 `src/assets/svgs/`（audit、dynamic/detail/side_toolbar、space 等目录）。
- 图片与文本常量集中在 `src/assets/img/BiliImg.ts`、`src/assets/text/BiliCommTxt.ts`、`BiliErrorTxt.ts`。

## 4. 约定与约束

- **禁止直接写死颜色/尺寸**：应优先使用 `theme.css` 中定义的 `--spacing-*`、`--radius-*`、`--text-*`、`--color-*` 变量，或对应的 Tailwind utility（如 `bg-gradient-module-primary`、`bili-level-bg-3`）。
- **Element Plus 组件样式修改必须通过 CSS 变量覆盖**（`--el-*`），而非直接写死像素值，以保证主题一致性。
- **暗色模式**：通过给 `<html>` 添加 `dark` class 驱动，组件中使用 Tailwind 的 `dark:` 变体；`app-tailwind.css` 中已预置 `elementDark` 层确保暗色下 Element Plus 样式正确覆盖。
- **业务类命名**：业务专属样式集中在 `app-tailwind.css` 的 `@layer components` 中，采用语义化类名（如 `.lottery-card-grand-prize`、`.universal-search-box`、`.fingerprint-cyber-container`、`.console-side-nav-menu`），避免散落在组件内部。
- **图标基线对齐**：`.bili-icon` 统一设置 `display:inline-block; line-height:1; vertical-align:baseline`，解决 SVG 图标在文本流中的基线间距问题。
- **构建产物**：Tailwind v4 通过 `@tailwindcss/vite` 插件在构建时扫描源码生成样式，无需传统 `tailwind.config.js`，主题全部由 `theme.css` 的 `@theme` 块声明。
- **代码风格**：ESLint（`@vue/eslint-config-typescript` + `eslint-plugin-vue`）+ Prettier（含 `prettier-plugin-tailwindcss`）在 `package.json` scripts 中提供 `lint`、`format` 命令。
- **OpenAPI 客户端生成**：通过 `@hey-api/vite-plugin` 从后端 OpenAPI 文档自动生成 TypeScript SDK（输出至 `src/api/*/hey-api`），并按 tag 拆分为 `*Service` 类，保持 API 调用类型安全。

## 5. 适用性说明

该风格体系仅存在于 `Vue3FrontEndDemoExercise` 子模块中，是本项目的前端单页应用；仓库其余部分（RPA-Browser、be-bilibili-crawler、be-gateway、be-message-service 等）均为后端服务，不包含前端样式代码。因此本卡片仅适用于 Vue 前端工程。