# -*- coding: utf-8 -*-
import random

import json
import pandas as pd
import pandasgui
from transformers import AutoModel, AutoTokenizer


tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm2-6b", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm2-6b", trust_remote_code=True, device='cuda')
model = model.eval()

while 1:
    origin_sent = ''
    while 1:
        inp = input('(按0结束输入)>>>')
        if inp != '0':
            origin_sent += inp + '\n'
        else:
            break
    response, history = model.chat(tokenizer, origin_sent, history=[], top_p=0.7, temperature=0.95, max_length=2048)
    print(f'【输入】\n{origin_sent}\n【输出】 {response}')

#
#
# dynamic_contents = []
# with open(r'F:\python test\github\my_operator\bili_upload\log\过滤抽奖信息.csv', 'r', encoding='utf-8') as f:
#     for i in f.readlines():
#         try:
#             Upname=i.split("\t")[1]
#             Dynamic_content = i.split("\t")[4]
#             input_sent = '问：\n'+f'UP主的昵称是{Upname}\n\n'+f'''---
# 动态原文如下：
#
# {Dynamic_content}
#
# 答：'''
#             dynamic_contents.append('''我希望你作为B站UP主的粉丝，与他的一条动态互动，我会提供你的个人信息和up主的信息，为了参与互动，需要写一段话发送在评论区，要求内容要有创新，能让人眼前一亮，不要有关键词：转发，关注，评论等，忽略[]包裹的文字，不要重复动态内容。除非动态内容中要求带话题、@好友或者附带个人信息，否则不要出现 #、 @和个人信息。@好友时随机选择一个B站用户。请用这样的格式返回：{"data":"需要写的一段话"}。
# ---\n\n
# ''' + input_sent)
#         except:
#             pass
#
# random.shuffle(dynamic_contents)
# dynamic_contents = dynamic_contents[0:100]
# csv_list = []
# for origin_sent in dynamic_contents:
#     formatted_str = origin_sent
#     response, history = model.chat(tokenizer, formatted_str, history=[], top_p=0.7,
#                                    temperature=0.95)
#     csv_list.append({"原始内容": origin_sent, "AI回复结果": response})
#
# df = pd.DataFrame(csv_list)
# df.to_csv('AI回答.csv', index=False,mode='a+',header=False)
# pandasgui.show(df)
