from pydantic import BaseModel, Field, Extra


class CustomBaseModel(BaseModel):
    extra_fields: dict = Field(default_factory=dict, exclude=True)

    class Config:
        # 设置为忽略多余字段
        extra = 'ignore'

    def __init__(self, **data):
        # 初始化模型，将多余字段存入 extra_fields 中
        super().__init__(**data)
        # 过滤出传入的多余字段
        if extra := {k: v for k, v in data.items() if k not in self.model_fields}:
            object.__setattr__(self, 'extra_fields', extra)
        else:
            object.__setattr__(self, 'extra_fields', None)