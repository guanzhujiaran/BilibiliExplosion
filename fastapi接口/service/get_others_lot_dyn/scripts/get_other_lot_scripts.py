import asyncio
from typing import Sequence

from fastapi接口.service.get_others_lot_dyn.Sql.models import TLotuserspaceresp
from fastapi接口.service.get_others_lot_dyn.Sql.sql_helper import SqlHelper,get_other_lot_redis_manager
from fastapi接口.service.get_others_lot_dyn.get_other_lot_main import BiliDynamicItem
from fastapi接口.utils.Common import sem_gen

_sem = sem_gen()

async def get_other_lot_by_lot_round_id(lot_round_id):
    space_lots:Sequence[TLotuserspaceresp] = await SqlHelper.getSpaceRespByRoundId(lot_round_id)
    all_target_uid_list = await get_other_lot_redis_manager.get_target_uid_list()
    all_dynamic_items = set()
    for x in space_lots:
        if x.spaceUid not in all_target_uid_list:
            all_dynamic_items.add(
                BiliDynamicItem(
                    dynamic_id=x.spaceOffset,
                    dynamic_raw_resp={'code': 0, 'data': {"item": x.spaceRespJson}},
                )
            )
        else:
            dynamic_item = x.spaceRespJson
            if dynamic_item.get('type') == 'DYNAMIC_TYPE_FORWARD':
                orig_dynamic_item = dynamic_item.get('orig')
                orig_dynamic_id_str = orig_dynamic_item.get('id_str')
                orig_single_dynamic_resp = {
                    'code': 0,
                    'data':
                        {
                            "item": orig_dynamic_item
                        }
                }
                orig_bili_dynamic_item = BiliDynamicItem(dynamic_id=orig_dynamic_id_str,
                                                         dynamic_raw_resp=orig_single_dynamic_resp)
                all_dynamic_items.add(orig_bili_dynamic_item)

    highlight_word_list = [
        'jd卡',
        '京东卡',
        '京东E卡',
        '红包',
        '主机',
        '显卡',
        '电脑',
        '天猫卡',
        '猫超卡',
        '现金',
        '见盘',
        '耳机',
        '鼠标',
        '手办',
        '景品',
        'ps5',
        '内存',
        '风扇',
        '散热',
        '水冷',
        '硬盘',
        '显示器',
        '主板',
        '电源',
        '机箱',
        'fgo',
        '折现',
        '樱瞳',
        '盈通',
        '🧧',
        '键盘',
        '游戏本',
        '御神子',
        '琉璃子',
        '固态',
        '手机',
        'GB',
        'TB',
        'tb',  # 可能是显存大小，硬盘容量，内存条容量等参数
        'switch',
        '冰箱'
    ]
    print(f'总共{len(all_dynamic_items)}条动态需要检查')
    task_set = set()
    for x in all_dynamic_items:
        await _sem.acquire()
        task = asyncio.create_task(x.judge_lottery(highlight_word_list,lot_round_id))
        task.add_done_callback(lambda __: _sem.release())
        task_set.add(task)
    await asyncio.gather(
        *task_set
    )
    print(all_dynamic_items)

if __name__ =="__main__":
    asyncio.run(get_other_lot_by_lot_round_id(234))