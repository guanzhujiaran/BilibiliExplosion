import unittest
from fastapi接口.service.handleLLMReplySingle import ChatGpt3_5


class MyTestCase(unittest.IsolatedAsyncioTestCase):
    __ = ChatGpt3_5()

    async def test_SingleReply(self):
        resp = await self.__.SingleReply('114514')
        print(resp)
        self.assertTrue(type(resp), str)  # add assertion here


if __name__ == '__main__':
    unittest.main()
