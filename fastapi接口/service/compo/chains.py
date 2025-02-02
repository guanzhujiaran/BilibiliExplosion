import re

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser, BaseTransformOutputParser
from typing import List

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
