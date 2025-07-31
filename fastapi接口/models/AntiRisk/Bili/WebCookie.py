from typing import List, Any
from dataclasses import dataclass
from pydantic import Field, ConfigDict

from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from utl.加密.utils import GenWebCookieParams


class BiliWebCookie(CustomBaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True
    )

    gen_web_cookie_params: GenWebCookieParams = Field(...)
    buvid3: str | None = Field(None)  # 第一次通过访问网页获取 _render_data_的access_id 做一个jwt解密,获取buvid键名,之后就一直不动了
    b_nut: str | None = Field(None)
    uuid: str | None = Field(None, alias='_uuid')
    at_once: str | None = Field(None, alias='__at_once')
    hit_dyn_v2: str | None = Field(None, alias='hit-dyn-v2')
    enable_web_push: str = Field('DISABLE')
    home_feed_column: str = Field('4')
    browser_resolution: str = Field('')

    buvid4: str | None = Field(None)  # 通过访问spi获取buvid4,响应里的buvid3不用管
    bili_ticket: str | None = Field(None)
    bili_ticket_expires: int | None = Field(None)

    b_lsid: str | None = Field(None)
    buvid_fp: str | None = Field(None)

    def model_post_init(self, context: Any):
        self.buvid_fp = self.gen_web_cookie_params.buvid_fp
        self.uuid = self.gen_web_cookie_params.uuid
        self.browser_resolution = f'{self.gen_web_cookie_params.avail_w}-{self.gen_web_cookie_params.avail_h}'
        self._is_used = False

    def to_str(self, include_keys: List["BiliWebCookie.model_fields"] | None = None) -> str:
        """
        确保按照顺序合成cookie字符串
        """
        cookie_dict = self.model_dump(by_alias=True,exclude_none=True)
        order = list(cookie_dict.keys())
        if include_keys is None:
            include_keys = order
        exclude_keys = ['gen_web_cookie_params','extra_fields']
        if self._is_used:
            exclude_keys.append('__at_once')
        order[:] = [x for x in order if x not in exclude_keys]
        ret = ''
        for key in order:
            if key in include_keys and cookie_dict.get(key):
                ret += f'{key}={cookie_dict.get(key)}; '
        self._is_used = True
        return ret.strip('; ')

@dataclass
class CookieWrapper:
    ck: BiliWebCookie
    ua: str
    expire_ts: int
    times_352: bool = 0

    @property
    def able(self) -> bool:
        if self.times_352 > 10:
            return False
        return True


if __name__ == '__main__':
    ck = BiliWebCookie(
        gen_web_cookie_params=GenWebCookieParams(
            buvid_fp='buvid_fp',
            uuid='uuid',
            avail_w=1920,
            avail_h=1080,
            window_h=1080,
            window_w=1920,
            ua='test-ua'
        ),
        buvid3='buvid3',
        b_nut='1',
        at_once='at_once',
    )
    print(ck.to_str())
    print(ck.to_str())

