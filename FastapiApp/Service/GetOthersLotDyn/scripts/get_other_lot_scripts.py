import asyncio
from typing import Sequence

from Service.GetOthersLotDyn.Sql.models import TLotuserspaceresp
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper,get_other_lot_redis_manager
from Service.GetOthersLotDyn import BiliDynamicItem
from Utils.通用.Common import sem_gen, asyncio_gather

_sem = sem_gen(100)

async def get_other_lot_by_lot_round_id(lot_round_id):
    space_lots:Sequence[TLotuserspaceresp] = await SqlHelper.getSpaceRespByRoundId(lot_round_id)
    all_target_uid_list = await get_other_lot_redis_manager.get_target_uid_list()
    all_target_uid_set = {item.uid for item in all_target_uid_list}
    all_dynamic_items = set()
    for x in space_lots:
        if x.spaceUid not in all_target_uid_set:
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

    print(f'总共{len(all_dynamic_items)}条动态需要检查')
    task_set = set()
    for x in all_dynamic_items:
        await _sem.acquire()
        task = asyncio.create_task(x.judge_lottery(lot_round_id))
        task.add_done_callback(lambda __: _sem.release())
        task_set.add(task)
    await asyncio_gather(
        *task_set
    )
    print(all_dynamic_items)

if __name__ =="__main__":
    asyncio.run(get_other_lot_by_lot_round_id(234))