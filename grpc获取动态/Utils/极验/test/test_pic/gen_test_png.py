import json
import time
from curl_cffi import requests
import re
url = 'https://api.geevisit.com/refresh.php'
params= {
'gt': '7ce10f9b15bbf37b23fe38702cf82d7a',
'challenge': 'd6b603de7798c80ae9be2f084d662723',
'lang': 'zh-cn',
'type': 'click',
'callback': f'geetest_{int(time.time())}',
}

for i in range(99,100):
    resp = requests.get(url,params=params,impersonate='chrome120')
    resp_dict = json.loads(re.findall("geetest_[0-9]+\((.*?)\)",resp.text)[0])
    img_api = resp_dict.get('data').get('image_servers')[0]
    pic = resp_dict.get('data').get('pic')
    pic_resp = requests.get(f'https://{img_api}{pic}',impersonate='chrome120')
    with open(f'{i}.jpg','wb') as f:
        f.write(pic_resp.content)

