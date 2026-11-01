# 用户中心 UID 展示口径（uid / mid 合并为 uid_str）

## 背景

本系统里 `uid` 与 `mid` 是**同一个 BIGINT 主键**（`TUserInfo.uid` ≡ `TUserDetail.mid`），
用户中心此前把两者分别展示（`UID` 取 nav 的 `uid`，`MID` 取 user_info 的 `mid`），
既重复又让 JS 侧存在精度丢失风险（19 位雪花 ID 超过 `Number.MAX_SAFE_INTEGER`）。

后端已按统一计划书的「雪花 ID 字符串出参」口径改造：
数值字段用 `int` 声明，字符串版由 `@auto_str` 自动派生，后缀 `_str`。

## 后端契约变更（已完成）

`bili-common/bili_common/models/pptr_user_gateway.py`：

| 模型 | 变更 |
| --- | --- |
| `PptrUserNavData` | `uid: int` + 自动派生 `uid_str: str \| null` |
| `PptrUserInfoUpdateResult` | `uid: int` + 自动派生 `uid_str: str \| null` |
| `PptrUserRoleSetResult` | `target_uid: int` + 自动派生 `target_uid_str: str \| null` |
| `PptrUserRoleSetParams` | 入参保持 `target_uid: str`，后端自行 `int()` 转换（不改） |

验证（`uv run python`）：
- `model_dump()` 含 `uid_str` / `target_uid_str`；
- FastAPI OpenAPI 的 `PptrUserNavData` 组件 schema 含 `uid_str`（serialization 模式）。

## 前端需求

### 1. SDK 重新生成（已完成）

`openapi.json` 变更后已重新生成 `src/api/**/hey-api/`，`PptrUserNavData` / `PptrUserInfoUpdateResult`
含 `readonly uid_str: string | null`，`PptrUserRoleSetResult` 含 `readonly target_uid_str: string | null`。

### 2. 字符串版收敛在 API 封装层（核心改动，已完成）

收敛点放在 `src/api/user/utils.ts` 新增的 `mapNavResponse(nav: PptrUserNavData): UserNavModel`：
`uid` 固定取 `nav.uid_str`，数值版 `nav.uid` **不进入 store**。

这样全站 60+ 处 `user_nav.uid`（`x-bili-mid` 请求头、与后端 `mid` 的字符串比较、空间页路由 mid、
评论归属判断等）**无需改动**，`UserNavModel.uid` 仍是 `string`；localStorage 里的旧数据天然兼容。

调用方：`isLogin()` 与 `UserCenterDefaultPanel.vue` 的 nav 兜底补拉。

### 3. 用户中心展示

`UserCenterDefaultPanel.vue`（`components/opus-detail/RightPannel/PannelItems/SettingComponent/`）：

- 「本系统账户」卡片中**只保留 `UID` 一行**，取值 `fmt(navInfo?.uid)`（store 已是 `uid_str` 字符串）；
- 删除 `MID` 行（不再需要 `profile?.mid ?? navInfo?.uid` 兜底）；
- 顶部身份区 `@用户名 · UID xxx` 保持不变。

### 4. 管理员授予角色

`UserBaseInfoConfig.vue`：目标用户输入框是**入参**，继续传字符串（`target_uid: str`），
后端转 int；`String(targetUid) === String(currentUser.value?.uid)` 的防自授权比较保持。

## 遗留（本次不处理）

- `GET /api/v1/user/user_info` 返回体中的 `mid`（裸 dict，非模型）：当前已是 `str(info.uid)`，
  字符串安全，但字段名与 `uid` 重复，后续可统一删除或改为 `uid_str`。
- 黑名单相关 `mid` / `target_mid`（`FollowListResp` 等）仍为 int，属独立口径，需单独排期。
