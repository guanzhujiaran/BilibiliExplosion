import asyncio

from fastapi接口.service.baseLLM import BaseLLM
from fastapi接口.service.compo.chains import myChains


class ChatGpt3_5(BaseLLM):

    async def SingleReply(self, inputs: str):
        try:
            chain = myChains.single_chain(self.OpenAIClient.OpenAiclient)
            return await chain.ainvoke(inputs)
        except Exception as e:
            self.OpenAIClient.isAvailable = False
            raise e
