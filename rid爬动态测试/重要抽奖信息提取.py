import time

import Bilibili_methods.paddlenlp

if __name__ =='__main__':
    s = int(time.time())
    a = Bilibili_methods.paddlenlp.my_paddlenlp()
    tlist = []
    f = open('./rid每日动态.csv', 'r', encoding='utf-8')
    temp = f.readlines()
    f.close()
    for i in temp:
        try:
            tlist.append(eval(i.split('\t')[3]))
        except:
            print(i)
    replylist = []
    for i in tlist:
        rep = a.information_extraction(i, ['奖品','开奖日期'])
        replylist.append([rep['奖品'],rep['开奖日期']])
    f = open('./ai提取信息.csv', 'w', encoding='utf-8')
    for i in range(len(temp)):
        f.writelines(f'{temp[i].strip()}\t{replylist[i][0]}\t{replylist[i][1]}\n')
    f.close()
    e = int(time.time())
    print(f'耗时{e - s}')
    print(f'平均每条耗时{(e - s) / len(temp)}秒')