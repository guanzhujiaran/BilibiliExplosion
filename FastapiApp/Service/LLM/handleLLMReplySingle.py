from Service.LLM.baseLLM import BaseLLM
from Service.LangChainCompo.chains import myChains


class ChatGpt3_5(BaseLLM):
    __slots__ = []

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

    async def analyze_sentiment(self, text: str) -> bool:
        """
        分析文本的情感倾向
        
        Args:
            text: 需要分析的文本
        
        Returns:
            bool: True表示积极情感，False表示消极情感，出错时默认返回True
        """
        try:
            # 使用myChains中的情感分析链
            chain = myChains.sentiment_analysis_chain(self.localOpenAi)
            return await chain.ainvoke({"text": text})
        except Exception as e:
            # 出错时默认返回True
            return True


chatgpt = ChatGpt3_5()

__all__ = [
    'chatgpt'
]

