import json
import os.path
from datetime import datetime

from CONFIG import CONFIG
from langchain_openai import ChatOpenAI
from fastapi接口.models.v1.ChatGpt3_5.ReplySingleModel import OpenAiClientModel, LLMShowInfo


class BaseLLM:
    _OpenAiclients = [
        OpenAiClientModel(
            OpenAiclient=ChatOpenAI(openai_api_key=x.open_ai_api_key, openai_api_base=x.baseurl,
                                    model_name="gpt-3.5-turbo"),
            base_url=x.baseurl
        )
        for x in CONFIG.chat_gpt_configs
    ]

    def show_openai_client(self):
        available_num = 0
        for i in self._OpenAiclients:
            if i.isAvailable:
                available_num += 1
        _ = LLMShowInfo(available_num=available_num, total_num=len(self._OpenAiclients))
        _.llm_list = self._OpenAiclients
        return _

    @property
    def OpenAIClient(self) -> OpenAiClientModel:
        for i in self._OpenAiclients:
            if i.isAvailable:
                i.useNum += 1
                return i
            else:
                if (datetime.now() - i.latestUseDate).days >= 1:
                    i.useNum = 0
                    i.isAvailable = True
                    i.latestUseDate = datetime.now()
                    return i
        self.read_openai_client_from_json()
        raise Exception("No OpenAiClient is available")

    def read_openai_client_from_json(self):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chatgpt/conf.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                json_obj = json.loads(f.read())
            assert type(json_obj.get('openai')) is list, f'读取chatgpt配置文件出错，请检查文件内容\n{file_path}'
            u_list = [x.base_url for x in self._OpenAiclients]
            for i in json_obj.get('openai'):
                if i.get('baseurl') in u_list:
                    continue
                self._OpenAiclients.append(OpenAiClientModel(
                    OpenAiclient=ChatOpenAI(
                        openai_api_key=i.get('open_ai_api_key'),
                        openai_api_base=i.get('baseurl'),
                        model_name="gpt-3.5-turbo"),
                    base_url=i.get('baseurl'),
                ))
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps({
                    "openai": [
                        {
                            "baseurl": x.baseurl,
                            "open_ai_api_key": x.open_ai_api_key
                        }
                        for x in self._OpenAiclients
                    ]
                }))
