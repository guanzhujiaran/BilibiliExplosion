from fastapi接口.service.baseLLM import BaseLLM


class ChatGpt3_5(BaseLLM):
    async def SingleReply(self, inputs: str):
        return await self.llm.ainvoke(inputs)
