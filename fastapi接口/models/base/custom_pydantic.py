from typing import Optional, Any, Union, Dict, List

from pydantic import BaseModel, Field, ConfigDict, computed_field


class CustomBaseModel(BaseModel):
    # extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, exclude=True)
    model_config = ConfigDict(
        extra='allow',
    )

    @computed_field
    def extra_fields(self) -> Optional[Dict[str, Any]]:
        return self.model_extra

    def dict(self, **kwargs):
        original_data = super().model_dump(**kwargs)
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


if __name__ == '__main__':
    class _Test(CustomBaseModel):
        abcdefg: bool = Field(True, description='a', alias='badjawdl')
        awdasdwasb: bool = Field(False)


    _test = _Test(
        c=12324
    )
    print(_test.dict(by_alias=True))
