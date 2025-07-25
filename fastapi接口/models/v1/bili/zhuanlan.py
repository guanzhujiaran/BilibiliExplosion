from pydantic import Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class lotteryArticleReq(CustomBaseModel):
    abstract_msg: str = Field(
        "由于代理不够+只获取了图片动态，内容不全。\n写了个网站 http://serena.dynv6.net/ （仅限ipv6访问,里面还有点samsclub的东西）正在完善中\nipv6开启方法:https://ipw.cn\n",
        description="插入专栏开头的摘要内容")
    save_to_local_file: bool = Field(False, description="是否保存到本地文件")


class ArticleInfo(CustomBaseModel):
    title: str
    content: str


class LotteryArticleResp(CustomBaseModel):
    reserve: ArticleInfo
    official: ArticleInfo
    charge: ArticleInfo
    topic: ArticleInfo
