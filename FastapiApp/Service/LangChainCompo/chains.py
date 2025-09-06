import re

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import BaseTransformOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from operator import itemgetter

class CustomStrOutputParser(BaseTransformOutputParser[str]):
    """OutputParser that parses LLMResult into the top likely string."""

    @classmethod
    def is_lc_serializable(cls) -> bool:
        """Return whether this class is serializable."""
        return True

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        """Get the namespace of the langchain object."""
        return ["langchain", "schema", "output_parser"]

    @property
    def _type(self) -> str:
        """Return the output parser type for serialization."""
        return "CustomStrOutputParser"

    def parse(self, text: str) -> str:
        """Returns the input text with no changes."""
        return re.sub(r'<think>.*?</think>', '', text, flags=re.S)


class SentimentOutputParser(StrOutputParser):
    """解析情感分析结果的输出解析器"""
    
    def parse(self, text: str) -> bool:
        """
        解析模型输出，判断是否为积极情感
        
        Args:
            text: 模型输出的文本
            
        Returns:
            bool: True表示积极情感，False表示消极情感
        """
        return "positive" in text.strip().lower()


class myChains:

    @staticmethod
    def single_chain(LLM: BaseChatModel):
        """
        单个回复chain，不带记忆，不带提示语
        :param LLM:
        :return:
        """
        chain = LLM | CustomStrOutputParser()
        return chain
        
    @staticmethod
    def sentiment_analysis_chain(LLM: BaseChatModel):
        """
        情感分析chain，返回布尔值：True表示积极，False表示消极
        :param LLM: 语言模型
        :return: 返回一个可以分析情感的chain
        """
        # 创建提示模板
        prompt = ChatPromptTemplate.from_template(
            "请分析以下文本的情感倾向，只回答'positive'表示积极或'negative'表示消极：\n\n{text}"
        )
        
        # 创建链式处理流程
        chain = (
            {"text": itemgetter("text")}
            | prompt
            | LLM
            | SentimentOutputParser()
        )
        
        return chain
