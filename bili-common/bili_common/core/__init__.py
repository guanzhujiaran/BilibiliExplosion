"""core: 公共基础模型基类（sqlmodel，自包含，不依赖具体业务项目）"""

from bili_common.core.browser import BaseBrowserId, BaseBrowserIdOptional, BaseUserMid

__all__ = ["BaseBrowserId", "BaseBrowserIdOptional", "BaseUserMid"]
