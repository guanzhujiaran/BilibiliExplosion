import re
import time

import requests
import Bilibili_methods.all_methods

Bapi = Bilibili_methods.all_methods.methods()


class get_thumb_user:
    def spec_item_likes(self, dyid, pn):
        url = 'http://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/spec_item_likes?dynamic_id={dyid}&pn={pn}&ps=20'.format(
            dyid=dyid, pn=pn)
        req = requests.get(url)
        return req.json()

    def User_parse(self, req_json):
        c_l = list()
        for i in req_json.get('data').get('item_likes'):
            c_l.append(
                ['https://space.bilibili.com/{}/dynamic '.format(i.get('uid')), i.get('uname'), i.get('user_info').get('level_info').get('current_level'), repr(i.get('user_info').get('sign')),
                 i.get('user_info').get('official_verify').get('type'),i.get('user_info').get('official_verify').get('desc'), Bapi.timeshift(i.get('time'))])
        return c_l

    def get_all_thumb_user(self, dyid):
        pn = 1
        u_list = list()
        while 1:
            res = self.spec_item_likes(dyid, pn)
            total = res.get('data').get('total_count')
            print('\t\t\t\t\t\t\t【当前进度：{}/{}】'.format(pn, int(total / 20) + 1))
            has_more = res.get('data').get('has_more')
            l = self.User_parse(res)
            u_list.extend(l)
            if str(has_more) == '0':
                print('该动态获取结束')
                break
            time.sleep(3)
            pn+=1
        return u_list

    def do(self, dynamic_list):
        info_dict = dict()
        dynamic_list = list(set(dynamic_list))
        for i in dynamic_list:
            if not 't.bilibili' in i:
                dyid = i
            else:
                dyid = re.findall('t.bilibili.com/(\d+)', i)
                if dyid:
                    dyid = int(dyid[0])
                else:
                    print('动态id获取出错')
                    print(dyid)
                    continue
            info_dict.update({dyid: self.get_all_thumb_user(dyid)})

        for i in info_dict.keys():
            print('https:t.bilibili.com/{}'.format(i))
            #print(info_dict.get(i))
            try:
                with open('./log/获取点赞信息.csv', 'a+', encoding='utf-8') as f:
                    f.writelines('https:t.bilibili.com/{}\n'.format(i))
                    for j in info_dict.get(i):
                        for t in j:
                            if t != j[-1]:
                                f.writelines('{},'.format(t))
                            else:
                                f.writelines('{}\n'.format(t))
            except:
                with open('./log/获取点赞信息.csv', 'w', encoding='utf-8') as f:
                    f.writelines('https:t.bilibili.com/{}\n'.format(i))
                    for j in info_dict.get(i):
                        for t in j:
                            if t != j[-1]:
                                f.writelines('{},'.format(t))
                            else:
                                f.writelines('{}\n'.format(t))
        print('点赞用户获取完毕，前往log文件夹下查看')

if __name__ == '__main__':
    g = get_thumb_user()
    g.do(['https://t.bilibili.com/706501212450586663'])
