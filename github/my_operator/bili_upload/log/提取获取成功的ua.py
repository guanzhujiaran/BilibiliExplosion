# -*- coding: utf-8 -*-
import json
import traceback

ua_list = []
with open('获取成功的参数.csv', 'r', encoding="utf-8", errors='ignore') as f:
    for i in f.readlines():
        try:
            req_dict = json.loads(i.split('\t')[1].strip().replace('\'','"'))
            header = req_dict.get('headers')
            ua_list.append(header.get('user-agent'))
        except:
            traceback.print_exc()
            print(i.split('\t'))

ua_list = list(set(ua_list))
for i in ua_list:
    print(f'"{i}"')
