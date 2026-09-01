# 前端 i18n 全量改造计划书

## 目标
将前端所有硬编码中文文案提取为 i18n key，支持 5 种语言：
- `zh-CN` 简体中文（默认）
- `en` English
- `zh-TW` 繁體中文
- `ja` 日本語
- `ko` 한국어

## 架构
- 方案：`vue-i18n`（legacy:false），在 `src/main.ts` 注册
- 命名空间模块：`src/i18n/modules/*.ts`（common / generated / user / changelog / lottery / callback / sams / message / rpa / moment / admin 等）
  - `generated.ts` 为业务文案统一归集（含 userNs / changelogNs / lotteryNs / callbackNs / samsNs / messageNs 常量）
- 汇总：`src/i18n/index.ts`，导出 `SUPPORTED_LOCALES`、`LOCALE_LABELS`
- 切换与持久化：`src/stores/locale.ts`（localStorage key `app-locale`，默认检测 `navigator.language`）
- 切换器：`src/components/CommonCompo/LanguageSwitcher.vue`（Header 中挂载），Element Plus locale 通过 `el-config-provider` 联动
- 文案替换：使用 `useI18n()` 的 `t()`；插值 `t('key', {param})`；动态映射（状态/类型/权限）尽量改为 i18n，或在 .ts 内提供多语言函数
- 约定：各语言 key 集合必须一致；语义化 Tailwind 类保持不变；禁止新增 `<style>`/内联样式

## 语言切换方式
顶部切换器（Header 下拉） + 持久化（localStorage）。默认跟随浏览器语言（navigator.language 映射）。

## 分阶段实施
- [x] Phase 0: 搭建 i18n 基础设施（createI18n、store、切换器、el-config-provider 联动、main.ts 注册）
- [x] Phase 1: common 命名空间（通用按钮/标题等）
- [x] Phase 2: 根 views（HomeView / NetworkErrorView / UserCenterView / ChangelogView / LotteryView / LotteryCardDetailView / CasdoorCallbackView）
- [x] Phase 3: message 系统核心 views + components（不含 Admin 大文件）
- [x] Phase 4: message 系统 Admin 大文件（NotifyAdminView / CommentAdminView / DmAdminView / MessageAdminPermission / messageAdmin.ts）
- [ ] Phase 5: rpa-browser（views + components，约 14+ 文件，最大批）
  - [x] 建立 rpa.* 命名空间（generated.ts 的 rpaNs 常量，5 语言，含通用/直播/action类型 key）
  - [x] LiveBox.vue（直播监控：biliMessage / 确认框 / 按钮 / 状态文本）
  - [x] ActionCard.vue（action 类型标题/描述/标签 映射改为 i18n key）
  - [x] MinimizeBar.vue（无硬编码中文，prop 传入）
  - [ ] 剩余：AdminManagement / ActionManagement / BrowserStream / CommunityPage / FingerprintCreateEdit / WorkflowManagement / ActionLogView（views）；ActionParamsForm / BranchContainer / ConditionEditor / LoopEditor / DebugBox / OperationFeedbackPanel / ToolboxPanel / WorkflowEditDialog / EditCustomActionDialog（components）
- [ ] Phase 6: components/lottery_data（约 30 文件）
- [ ] Phase 7: moment（MomentCard 等 6 文件）
- [ ] Phase 8: admin（AdminLayout / AdminOverview / MomentAuditListView）
- [ ] Phase 9: components/CommonCompo、home、communicate_list 等其余组件
- [ ] Phase 10: stores / utils 中的中文文案（如 utils/message.ts 的 ElMessage 提示）
- [ ] Phase 11: 全量 `vite build` / `vue-tsc` 验证

## 进度统计
- 已使用 `useI18n` 的文件：约 26 个
- src 下 vue 文件总数：187 个
- 说明：tsconfig `baseUrl` deprecation 告警（TypeScript 7.0）非本次改动引起，可忽略

---

# 后端 i18n（FastAPI，fastapi-i18n）

## 目标
后端对外返回的业务 `msg`（统一异常 msg、ResponseMsg 枚举、鉴权依赖抛出的 detail）支持多语言，
随请求 `Accept-Language` 头切换，前端同步注入当前 locale。

## 范围（已与用户确认）
- **服务范围**：仅 `bili-common` 共享层（各业务服务直接复用，无需各自改造）。
- **文案范围**：统一异常 msg + 业务提示文案（对外 msg），含 `ResponseMsg` 枚举、`exceptions.py`、
  `deps/auth.py` 鉴权依赖 detail。
- **locale 位置**：统一放在 `bili-common/bili_common/locale/`，`FASTAPI_I18N__LOCALE_DIR` 指向它。
- 语言：zh-CN（默认）/ en / zh-TW / ja / ko（与前端一致）。
- 不纳入：模型文件（lottery_query 等）内的 UI 元数据 label/description（属前端筛选 UI 来源，非接口 msg）。

## 关键技术约束（fastapi-i18n 行为）
- `from fastapi_i18n import i18n, _`；`_` 是 gettext 别名，依赖请求级 `ContextVar`。
- 枚举 / 异常类属性在**类定义时即求值**，此时无请求上下文 → 不能直接在类体内写 `_("...")`。
- **必须延迟翻译**：枚举存「原文中文 key」，对外取值时再 `_()` 翻译；异常 `msg` 同样延迟。
- 动态字符串（含 `{xxx}` 占位）：先 `_("模板原文")` 再 `.format(...)` / `%`，绝不放占位符进翻译。

## 改造文件
- [ ] `bili-common/pyproject.toml`：`uv add fastapi-i18n`
- [ ] `bili-common/bili_common/i18n.py`：新建，封装 `i18n`、`_`、提供 `translate_msg(key, **kw)` 延迟翻译辅助，
      并 `load_dotenv`/读取 `FASTAPI_I18N__LOCALE_DIR` 指向本包 locale 目录（默认 `bili_common/locale`）。
- [ ] `bili-common/bili_common/models/response_msg.py`：枚举值改为原文中文（已是中文），
      新增 `t(self, **kw)` 方法返回 `_()` 后的翻译；保持 `StrEnum` 兼容（取值时调用方用 `.t()`）。
- [ ] `bili-common/bili_common/exceptions.py`：
      - `BaseException.msg` 默认 `"ok"` 改为延迟翻译（`to_response` 时 `_()`）；
      - `NotLoggedInException.msg`、文本型异常 msg 改为 `_()` 翻译（在 `to_response` 内翻译）；
      - `BiliException` 的 `detail` 在处理器内翻译；
      - `InvalidUIDException` / `InvalidMidFormatException` / `ResourceConflictException` 的 f-string 改为
        先 `_("模板")` 再 `.format()`；
      - 全局兜底 `_unhandled_exception_handler` 的 `f"服务器内部错误 (错误ID: {error_id})"` 改为
        `_("服务器内部错误 (错误ID: {error_id})").format(error_id=error_id)`。
- [ ] `bili-common/bili_common/deps/auth.py`：
      - `require_root` / `require_admin` / `require_permission` 抛出的中文 `detail` 改为 `_()`（在抛出处翻译，
        因在请求上下文中执行，可直接 `_()`）。
- [ ] `bili-common/bili_common/locale/`：建 `babel.cfg` + 5 语言 `messages.po` + 编译 `messages.mo`。
- [ ] `bili-common/bili_common/models/response.py`：`success()` / `error()` / `custom()` 等辅助函数
      若直接 hardcode 中文 msg 则改为 `_()`（当前为文档中文，无 hardcode msg，确认后跳过）。

## Babel 流程
```bash
cd bili-common
# 抽取
pybabel extract -F babel.cfg -o locale/messages.pot bili_common
# 初始化各语言
pybabel init -i locale/messages.pot -d bili_common/locale -l en
pybabel init -i locale/messages.pot -d bili_common/locale -l zh_TW
pybabel init -i locale/messages.pot -d bili_common/locale -l ja
pybabel init -i locale/messages.pot -d bili_common/locale -l ko
# zh_CN 用默认（en 为默认则 zh_CN 与原文一致，无需翻译或设为空）
# 翻译后编译
pybabel compile -d bili_common/locale
```
注：gettext locale 命名用下划线 `zh_TW`（非连字符），`FASTAPI_I18N__LOCALE_DEFAULT` 设为 `zh_CN`。

## 环境变量（各业务服务 docker / .env 配置）
- `FASTAPI_I18N__LOCALE_DIR=/path/to/bili_common/locale`（或由包内默认值兜底）
- `FASTAPI_I18N__LOCALE_DEFAULT=zh_CN`

## 前端配套（后续，本计划书前端部分）
- axios 拦截器注入 `Accept-Language: <当前 locale>`（locale 映射：zh-CN→zh_CN, zh-TW→zh_TW 等）。

## 分阶段
- [x] Phase 12.1: bili-common 引入 fastapi-i18n，建 i18n.py 封装 + locale 目录 + babel.cfg
- [x] Phase 12.2: response_msg.py 延迟翻译改造（枚举值原文 + `.t()` 延迟翻译 + 抽取标记块）
- [x] Phase 12.3: exceptions.py 延迟翻译改造（`to_response`/`detail`/`f-string` 占位符）
- [x] Phase 12.4: deps/auth.py 鉴权 detail 翻译（4 处中文 HTTPException）
- [x] Phase 12.5: Babel 抽取 + 5 语言 .po 翻译 + 编译 .mo
- [x] Phase 12.6: 验证通过（uv run 模拟 Accept-Language 切换，5 语言全部正确翻译）

## 业务服务接入步骤（各 FastAPI 服务需自行完成，不在本范围）
bili-common 已提供 `i18n` 依赖与 locale，各业务服务只需：
1. 注册依赖：`FastAPI(dependencies=[Depends(i18n)])`（`i18n` 从 `bili_common.i18n` 导入）；
   若已自定义异常处理器，确保 `register_exception_handlers` / `register_business_exception_handlers` 已调用。
2. 环境变量（docker / .env）：
   - `FASTAPI_I18N__LOCALE_DIR`：指向 bili-common 的 locale 绝对路径
     （如 `/app/bili_common/bili_common/locale`，由 editable 安装位置决定）；
   - `FASTAPI_I18N__LOCALE_DEFAULT=zh_CN`。
3. 业务接口内手工返回的 msg：若直接 hardcode 中文，建议改为 `from bili_common.i18n import _` 后 `_("...")`，
   并在请求上下文中调用（视图/依赖执行期）；动态串先 `_("模板 {x}")` 再 `.format(x=...)`。
   （bili-common 已翻译的 `ResponseMsg` / 异常 msg 会自动随语言切换。）

## 重新生成翻译流程（后续维护）
```bash
cd bili-common
uv run pybabel extract -F babel.cfg -o bili_common/locale/messages.pot \
  bili_common/exceptions.py bili_common/deps/auth.py bili_common/models/response_msg.py
uv run pybabel update -i bili_common/locale/messages.pot -d bili_common/locale
# 手动更新各语言 .po 的 msgstr 后编译
uv run pybabel compile -d bili_common/locale
```
注：`fill_po.py`（开发期工具）可一次性为 en/zh_TW/ja/ko 填充翻译，按需复用。

---

# 前端 Accept-Language 注入（后端 i18n 配套）

## 目标
前端所有 HTTP 请求携带当前语言，使后端 `fastapi-i18n` 按 `Accept-Language` 返回对应语言文案。

## 实现
- [x] `src/stores/locale.ts`：新增 `acceptLanguage` computed，返回当前 locale 值
      （`zh-CN`/`en`/`zh-TW`/`ja`/`ko`；后端 `fastapi-i18n` 会把 `-` 规范为 `_` 匹配 locale 目录，故直接发原值即可）。
- [x] `src/api/base_axios/base_axios.ts`：请求拦截器 `AXIOS_REQ_AUTH_INJECTION` 注入
      `config.headers['Accept-Language'] = useLocaleStore().acceptLanguage`。
- [x] `src/api/notify/runtime_config.ts`、`src/api/browser/runtime_config.ts`、
      `src/api/bili_lottery_data/runtime_config.ts`：hey-api `onRequest` 注入
      `options.headers.set('Accept-Language', LocaleStore.acceptLanguage)`。
- 说明：后端 `parse_accept_language` 会将 `zh-CN` → `zh_CN`，与 locale 目录命名一致；
      默认语言 `FASTAPI_I18N__LOCALE_DEFAULT=zh_CN`。

## 已知遗留问题（前序 i18n 改造引入，非本次改动）
- `src/i18n/modules/generated.ts` 存在 8 处 TS 错误（对象文本多个同名属性，行 274/275/276/639/899/1159/1419/1679），
  为前序插入 messageNs/rpaNs 时 key 重复或 locale 块重复声明所致，会阻断 `vue-tsc` / `vite build`。
  属独立修复任务，需在「前端 i18n 全量改造」收尾时统一处理（见上方 Phase 5-11）。
