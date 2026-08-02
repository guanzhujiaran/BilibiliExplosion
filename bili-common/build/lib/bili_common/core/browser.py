"""
浏览器 / 用户基础参数模型（sqlmodel 版，自包含）

从各业务项目复刻而来的精简基类，避免公共包反向依赖具体项目。
"""

from sqlmodel import SQLModel
from pydantic import field_validator, computed_field


class BaseBrowserId(SQLModel):
    """浏览器指纹基础参数模型"""

    browser_id: int | str

    @field_validator("browser_id", mode="before")
    @classmethod
    def validate_id(cls, v):
        return int(v) if v is not None and isinstance(v, str) else v

    @computed_field
    @property
    def browser_id_str(self) -> str:
        return str(self.browser_id)


class BaseBrowserIdOptional(SQLModel):
    """浏览器指纹基础参数模型（browser_id 可空）"""

    browser_id: int | str | None = None

    @field_validator("browser_id", mode="before")
    @classmethod
    def validate_id(cls, v):
        return int(v) if v is not None and isinstance(v, str) else v

    @computed_field
    @property
    def browser_id_str(self) -> str:
        return str(self.browser_id or "")


class BaseUserMid(SQLModel):
    """用户ID基础参数模型"""

    mid: int | str

    @field_validator("mid", mode="before")
    @classmethod
    def validate_mid(cls, v):
        return int(v) if v is not None and isinstance(v, str) else v

    @computed_field
    @property
    def mid_str(self) -> str:
        return str(self.mid)
