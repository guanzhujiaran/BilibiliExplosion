# -*- coding: utf-8 -*-
import pandas as pd

format_list=[]
with open('../recorded_proxy.txt','r',encoding='utf-8') as f :
    for line in f.readlines():
        format_list.append(eval(line.strip()))

df = pd.DataFrame(format_list)
df.to_csv('格式化的代理内容.csv',header=True,index=False)