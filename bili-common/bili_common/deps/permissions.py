"""管理端权限（v2，Linux 风格 per-biz_type 位掩码，计划书 §权限 v2）。

设计（对齐 Linux 文件权限的心智模型）：

- **资源维度** = `InteractionBizTypeEnum`（动态 / 话题 / 评论 / 私信 / 头像 / 封面 /
  举报 / 用户 …），类比 Linux 下「不同的文件」；
- **操作位** = `BizPermOp`（`IntFlag`），数值语义对齐 rwx：
  `BAN=1(x 处置：封禁/解封)`、`AUDIT=2(w 审核：通过/驳回/下架/恢复)`、`VIEW=4(r 查看)`;
- **权限字** = 每个资源域一个 `0~7` 的 int（`7`=rwx 全权、`6`=查看+审核、`4`=只读、
  `0`=无权限），即 chmod 的八进制权限字；
- **存储 / 传输**：`dict[biz文本, 权限字]`（如 `{"dm": 7, "comment": 4}`），
  管理员表 `msg_admin.biz_perms`（JSON 列）与网关头 `x-bili-permissions` 同构；
  root 恒为 `{"*": 7}`（`*` 键表示全部资源域全权）；
- **检查**：`has_biz_perm(biz, op)` = root 恒真，否则 `biz_perms.get(biz_text, 0) & op`；
- **内容明文**：root 专属（原 `*_VIEW_CONTENT`），不占权限位——依赖层直接按
  `is_root` 判定，普通管理员的权限字最高 7 也拿不到明文。

"""

from typing import Any
from enum import IntFlag

__doc__ = __doc__  # noqa: A003


class BizPermOp(IntFlag):
    """资源操作位（数值对齐 Linux rwx：x=1 / w=2 / r=4）。"""

    BAN = 1  # 处置（x）：封禁 / 解封用户
    AUDIT = 2  # 审核（w）：通过 / 驳回 / 下架 / 恢复
    VIEW = 4  # 查看（r）：审核队列 / 详情


#: 全部基础操作位（0b111 = 7）
ALL_OPS = int(BizPermOp.VIEW | BizPermOp.AUDIT | BizPermOp.BAN)

#: root 的权限字（`*` 键 = 全部资源域全权）
ROOT_BIZ_PERM = 7

#: 审核统计 / 管理队列涉及的默认资源域文本（授权 UI 的行序即此序）
AUDIT_BIZ_KEYS: list[str] = [
    "dynamic",
    "topic",
    "comment",
    "dm",
    "avatar",
    "folder_cover",
    "report",
    "user",
    "rpa_action",
    "rpa_workflow",
    "rpa_plugin",
    "rpa_browser",
]


def parse_biz_key(key: str):
    """资源域键 → 枚举成员（文本形式，大小写不敏感）；非法返回 None。

    延迟导入 InteractionBizTypeEnum（避免 models ↔ deps 循环导入）。
    """
    from bili_common.models.interaction import InteractionBizTypeEnum

    return _BIZ_BY_TEXT().get(str(key).strip().lower())


def _BIZ_BY_TEXT() -> dict:
    from bili_common.models.interaction import InteractionBizTypeEnum

    return {b.to_text(): b for b in InteractionBizTypeEnum}


def normalize_biz_perms(raw: Any) -> dict[str, int]:
    """把任意入参清洗为合法的 `dict[biz文本, 权限字]`。

    - 非 dict / 空值 → `{}`；
    - 键：必须是合法资源域文本（`parse_biz_key` 可解析），非法键丢弃；
    - 值：0~7（超出按位截断到 3 位）；
    - `*` 键保留（root 专用标记，普通管理员授权 API 不得写入）。
    """
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not k:
            continue
        if k == "*":
            out[k] = int(v) & ALL_OPS
            continue
        biz = parse_biz_key(k)
        if biz is None:
            continue
        try:
            out[k] = int(v) & ALL_OPS
        except (TypeError, ValueError):
            continue
    return out


def has_biz_perm(
    biz_perms: dict[str, int] | None,
    biz: "InteractionBizTypeEnum",
    op: "BizPermOp | int",
) -> bool:
    """按位检查：指定资源域是否持有某操作位。"""
    if not biz_perms:
        return False
    return (int(biz_perms.get(biz.to_text(), 0)) & int(op)) != 0


def ops_text(mask: int) -> str:
    """权限字 → 可读字母串（如 `7` → `rwx`、`4` → `r--`、`0` → `---`）。"""
    m = int(mask) & ALL_OPS
    return (
        ("r" if m & int(BizPermOp.VIEW) else "-")
        + ("w" if m & int(BizPermOp.AUDIT) else "-")
        + ("x" if m & int(BizPermOp.BAN) else "-")
    )


__all__ = [
    "BizPermOp",
    "ALL_OPS",
    "ROOT_BIZ_PERM",
    "AUDIT_BIZ_KEYS",
    "parse_biz_key",
    "normalize_biz_perms",
    "has_biz_perm",
    "ops_text",
]
