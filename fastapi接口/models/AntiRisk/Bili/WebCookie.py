from typing import List, Any

from pydantic import Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from utl.加密.utils import GenWebCookieParams


class BiliWebCookie(CustomBaseModel):
    gen_web_cookie_params: GenWebCookieParams = Field(...)
    buvid3: str | None = Field(None)  # 第一次通过访问网页获取 _render_data_的access_id 做一个jwt解密,获取buvid键名,之后就一直不动了
    b_nut: str | None = Field(None)
    b_lsid: str | None = Field(None)
    uuid: str | None = Field(None, alias='_uuid')
    hit_dyn_v2: str | None = Field(None, alias='hit-dyn-v2')
    enable_web_push: str = Field('DISABLE')
    home_feed_column: str = Field('4')
    browser_resolution: str = Field('')

    buvid4: str | None = Field(None)  # 通过访问spi获取buvid4,响应里的buvid3不用管
    bili_ticket: str | None = Field(None)
    bili_ticket_expires: str | None = Field(None)

    buvid_fp: str | None = Field(None)

    def model_post_init(self, context: Any):
        self.buvid_fp = self.gen_web_cookie_params.buvid_fp
        self.uuid = self.gen_web_cookie_params.uuid

    def to_str(self, include_keys: List["BiliWebCookie.model_fields"] | None = None) -> str:
        """
        确保按照顺序合成cookie字符串
        """
        order = list(BiliWebCookie.model_fields.keys())

        if include_keys is None:
            include_keys = order
        order[:] = [x for x in order if x != 'gen_web_cookie_params']
        ret = ''
        for key in order:
            if key in include_keys and getattr(self, key):
                ret += f'{key}={getattr(self, key)}; '

        return ret.strip('; ')
