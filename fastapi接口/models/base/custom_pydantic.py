from typing import Optional, Any, Union, Dict, List
from pydantic import BaseModel, Field, ConfigDict

class CustomBaseModel(BaseModel):
    extra_fields: Optional[dict] = Field(default_factory=dict, exclude=True)
    model_config = ConfigDict(
        extra='ignore',
    )

    def __init__(self, **data):
        # 初始化模型，将多余字段存入 extra_fields 中
        super().__init__(**data)
        # 过滤出传入的多余字段
        if extra := {k: v for k, v in data.items() if k not in self.model_fields}:
            object.__setattr__(self, 'extra_fields', extra)
        else:
            object.__setattr__(self, 'extra_fields', None)

    def dict(self, **kwargs):
        original_data  = super().dict(**kwargs)
        converted_data = self._convert_large_ints_to_str(original_data)
        return converted_data

    def _convert_large_ints_to_str(self, data: Any) -> Union[Dict[str, Any], List[Any], str, int, float]:
        max_safe_integer = 9007199254740991  # JavaScript 最大安全整数

        if isinstance(data, dict):
            return {k: self._convert_large_ints_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_large_ints_to_str(item) for item in data]
        elif isinstance(data, int) and data > max_safe_integer:
            return str(data)
        else:
            return data