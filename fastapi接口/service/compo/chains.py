from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

class myChains:

    @staticmethod
    def single_chain(LLM:BaseChatModel):
        """
        单个回复chain，不带记忆，不带提示语
        :param LLM:
        :return:
        """
        chain = LLM | StrOutputParser()
        return chain
