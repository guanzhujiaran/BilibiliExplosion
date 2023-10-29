# -*- coding: utf-8 -*- #
import ast
# ------------------------------------------------------------------
# Description:      Search_generate_reserve_lottery:从所有的直播预约中筛选出有抽奖的内容
# ------------------------------------------------------------------
import os

from functools import reduce

import json
import pandas


def file_remove_repeat_contents(filename):
    s = set()
    l = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line not in s:
                s.add(line)
                l.append(line)
    if l:
        with open(filename, "w", encoding="utf-8") as f:
            for line in l:
                f.write(line + "\n")


def remove_list_dict_duplicate(list_dict_data):
    """
    对list格式的dict进行去重

    """
    run_function = lambda x, y: x if y in x else x + [y]
    return reduce(run_function, [[], ] + list_dict_data)


def mix_dict_resolve(my_dict: dict, parent_key=None) -> dict:
    '''
    多层dict解码，键名用.分割不同的key下内容
    :param my_dict:
    :param parent_key:
    :return:
    '''
    if parent_key is None:
        parent_key = []
    ret_dict = dict()
    for k, v in my_dict.items():
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except:
                pass
        if isinstance(v, dict):
            parent_key.append(k)
            ret_dict.update(mix_dict_resolve(v, parent_key))
            continue
        key_prename = ''
        # if parent_key:
        #     key_prename = '.'.join(parent_key) + '.'
        ret_dict.update({key_prename + k: str(v)})
    return ret_dict


def resolve_dict_key(my_dict):
    k_list = []
    for k, v in my_dict.items():
        if isinstance(v, dict):
            k_list.extend(resolve_dict_key(v))
        else:
            k_list.append(k)
    return k_list


def Search_generate_reserve_lottery():
    if not os.path.exists('result'):
        os.mkdir('result')
    all_reserve_file_name = '所有直播预约.csv'
    file_remove_repeat_contents(all_reserve_file_name)
    # have_got_reserve_sid_List = []
    # if os.path.exists('result/全部抽奖预约.csv'):
    #     reserve_sid_df = pandas.read_csv('result/全部抽奖预约.csv', dtype=str)
    #     have_got_reserve_sid_List = list(reserve_sid_df.to_dict().get('sid'))
    lottery_reserve_list = []
    with open(all_reserve_file_name, 'r', encoding='utf-8') as f:
        for i in f.readlines():
            try:
                req_dict = ast.literal_eval(i.strip())
                if req_dict.get('data'):
                    if req_dict.get('data').get('list').get(str(req_dict.get('ids'))).get('lotteryType') == 1:
                        req_dict.pop('update_time', None)
                        lottery_reserve_list.append(mix_dict_resolve(req_dict))
            except:
                print(f'ERROR\t{i.strip()}')
    lottery_reserve_list = remove_list_dict_duplicate(lottery_reserve_list)  # 去重
    lottery_reserve_list = sorted(lottery_reserve_list, key=lambda x: x['dynamicId'])
    df = pandas.DataFrame(lottery_reserve_list)
    # if os.path.exists('result/全部抽奖预约.csv'):
    #     df.to_csv('result/全部抽奖预约.csv', mode='a+', header=False, encoding='utf-8', index=False,sep='滹')
    # else:
    df.to_csv('result/全部抽奖预约.csv', header=True, encoding='utf-8', index=False, sep='滹')
    file_remove_repeat_contents('result/全部抽奖预约.csv')

    newly_updated_reserve_list = []
    newly_updated_reserve_file_name = '最后一次更新的直播预约.csv'
    with open(newly_updated_reserve_file_name, 'r', encoding='utf-8') as f:
        for i in f.readlines():
            req_dict = eval(i.strip())
            if req_dict.get('data'):
                if req_dict.get('data').get('list').get(str(req_dict.get('ids'))).get('lotteryType') == 1:
                    # and str(req_dict.get('ids')) not in have_got_reserve_sid_List:
                    req_dict.pop('update_time', None)
                    newly_updated_reserve_list.append(mix_dict_resolve(req_dict))

    if len(newly_updated_reserve_list) == 0:
        exit('更新抽奖数量为0，检查代码！')
    newly_updated_reserve_list = remove_list_dict_duplicate(newly_updated_reserve_list)  # 去重
    newly_updated_reserve_list = sorted(newly_updated_reserve_list, key=lambda x: x['dynamicId'])
    df = pandas.DataFrame(newly_updated_reserve_list)
    open('result/更新的抽奖预约.csv', 'w').close()
    df.to_csv('result/更新的抽奖预约.csv', header=True, encoding='utf-8', index=False, sep='滹')
    file_remove_repeat_contents('result/更新的抽奖预约.csv')


if __name__ == '__main__':
    Search_generate_reserve_lottery()
