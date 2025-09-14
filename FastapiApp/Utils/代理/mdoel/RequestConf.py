from pydantic import Field

from Models.base.custom_pydantic import CustomBaseModel


class RequestConf(CustomBaseModel):
    is_use_cookie: bool = Field(False)
    is_use_available_proxy: bool = Field(False)
    is_use_custom_proxy: bool = Field(False)
    is_return_raw_response: bool = Field(False)
    
