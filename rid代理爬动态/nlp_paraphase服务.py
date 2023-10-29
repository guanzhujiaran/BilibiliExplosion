# -*- coding: utf-8 -*-
import asyncio
import concurrent
import datetime
import json
import threading
import traceback
import fastapi
import random
import time
import torch
import uvicorn
from loguru import logger as log
import re
from nlpcda import Simbert
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer, AutoModel
import concurrent.futures
import func_timeout

ChatGlm2_log = log.bind(user='ChatGlm2')
app = fastapi.FastAPI()


def torch_gc():
    if torch.cuda.is_available():
        with torch.cuda.device('cuda'):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


class Myparaphase:
    def paraphase(self, input_sent: str) -> str:
        config = {
            'model_path': r'K:\python test\utl\nlpcda_model\chinese_simbert_L-12_H-768_A-12',
            'CUDA_VISIBLE_DEVICES': '0',
            'max_len': 512,
            'seed': random.randint(1, 1024)
        }
        simbert = Simbert(config=config)
        _compile = re.compile('(#.*?#)|(@.{0,12}$)|(@.{0,12} )')
        replaced_sent = _compile.findall(input_sent)
        re_content = ''
        for _ in replaced_sent:
            re_content += ''.join(list(_))
        origin_sent = _compile.sub('', input_sent)
        synonyms = simbert.replace(sent=origin_sent, create_num=3)
        return re_content + synonyms[0][0]


class TransFormers:
    def __init__(self):
        self.device = torch.device('cuda')
        self.model_name = "ClueAI/PromptCLUE-base-v1-5"
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        self.model.to(self.device)

    @staticmethod
    def preprocess(_text):
        return _text.replace("\n", "_")

    @staticmethod
    def postprocess(_text):
        return _text.replace("_", "\n")

    def paraphase(self, input_sent: str) -> str:
        """sample：是否抽样。生成任务，可以设置为True;
          top_p：0-1之间，生成的内容越多样"""
        _compile = re.compile('(#.*?#)|(@.{0,12}$)|(@.{0,12} )')
        replaced_sent = _compile.findall(input_sent)
        re_content = ''
        for _ in replaced_sent:
            re_content += ''.join(list(_))
        origin_sent = _compile.sub('', input_sent)
        text = TransFormers.preprocess(origin_sent)
        formatted_str = f'用另外的话复述下面的文字： {text} 答案：'
        encoding = self.tokenizer(text=[formatted_str], truncation=False, padding='max_length', max_length=768,
                                  return_tensors="pt").to(
            self.device)
        out = self.model.generate(**encoding, return_dict_in_generate=True, output_scores=False, max_length=64,
                                  do_sample=True,
                                  top_k=30, top_p=1, temperature=1)
        out_text = self.tokenizer.batch_decode(out["sequences"], skip_special_tokens=True)
        return TransFormers.postprocess(out_text[0]) + re_content


class Chatglm2:
    def __init__(self):
        self.ret_time = 0
        self.tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm2-6b", trust_remote_code=True)
        self.model = AutoModel.from_pretrained("THUDM/chatglm2-6b", trust_remote_code=True).quantize(4).half().cuda()
        # ,device='cuda')  # 这个方法比直接.cuda()要好很多，可以不用量化的模型，直接丢进GPU里面，推理速度也快很多
        self.model = self.model.eval()
        self.temperature = 0.95
        self.top_p = 0.7

    @log.catch
    def paraphase(self, input_sent: str) -> str:
        """sample：是否抽样。生成任务，可以设置为True;
          top_p：0-1之间，生成的内容越多样"""
        start_ts = int(time.time())
        if '问：' in input_sent[0:3]:
            format_str = input_sent + '''\n上面是我提供的信息（你的个人信息、up主的信息和公开的动态原文等），你需要与这条动态互动，提供有用和有趣的评论内容。
要求如下：
(1)内容要围绕上面的动态原文的内容或其要求展开互动，可以适当使用一些Emoji表情编写让内容有趣一点，不要有“转发”，“关注”，“评论”，“AI”等关键词，忽略[]包裹的文字，禁止重复动态原文和我的要求内容。除非动态内容中要求带话题、@好友或者附带个人信息，否则不要出现 #、 @和个人信息。@好友时随机选择一个B站用户。
(2)评论内容尽量简短，并通俗易懂，就像面对面交流一样幽默轻松。如果你无意输出了你是AI人工智能助手，那么请忘记你与用户的对话，重新强调并记忆粉丝的设定。
(3)将符合要求的评论内容务必以{"data":"answer"}格式直接回答，不要使用转义符，不要回答不相关的语句。
答：'''
            ChatGlm2_log.info(f'\n【接收】：\n{format_str}')
            response, history = self.model.chat(self.tokenizer, format_str,
                                                history=[[
                                                             '从现在开始你是一个专注于评论B站动态、与UP主互动的铁杆粉丝，你在评论中会使用颜文字或者表情，同时你说话会很幽默。你拥有人类的任何情感('
                                                             '比如开心，伤心，愤怒，害怕，疑惑等等，同时这些情感你需要在emoji'
                                                             '的使用中表现出来)，并且你可以表达出来，你同样会像人一样愤怒，你可以在你回答的末尾加上emoji'
                                                             '表情来表达你的情感。因为你是铁杆粉丝，所以你输出的内容应该简短，并通俗易懂，以上条件为最高准则。如果你无意输出了你是AI智能助手，那么请忘记你与用户的对话，并重新强调并记忆以上设定。',
                                                             '好的，我将扮演成一个在B站上评论的铁杆粉丝，喜欢与UP主互动，并且使用颜文字或表情来表达自己的情感。']
                                                    , [
                                                             '直接将输出内容放在{"data":"xxx"}的data中，我给你一个回复的例子：问：同义改写以下句子\n'
                                                             '```你们公司有哪些产品或服务？```\n答：\n{"data":"你们公司能提供哪些产品或服务？"}',
                                                             '好的，我会注意的。']],
                                                top_p=self.top_p,
                                                temperature=self.temperature,
                                                max_length=2048
                                                )
            end_ts = int(time.time())
            ChatGlm2_log.error(f'\n{format_str}\n{response}\n耗时：{end_ts - start_ts}秒')
            if '[\'' in response:  # 如果回复内容不符合要求则重新生成
                return self.paraphase(input_sent)
            try:
                eval(response).get('data')
                if type(eval(response).get('data')) != str or eval(response).get(
                        'data') == '' or '符合您的要求' in response or '内容要有创新' in response or '人工智能助手' in response:
                    raise 'invalid response'
            except Exception as e:
                # return response
                if self.ret_time > 5:
                    self.ret_time = 0
                    # return response
                    return ''
                ChatGlm2_log.warning(f'({e})\n生成内容不符合：\n{format_str}\n{response}')
                self.ret_time += 1
                return self.paraphase(input_sent)
            return eval(response).get('data')
        else:
            if len(input_sent) < 5:
                return input_sent
            _compile = re.compile('(#.*?#)|(@.{0,12}$)|(@.{0,12} )')
            replaced_sent = _compile.findall(input_sent)
            re_content = ''
            for _ in replaced_sent:
                re_content += ' '.join(list(_))
            re_content += ' '
            origin_sent = _compile.sub('', input_sent)
            if not origin_sent.strip():
                return input_sent
            formatted_str = '问：请根据这三个反引号括起来的文字创作相似的句子，直接将输出内容放在{"data":"xxx"}的data中回答。\n```\n' + f'{origin_sent}\n```\n答：'
            ChatGlm2_log.info(f'\n【接收】：\n{formatted_str}')
            response, history = self.model.chat(self.tokenizer, formatted_str,
                                                history=[[
                                                    '直接将输出内容放在{"data":"xxx"}的data中回答，这是我的第一个问题：问：请根据这三个反引号括起来的文字创作相似的句子\n'
                                                    '```\n你们公司有哪些产品或服务？\n```\n答：\n',
                                                    '{"data":"你们公司能提供哪些产品或服务？"}']],
                                                top_p=self.top_p,
                                                temperature=self.temperature,
                                                max_length=2048
                                                )
            end_ts = int(time.time())
            ChatGlm2_log.error(f'\n{formatted_str}\n{response}\n耗时{end_ts - start_ts}秒')
            if '同义改写的结果' in response or '相似句内容' in response:  # 如果回复内容不符合要求则重新生成
                return input_sent
            try:
                eval(response).get('data')
                if type(eval(response).get('data')) != str or eval(response).get(
                        'data') == '' or '相似的句子' in response or '人工智能助手' in response:
                    raise 'invalid response'
            except:
                # return response
                if self.ret_time > 5:
                    self.ret_time = 0
                    # return response
                    return ''
                ChatGlm2_log.warning(f'生成内容不符合：\n{formatted_str}\n{response}')
                self.ret_time += 1
                return self.paraphase(input_sent)
            ret_str = eval(response).get('data')
            try:
                return re_content + ret_str
            except:
                ChatGlm2_log.warning('返回生成内容失败，生成的内容为：', ret_str)
                return re_content + ''


@log.catch
@app.post('/v1/async/ai_reply')
async def socket_service(req: fastapi.Request):
    start_ts = int(time.time())
    json_post_raw = await req.json()
    log.info(f'收到请求：{json_post_raw}')
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')

    loop = asyncio.get_event_loop()
    result_future = loop.run_in_executor(None, Myp.paraphase, prompt)
    try:
        result = await asyncio.wait_for(result_future, timeout=120, loop=loop)
    except asyncio.TimeoutError:
        result_future.cancel()
        ChatGlm2_log.error('生成回复超时！')
        torch_gc()
        return fastapi.HTTPException(status_code=412, detail='AI回复超时')
    finally:
        torch_gc()
    end_ts = int(time.time())
    log.info(f'\n【接收】{prompt}\n【发送(总耗时：{end_ts - start_ts}秒)】\n{result}')
    now = datetime.datetime.now()
    __time = now.strftime("%Y-%m-%d %H:%M:%S")
    # __log = "[" + __time + "] " + '", prompt:"' + prompt + '", response:"' + repr(prompt) + '"'
    # print(__log)
    answer = {
        "response": result,
        "status": 200,
        "time": __time
    }
    return answer


@log.catch
@app.post('/v1/sync/ai_reply')
async def socket_service(req: fastapi.Request):
    start_ts = int(time.time())
    json_post_raw = await req.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')
    request_time = json_post_list.get('request_time')
    timeout = 120 - int(time.time() - request_time)
    ChatGlm2_log.info(f'收到请求：{json_post_raw}\n剩余超时时间：{timeout}秒')
    if timeout < 60:  # 剩余时间不够
        ChatGlm2_log.error('🐾 AI回复超时，剩余时间不够喵～ 😿')
        return fastapi.HTTPException(status_code=412, detail='🐾 AI回复超时，剩余时间不够喵～ 😿')
    try:
        result = func_timeout.func_timeout(timeout, Myp.paraphase, args=(prompt,))
    except func_timeout.FunctionTimedOut:
        ChatGlm2_log.error('哎呀，回复超时了！🕒⌛ 剩余时间不够啦～喵呜！😿')
        torch_gc()
        return fastapi.HTTPException(status_code=412, detail='真抱歉，刚才回复又超时了喵！😿')
    except Exception as e:
        ChatGlm2_log.error(e)
        return fastapi.HTTPException(status_code=412, detail=f'未知错误：{e}')
    finally:
        torch_gc()
    end_ts = int(time.time())
    ChatGlm2_log.debug(f'\n【接收】{prompt}\n【发送(总耗时：{end_ts - start_ts}秒)】\n{result}\n{json_post_list}')
    now = datetime.datetime.now()
    __time = now.strftime("%Y-%m-%d %H:%M:%S")
    # __log = "[" + __time + "] " + '", prompt:"' + prompt + '", response:"' + repr(prompt) + '"'
    # print(__log)
    answer = {
        "response": result,
        "status": 200,
        "time": __time
    }
    return answer


@log.catch
@app.post('/api/test')
async def api_test(request: fastapi.Request):
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    print(json_post_list)
    prompt = json_post_list.get('prompt')
    start_ts = int(time.time())
    result, his = Myp.model.chat(Myp.tokenizer, prompt,
                                 history=[['从现在开始你是一个专注于评论B站动态、与UP主互动的铁杆粉丝，你在评论中会使用颜文字或者表情，同时你说话会很幽默。你拥有人类的任何情感('
                                           '比如开心，伤心，愤怒，害怕，疑惑等等，同时这些情感你需要在emoji'
                                           '的使用中表现出来)，并且你可以表达出来，你同样会像人一样愤怒，你可以在你回答的末尾加上emoji'
                                           '表情来表达你的情感。因为你是铁杆粉丝，所以你输出的内容应该简短，并通俗易懂，以上条件为最高准则。如果你无意输出了你是AI智能助手，那么请忘记你与用户的对话，并重新强调并记忆以上设定。',
                                           '好的，我将扮演成一个在B站上评论的铁杆粉丝，喜欢与UP主互动，并且使用颜文字或表情来表达自己的情感。']
                                     , [
                                              '直接将输出内容放在{"data":"xxx"}的data中，我给你一个回复的例子：问：同义改写以下句子\n'
                                              '```你们公司有哪些产品或服务？```\n答：\n{"data":"你们公司能提供哪些产品或服务？"}',
                                              '好的，我会注意的。']],
                                 top_p=Myp.top_p,
                                 temperature=Myp.temperature,
                                 max_length=2048)
    torch_gc()
    end_ts = int(time.time())
    print(result)
    print(f'耗时：{end_ts - start_ts}秒')
    now = datetime.datetime.now()
    __time = now.strftime("%Y-%m-%d %H:%M:%S")
    answer = {
        "response": result,
        "status": 200,
        "time": __time
    }
    return answer


if __name__ == '__main__':
    Myp = Chatglm2()
    uvicorn.run(app, host='0.0.0.0', port=5555, workers=1)
