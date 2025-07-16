from pydantic import Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class lotteryArticleReq(CustomBaseModel):
    abstract_msg: str = Field(
        "由于代理不够+只获取了图片动态，内容不全。\n写了个网站 http://serena.dynv6.net/ （仅限ipv6访问）正在完善中\n",
        description="插入专栏开头的摘要内容")
    save_to_local_file: bool = Field(False, description="是否保存到本地文件")


class lotteryArticleResp(CustomBaseModel):
    reserve: str
    official: str
    charge: str
    topic: str
