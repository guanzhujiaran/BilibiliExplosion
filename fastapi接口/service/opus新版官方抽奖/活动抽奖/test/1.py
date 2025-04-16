import json
from typing import List

from bs4 import BeautifulSoup
from curl_cffi import requests

from fastapi接口.service.opus新版官方抽奖.活动抽奖.model.EraBlackBoard import EraTask, EraLotteryConfig, EraVideoSourceCONFIG, \
    H5ActivityLottery, H5ActivityLotteryGiftSource, MatchLotteryTask, MatchLottery, EvaContainerTruck


def handle_topic_lottery_url(url):
    resp = requests.get(url, )
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 查找包含 window.__initialState 的脚本标签
    script_tags = soup.find_all('script')
    # region era活动（url里面带有era
    if 'era/' in url:
        for tag in script_tags:
            if '__initialState' in tag.text:
                # 尝试从字符串中提取 JSON 数据
                start_index = tag.string.find('__initialState = ')
                end_index = tag.string.find(';\n', start_index)
                data_str = tag.string[start_index + len('__initialState = '):end_index].strip()
                # 将字符串转换为字典
                data = json.loads(data_str)
                era_tasks = []
                for x in data.get('EraTasklist', data.get('EraTasklistPc', [])):
                    for y in x.get('tasklist', []):
                        try:
                            era_tasks.append(EraTask.model_validate(y))
                        except Exception as e:
                            print(e)
                            print(y)
                era_lottery_configs = [EraLotteryConfig.model_validate(x['config']) for x in
                                       data.get('EraLottery', data.get('EraLotteryPc', [])) if x.get('config')]
                era_video_configs = [EraVideoSourceCONFIG.model_validate(x['config']) for x in
                                     data.get('EraVideoSource', data.get("EraVideoSourcePc", [])) if x.get('config')]
                era_jika = [EvaContainerTruck(
                    activityUrl=x.get('cardGeneralBigDispositionProps').get('cardQrcodePanel').get('activityUrl'),
                    jikaId=x.get('config').get('selected'),
                    topId=x.get('cardShareMessage').get('topId'),
                    topName=x.get('cardShareMessage').get('topName')
                ) for x in data.get('EvaContainerTrucksH5', [])
                ]
                print(f'抽奖任务：{era_tasks}')
                print(f'抽奖内容：{era_lottery_configs}')
                print(f'视频活动：{era_video_configs}')
                print(f'集卡活动：{era_jika}')
                break
    # endregion

    # region h5转盘抽奖
    elif '/activity-' in url:
        for tag in script_tags:
            if '__initialState' in tag.text:
                # 尝试从字符串中提取 JSON 数据
                start_index = tag.string.find('__initialState = ')
                end_index = tag.string.find(';\n', start_index)
                data_str = tag.string[start_index + len('__initialState = '):end_index].strip()
                # 将字符串转换为字典
                data = json.loads(data_str)
                if data.get('h5-lottery-v3', []):
                    h5_lottery = [H5ActivityLottery(
                        lotteryId=x.get('lotteryId'),
                        continueTimes=x.get('continueTimes'),
                        list=[H5ActivityLotteryGiftSource.model_validate(y) for y in x.get('list').get('source')],
                    ) for x in data.get('h5-lottery-v3', [])]
                    print(h5_lottery)
                if data.get('match-lottery-task-pc'):
                    match_task: List[MatchLotteryTask] = []
                    match_lottery = [MatchLottery(
                        activity_id=x.get('activity_id'),
                        lottery_id=x.get('lottery_id'),
                    ) for x in data.get('match-lottery-pc', [])]
                    for x in data.get('match-lottery-task-pc'):
                        for y in x.get('tasks', []):
                            try:
                                match_task.append(MatchLotteryTask.model_validate(y))
                            except Exception as e:
                                print(e)
                                print(y)
                    print(match_task)
                    print(match_lottery)
                break
    # endregion
    elif 'dynamic/' in url:
        native_page_dynamic_index_api = 'https://api.bilibili.com/x/native_page/dynamic/index?page_id=344929&jsonp=jsonp'
        native_page_resp = requests.get(native_page_dynamic_index_api)
        native_page_resp_dict = native_page_resp.json()
        pc_url = native_page_resp_dict.get('data').get('pc_url')

        return handle_topic_lottery_url(pc_url)
    else:
        for tag in script_tags:
            if '__initialState' in tag.text:
                # 尝试从字符串中提取 JSON 数据
                start_index = tag.string.find('__initialState = ')
                end_index = tag.string.find(';\n', start_index)
                data_str = tag.string[start_index + len('__initialState = '):end_index].strip()
                # 将字符串转换为字典
                data = json.loads(data_str)
                jump_url = list(set([x.get('button_jump_url') for x in data.get('h5-button', data.get('button', [])) if
                                     'blackboard' in x.get('button_jump_url', '')]))
                print(jump_url)  # TODO 这里完成之后，递归抽奖链接
                for x in jump_url:
                    handle_topic_lottery_url(jump_url)
                break


__ = 'https://www.bilibili.com/blackboard/dynamic/338975'
handle_topic_lottery_url(__)

