from langchain_openai import OpenAI
from CONFIG import CONFIG


class BaseLLM:
    llm = OpenAI(
        openai_api_key=CONFIG.chat_gpt_config.open_ai_api_key,
        openai_api_base=CONFIG.chat_gpt_config.baseurl
    )
