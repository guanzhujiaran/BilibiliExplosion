# 字段名统一为 snake_case（待执行方案）

## 背景

`@auto_str` 的默认后缀已统一为 `_str`，但**驼峰字段名加后缀后是混合形式**
（`bizId` → `bizId_str`、`folderId` → `folderId_str`），不是纯 snake_case。
若要 `bizId` → `biz_id_str`，必须先把字段本身重命名。

## 为什么必须单独立项

重命名会同时命中两类属性访问，**语法上无法区分**：

| 类别 | 例子 | 是否要改 |
| --- | --- | --- |
| schema 实例属性 | `req.bizId` / `params.folderId` | **要改** |
| DB 表模型属性 | `row.bizId` / `dyn.dynId` | **绝不能改**（`app/models/db/**` 是真实表列名） |

此外还有两类易被误伤的目标：

- **原生 SQL 字符串**：`text(f"DELETE FROM TMoment WHERE dynId= {oid}")`
- **局部变量 / 常量**：`auditStatus = req.audit_status`

2026-10-04 的实施中，正则脚本同时误伤了以上三类，导致工作区进入不一致状态
（mypy 新增 596 个错误），最终已 `git checkout app tests` 回滚重做。
**教训：这类重命名不能用正则，必须用 AST + 静态检查驱动。**

## 已备好的工具与基线

| 资产 | 位置 / 数值 |
| --- | --- |
| 驼峰 → snake 映射规则 | `re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()`，93 条、无冲突 |
| mypy 安全网 | 已装 `mypy 2.4.0`；**基线 392 个既有错误** |
| AST 脚本（阶段 1） | `visit_Call`(keywords) / `visit_FunctionDef`(args) —— **不碰属性访问与字符串** |
| mypy 驱动修复（阶段 2） | 解析 `has no attribute "xxx"` 报错，只改点号属性 |

## 执行步骤（建议顺序）

1. **新分支**，从干净状态开始（不要在叠了 auto_str 改造的工作区做）
2. 生成映射表：扫 `app/models/schemas/**` 的字段声明 → snake
3. 阶段 1（AST）：`app/` + `tests/` 的**字段声明 + 关键字参数 + 函数定义参数**
   —— 明确**不改** `ast.Attribute`（属性访问）与字符串常量
4. 跑 `mypy app tests`，与基线 diff，**只处理新增的 `has no attribute`**
5. 阶段 2：按 mypy 报错的 `文件:行` 精确修属性访问
   —— `has no attribute` 必然是 schema 属性（DB 属性存在不会被报），所以这一步**天然安全**
6. 跑全量 `pytest`，与基线 diff（基线 12 failed）
7. **人工审阅 `git diff`**：重点确认没有 `.xxx` 形式的 DB 访问被改
8. 同步 `tests/` 里的原生 SQL 字符串（这一步只能人工，工具无法区分）
9. 前端：SDK 重新生成 + 消费点改名（`xxxStr` → `xxx_str`）

## 风险清单

- DB 模型 `app/models/db/**` 必须零改动（用 `git diff --stat` 确认该目录无变更）
- `bili_common/models/report.py` 等公共库里的 `record_report(biz_id=...)` 签名已是 snake
- 驼峰字段名改成 snake 后，`auto_str` 派生字段才变成纯 `biz_id_str`
- 部分模型字段名与 DB 列同名（如 `auditStatus`），装配处 `xxx=Row.auditStatus` 左边改右边不改
- 回归验证存在干扰：部分测试单独跑通过、全量跑失败（测试间 DB 状态污染），
  且 `test_report_idempotent` 对残留数据敏感（`reportMid=906102, bizId=27` 命中即失败），
  排查失败前先确认不是脏数据
