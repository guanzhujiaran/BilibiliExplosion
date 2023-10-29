import time
import requests
import random
import json
class Dm:
    def send_msg(self,msg,rid):
        url='https://api.live.bilibili.com/msg/send'
        data={
            'bubble': '0',
            'msg':msg,
            'color': '5566168',
            'mode': '1',
            'fontsize': '25',
            'rnd':int(time.time()),
            'roomid': rid,
            'csrf': '62a12e951547a821766e96d357b3ebf9',
            'csrf_token': '62a12e951547a821766e96d357b3ebf9'
            }
        headers={
            "cookie": "SESSDATA=c356c770%2C1642774741%2C1f708%2A71;bili_jct=62a12e951547a821766e96d357b3ebf9",
            "user - agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67"
        }

        response=requests.request("POST",url,headers=headers,data=data)

        reqdict = json.loads(response.text)
        print(reqdict)

msglist=["(⌒▽⌒)","(⌒▽⌒)","(=・ω・=)","(｀・ω・´)","(〜￣△￣)〜","(･∀･)","(°∀°)ﾉ","(￣3￣)","╮(￣▽￣)╭","_(:3」∠)_","( ´_ゝ｀)","←_←","→_→","(<_<)","(>_>)","(;¬_¬)","(▔□▔)/","(ﾟДﾟ≡ﾟдﾟ)!?","Σ(ﾟдﾟ;)","Σ( ￣□￣||)","(´；ω；`)","（/TДT)/","(^・ω・^ )","(｡･ω･｡)","(●￣(ｴ)￣●)","ε=ε=(ノ≧∇≦)ノ","(´･_･`)","(-_-#)","（￣へ￣）","(￣ε(#￣) Σ","ヽ(`Д´)ﾉ","（#-_-)┯━┯","(╯°口°)╯(┴—┴","←◡←","( ♥д♥)","Σ>―(〃°ω°〃)♡→","⁄(⁄ ⁄•⁄ω⁄•⁄ ⁄)⁄","(╬ﾟдﾟ)▄︻┻┳═一","･*･:≡(　ε:)","(汗)"]
group=['1361615','13786821','21437724','21626454','22304399','22254771']
cls = Dm()
for x in group:
    cls.send_msg(random.choice(msglist),x)
    time.sleep(1)