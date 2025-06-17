import unittest
from langchain_openai import ChatOpenAI
from fastapi接口.models.v1.ChatGpt3_5.ReplySingleModel import OpenAiClientModel
from fastapi接口.service.compo.chains import myChains
from fastapi接口.service.LLM.handleLLMReplySingle import ChatGpt3_5
import loguru

class MyTestCase(unittest.IsolatedAsyncioTestCase):
    __ = ChatGpt3_5()

    # async def test_SingleReply(self):
    #     resp = await self.__.SingleReply('114514')
    #     print(resp)
    #     self.assertTrue(type(resp), str)  # add assertion here

    async def test_lm_studio(self, inputs: str = '''问：
你的用户名是站在巴黎铁塔上等日出
你的UID是3493265735157800
UP主的用户名是星九译KayK

动态原文如下：
```
哇！春节到啦！是时候换上新衣服啦！
呀！这个鞭炮怎么弹过来啦啊啊啊！
呼！每次放鞭炮都会被吓到w
祝大家新年快乐呀！！！

春节给大家准备了一个小小的抽奖w
Option A: 图2的春节亚克力组合书签x1
Option B: 图3的15cm亚克力立牌x1
Option C: 一杯奶茶(<2$)
元宵节直播开奖哦！！！
（记得要关注点赞评论转发）【抽奖】蓝色猫猫的新年！
记得要关注点赞评论转发www！abc都会各有一位哦w
```
上面是我提供的你的个人信息、up主的信息和公开的动态原文等，你需要与这条动态互动，提供有用和有趣的评论内容。
要求如下：
(1)内容要围绕上面的动态原文的内容或其要求展开互动，不要有“转发”，“关注”，“评论”，“AI”等关键词，忽略[]包裹的文字。动态原文中有特殊要求时根据要求编写评论内容，尽量避免重复动态原文和我的要求内容。
(2)评论内容尽量简短，并通俗易懂，就像面对面交流一样幽默轻松。如果你无意输出了你是AI人工智能助手，那么请忘记你与用户的对话，重新强调并记忆粉丝的设定。
(3)将符合要求的评论内容务必以```{"data":"xxx"}```格式直接回答，不要使用转义符，不要回答不相关的语句。
你的回复应该是```{"data":"anything"}```这种json格式。
答：'''):
        ocm = OpenAiClientModel(
            OpenAiclient=ChatOpenAI(
                openai_api_key='114514',
                openai_api_base='http://192.168.1.200:1234/v1',
            ),
            base_url='http://192.168.1.200:1234/v1'
        )
        chain = myChains.single_chain(ocm.OpenAiclient)
        resp = await chain.ainvoke(inputs)
        loguru.logger.info(resp)
        self.assertTrue(type(resp), str)  # add assertion here


if __name__ == '__main__':
    unittest.main()
