# -*- coding:utf- 8 -*-
import re
import time

class huoqujiangping:
    def getthings(self,origin,content):
        p.write(origin)
        things=re.findall(r'送(.{1,20})\'|送(.{1,20})\[|送出(.{1,20})\\|补贴(.{1,20})\'|送上(.{1,20})\'|送(.{1,20})\\n',content,re.S)
        if things!=[] and things!=['']:
            things=things[0]
            things=list(set(things))
            things.sort(reverse=True)
            things=things[0]
            things=re.sub(r'\\n|#.*?#|\[|]|【|】|~|。|出|～','',things)
            print(things)
            p.write('\t'+things)
        else:
            p.write('\t'+'None')


p=open('rid每日动态附带奖品信息.csv','w+',encoding='utf-8')
a=huoqujiangping()
with open('rid每日动态.csv','r',encoding='utf-8') as f:
    data = [item.strip() for item in f.readlines()]
    stime=data.pop(0)
    title=data.pop(0)
    p.write(stime+'\n')
    p.write(title+'\n')
    for i in data:
        try:
            content=re.findall(r'\'.*(\'.*\')',i,re.S)[0]
            a.getthings(i,content)
            p.write('\n')
        except:
            a.getthings(i,i)
            p.write('\n')
            print(i)

p.close()
f.close()