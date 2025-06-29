from pydantic import Field, ConfigDict

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class SamsClubHeadersModel(CustomBaseModel):
    model_config = ConfigDict(extra='ignore', serialize_by_alias=True, )
    language: str = "CN"
    system_language: str = Field("CN", alias="system-language")
    device_type: str = Field("android", alias="device-type")
    tpg: str = Field("1")
    app_version: str = Field("5.0.120", alias="app-version")
    device_id: str = Field("d3e9907ab1881aac891aff90100016e1950c", alias="device-id")
    device_os_version: str = Field("11", alias="device-os-version")
    device_name: str = Field("OnePlus_ONEPLUS+A6000", alias="device-name")
    treq_id: str = Field(..., alias="treq-id")
    auth_token: str = Field(...,
                            alias="auth-token")
    longitude: str | float = Field(...)
    latitude: str | float = Field(...)
    p: str = Field("1656120205")
    t: str = Field(...)
    n: str = Field(...)
    sy: str = Field("0")
    st: str = Field(...)
    sny: str = "c"
    rcs: str = "1"
    spv: str = "2.0"
    Local_Longitude: str | float = Field(..., alias="Local-Longitude")
    Local_Latitude: str | float = Field(..., alias="Local-Latitude")
    zoneType: str = "1"
    content_type: str = Field("application/json;charset=utf-8", alias="Content-Type")
    Host: str = "api-sams.walmartmobile.cn"
    Connection: str = 'Keep-Alive'
    accept_encoding: str = Field("gzip", alias='Accept-Encoding')
    user_agent: str = Field("okhttp/4.12.0", alias="User-Agent")


class SamsClubEncryptModel(CustomBaseModel):
    device_id_str: str
    version_str: str
    device_name: str
    do_encrypt_result_str: str


class SamsClubGetDoEncryptReqModel(CustomBaseModel):
    timestampStr: str
    bodyStr: str
    uuidStr: str
    tokenStr: str


class SamsClubQuerySpuInfoParamsModel(CustomBaseModel):
    spu_new_tag_tag_mark: str | None
    spu_info_title: str | None
    spu_info_update_asc: bool | None
    spu_price_asc: bool | None
    spu_price_min: bool | None
    spu_price_max: bool | None
