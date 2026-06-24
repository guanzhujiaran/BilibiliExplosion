from abc import abstractmethod, ABC
from typing import Optional, Any, Union, Dict, List
from pydantic import BaseModel, Field, ConfigDict, computed_field


class CustomGenericModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    @computed_field
    @property
    def extra_fields(self) -> Optional[Dict[str, Any]]:
        return self.model_extra or None

    def dict(self, **kwargs):
        original_data = super().model_dump(**kwargs)
        converted_data = self._convert_large_ints_to_str(original_data)
        return converted_data

    def _convert_large_ints_to_str(
        self, data: Any
    ) -> Union[Dict[str, Any], List[Any], str, int, float]:
        max_safe_integer = 9007199254740991  # JavaScript 最大安全整数

        if isinstance(data, dict):
            return {k: self._convert_large_ints_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_large_ints_to_str(item) for item in data]
        elif isinstance(data, int) and data > max_safe_integer:
            return str(data)
        else:
            return data


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    @computed_field
    @property
    def extra_fields(self) -> Optional[Dict[str, Any]]:
        return self.model_extra or None

    def dict(self, **kwargs):
        original_data = super().model_dump(**kwargs)
        converted_data = self._convert_large_ints_to_str(original_data)
        return converted_data

    def _convert_large_ints_to_str(
        self, data: Any
    ) -> Union[Dict[str, Any], List[Any], str, int, float]:
        max_safe_integer = 9007199254740991  # JavaScript 最大安全整数

        if isinstance(data, dict):
            return {k: self._convert_large_ints_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_large_ints_to_str(item) for item in data]
        elif isinstance(data, int) and data > max_safe_integer:
            return str(data)
        else:
            return data


class CustomBaseModelHashable(ABC, CustomBaseModel):
    """可哈希的自定义基础模型
    Args:
        ABC (_type_): _description_
        CustomBaseModel (_type_): _description_
    """

    @abstractmethod
    def __hash__(self) -> int:
        """
        hash方法必须返回int类型
        """
        ...
