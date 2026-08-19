"""社区互动通用枚举（收藏 / 点赞等跨服务互动，供各业务系统统一读取）。"""

from enum import IntEnum


class InteractionBizTypeEnum(IntEnum):
    """互动资源类型（be-message 统一管理收藏/点赞，按该类型区分资源归属）。

    **存储**：数据库以 int 存储（值 1~6），减小存储空间、利于索引；
    **对外契约**：API 层经 `from_text` / `to_text` 转换为可读文字
    （`dynamic` / `lottery` / ...），前端 / 跨服务 RPC 契约保持文字不变。
    """

    DYNAMIC = 1  # 动态（bizId = dynId）
    LOTTERY = 2  # 抽奖卡片（bizId = 抽奖卡片 id）
    RPA_ACTION = 3  # RPA 自定义操作（bizId = action_id）
    RPA_WORKFLOW = 4  # RPA 工作流（bizId = workflow_id）
    RPA_BROWSER = 5  # RPA 浏览器实例（bizId = browser_id）
    RPA_PLUGIN = 6  # RPA 插件（bizId = plugin_id）

    @classmethod
    def from_text(cls, text: "InteractionBizTypeEnum | str | int | None") -> "InteractionBizTypeEnum":
        """把对外文字（dynamic/lottery/...）或数值转换为枚举成员（统一入口）。

        - 已是枚举成员：原样返回；
        - 数字 / 数字字符串：按值构造（兼容内部存储读取）；
        - 文字（大小写不敏感，如 dynamic / DYNAMIC）：按成员名解析。
        """
        if isinstance(text, cls):
            return text
        if text is None:
            raise ValueError("不支持的资源类型: None")
        if isinstance(text, int) or (isinstance(text, str) and text.strip().isdigit()):
            return cls(int(text))
        return cls[text.strip().upper()]

    def to_text(self) -> str:
        """转对外可读文字（dynamic / lottery / ...）。"""
        return self.name.lower()


__all__ = ["InteractionBizTypeEnum"]
