from fastapi接口.service.LLM.baseLLM import BaseLLM
from fastapi接口.service.compo.chains import myChains


class ChatGpt3_5(BaseLLM):

    async def SingleReply(self, inputs: str):
        try:
            chain = myChains.single_chain(self.OpenAIClient.OpenAiclient)
            return await chain.ainvoke(inputs)
        except Exception as e:
            if '127.0.0.1' in self.OpenAIClient.base_url or '192.168' in self.OpenAIClient.base_url:
                ...  # 本地部署的大模型不需要设置出错
            else:
                self.OpenAIClient.isAvailable = False
            raise e
